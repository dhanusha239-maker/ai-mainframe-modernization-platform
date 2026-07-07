import os
import re
from collections import defaultdict


class CFGBuilder:
    """
    Builds CFG for all HLASM modules.

    Output:
      MODULE
        BLOCK/LABEL
          CALLS       -> external modules/subroutines
          BRANCHES    -> explicit branch labels
          FALLTHROUGH -> next executable block if control continues naturally

    Important:
      HLASM column position matters.
      We preserve leading spaces for label detection.
    """

    def __init__(self, asm_folder="HLASM"):
        self.asm_folder = asm_folder

        self.cfg = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "calls": [],
                    "branches": [],
                    "fallthrough": None,
                    "terminates": False,
                }
            )
        )

        self.modules = []
        self.block_order = defaultdict(list)

        self.branch_ops = {
            "B", "BE", "BNE", "BNZ", "BZ",
            "BH", "BL", "BNH", "BNL",
            "JZ", "JNZ"
        }

        # Declaration/control-block opcodes.
        # These should not become CFG blocks, except DS 0H.
        self.non_executable_ops = {
            "DC", "DSECT", "EQU",
            "ACB", "RPL", "DCB",
            "ORG", "LTORG"
        }

        self.terminating_ops = {
            "B",      # unconditional branch
            "BR",     # branch register / return
            "PR",     # program return
            "END",
        }

    def _add_unique(self, items, value):
        if value not in items:
            items.append(value)

    def scan_repository(self):
        for filename in os.listdir(self.asm_folder):
            if filename.lower().endswith((".asm", ".asm.txt")):
                filepath = os.path.join(self.asm_folder, filename)
                self.parse_file(filepath)

        self._add_fallthroughs()

    def parse_file(self, filepath):
        current_module = None
        current_block = None

        with open(filepath, "r", encoding="utf-8") as f:
            for raw_line in f:
                raw = raw_line.rstrip("\n")

                if not raw.strip():
                    continue

                if raw.startswith("*"):
                    continue

                has_label = not raw.startswith(" ")

                clean = raw.strip()
                parts = clean.split()

                if not parts:
                    continue

                # CSECT/module start
                if has_label and len(parts) >= 2 and parts[1].upper() == "CSECT":
                    current_module = parts[0].upper()
                    current_block = current_module

                    self._add_unique(self.modules, current_module)
                    self._add_unique(
                        self.block_order[current_module],
                        current_block
                    )
                    continue

                if current_module is None:
                    continue

                # Detect label/block only if label is in column 1
                if has_label and len(parts) >= 2:
                    label = parts[0].upper()
                    opcode = parts[1].upper()

                    # DS 0H is an executable label/block marker.
                    # DS 18F, DS CL80, DS PL4, etc. are data declarations.
                    if opcode == "DS":
                        if len(parts) >= 3 and parts[2].upper() == "0H":
                            current_block = label
                            self._add_unique(
                                self.block_order[current_module],
                                current_block
                            )
                        else:
                            continue

                    # DC/ACB/RPL/DCB/ORG/LTORG/etc. are declarations.
                    elif opcode in self.non_executable_ops:
                        continue

                    # Normal executable label:
                    # OPEN_ERR LA 15,12
                    # IO_ERROR LA 15,16
                    else:
                        current_block = label
                        self._add_unique(
                            self.block_order[current_module],
                            current_block
                        )

                if current_block is None:
                    current_block = current_module

                # Ensure block exists
                _ = self.cfg[current_module][current_block]

                # =V(MODULE)
                vcon_match = re.search(
                    r"=V\(([A-Z0-9_#$@]+)\)",
                    clean,
                    re.IGNORECASE
                )
                if vcon_match:
                    target = vcon_match.group(1).upper()
                    self._add_unique(
                        self.cfg[current_module][current_block]["calls"],
                        target
                    )

                # LOAD/LINK/ATTACH/XCTL EP=MODULE
                ep_match = re.search(
                    r"\b(LOAD|LINK|ATTACH|XCTL)\s+EP=([A-Z0-9_#$@]+)",
                    clean,
                    re.IGNORECASE
                )
                if ep_match:
                    target = ep_match.group(2).upper()
                    self._add_unique(
                        self.cfg[current_module][current_block]["calls"],
                        target
                    )

                # CALL MODULE
                call_match = re.search(
                    r"\bCALL\s+([A-Z0-9_#$@]+)",
                    clean,
                    re.IGNORECASE
                )
                if call_match:
                    target = call_match.group(1).upper()
                    self._add_unique(
                        self.cfg[current_module][current_block]["calls"],
                        target
                    )

                # BAL/BAS direct target
                bal_match = re.search(
                    r"\b(BAL|BAS)\s+\d+\s*,\s*([A-Z0-9_#$@]+)",
                    clean,
                    re.IGNORECASE
                )
                if bal_match:
                    target = bal_match.group(2).upper()
                    self._add_unique(
                        self.cfg[current_module][current_block]["calls"],
                        target
                    )

                # Explicit branches
                branch_target = self._extract_branch(parts)
                if branch_target:
                    self._add_unique(
                        self.cfg[current_module][current_block]["branches"],
                        branch_target
                    )

                # Terminating instruction
                if self._is_terminating_instruction(parts):
                    self.cfg[current_module][current_block]["terminates"] = True

    def _extract_branch(self, parts):
        if len(parts) < 2:
            return None

        op = parts[0].upper()

        # B TARGET / BNZ TARGET
        if op in self.branch_ops:
            return parts[1].replace(",", "").upper()

        # LABEL B TARGET / LABEL BNZ TARGET
        if len(parts) >= 3:
            op = parts[1].upper()
            if op in self.branch_ops:
                return parts[2].replace(",", "").upper()

        return None

    def _is_terminating_instruction(self, parts):
        if not parts:
            return False

        op1 = parts[0].upper()
        op2 = parts[1].upper() if len(parts) >= 2 else None

        if op1 in self.terminating_ops:
            return True

        if op2 in self.terminating_ops:
            return True

        return False

    def _add_fallthroughs(self):
        for module in self.modules:
            blocks = self.block_order[module]

            for index, block in enumerate(blocks[:-1]):
                next_block = blocks[index + 1]
                block_data = self.cfg[module][block]

                if block_data["terminates"]:
                    continue

                block_data["fallthrough"] = next_block

    def _build_module_call_graph(self):
        call_graph = defaultdict(list)

        for module in self.modules:
            for block in self.block_order[module]:
                block_data = self.cfg[module][block]

                for target in block_data["calls"]:
                    self._add_unique(call_graph[module], target)

        return call_graph

    def _find_entry_modules(self):
        called_modules = []

        call_graph = self._build_module_call_graph()

        for targets in call_graph.values():
            for target in targets:
                self._add_unique(called_modules, target)

        entry_modules = []

        for module in self.modules:
            if module not in called_modules:
                entry_modules.append(module)

        return entry_modules

    def _flow_order_modules(self):
        call_graph = self._build_module_call_graph()
        entries = self._find_entry_modules()

        visited = set()
        order = []

        def dfs(module):
            if module in visited:
                return

            visited.add(module)
            order.append(module)

            for target in call_graph.get(module, []):
                if target in self.cfg:
                    dfs(target)

        for entry in entries:
            dfs(entry)

        for module in self.modules:
            if module not in visited:
                order.append(module)

        return order

    def print_report(self):
        print("\nCONTROL FLOW GRAPH")
        print("-" * 60)

        entries = self._find_entry_modules()

        print("\nENTRY MODULES")
        print("-" * 60)

        if entries:
            for entry in entries:
                print(entry)
        else:
            print("None detected")

        print("\nMODULE FLOW ORDER")
        print("-" * 60)

        module_order = self._flow_order_modules()
        print(" -> ".join(module_order))

        for module in module_order:
            print(f"\n{module}:")

            for block in self.block_order[module]:
                block_data = self.cfg[module][block]

                calls = block_data["calls"]
                branches = block_data["branches"]
                fallthrough = block_data["fallthrough"]

                if not calls and not branches and not fallthrough:
                    continue

                print(f"  {block}:")

                if calls:
                    print(f"    CALLS       -> {', '.join(calls)}")

                if branches:
                    print(f"    BRANCHES    -> {', '.join(branches)}")

                if fallthrough:
                    print(f"    FALLTHROUGH -> {fallthrough}")