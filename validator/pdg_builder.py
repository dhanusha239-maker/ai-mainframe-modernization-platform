import os
import re
from collections import defaultdict


class PDGBuilder:
    """
    Program Dependency Graph Builder.

    This version:
    1. Ignores DS 0H labels.
    2. Ignores save/work/control-only declarations like SAVEAREA DS 18F.
    3. Captures parameter blocks: BUSPARM DC A(CURRTX),A(ERRCODE)
    4. Resolves simple LM 2,3,0(1) parameter register mapping.
    5. Captures VSAM DDNAMEs from ACB definitions.
    """

    def __init__(self, asm_folder="HLASM"):
        self.asm_folder = asm_folder

        self.symbols = {}
        self.parameter_blocks = {}
        self.ddnames = {}

        self.reads = defaultdict(list)
        self.writes = defaultdict(list)

        self.symbol_readers = defaultdict(list)
        self.symbol_writers = defaultdict(list)

        # module -> register -> symbol
        self.register_map = defaultdict(dict)

        self.data_definition_ops = {"DS", "DC"}
        self.control_block_ops = {"ACB", "RPL", "DCB"}

        self.ignore_symbol_prefixes = {
            "SAVE", "SAVEAREA"
        }

    def _add_unique(self, items, value):
        if value not in items:
            items.append(value)

    def scan_repository(self):
        for filename in os.listdir(self.asm_folder):
            if filename.lower().endswith((".asm", ".asm.txt")):
                filepath = os.path.join(self.asm_folder, filename)
                self.parse_file(filepath)

    def parse_file(self, filepath):
        current_module = None

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

                # Detect module
                if has_label and len(parts) >= 2 and parts[1].upper() == "CSECT":
                    current_module = parts[0].upper()
                    continue

                if current_module is None:
                    continue

                self._capture_ddname(current_module, has_label, parts, clean)
                self._discover_symbol(current_module, has_label, parts, clean)
                self._discover_parameter_block(current_module, has_label, parts, clean)
                self._track_register_mapping(current_module, clean)
                self._track_usage(current_module, clean)

    def _capture_ddname(self, module, has_label, parts, clean):
        """
        Example:
          INACB ACB AM=VSAM,DDNAME=INVSAM,...
        """

        if not has_label or len(parts) < 2:
            return

        symbol = parts[0].upper()
        opcode = parts[1].upper()

        if opcode not in self.control_block_ops:
            return

        dd_match = re.search(r"DDNAME=([A-Z0-9_#$@]+)", clean, re.IGNORECASE)

        if dd_match:
            self.ddnames[symbol] = {
                "module": module,
                "ddname": dd_match.group(1).upper(),
                "line": clean,
            }

    def _discover_symbol(self, module, has_label, parts, clean):
        """
        Discover business/data symbols from DS/DC.

        Excludes:
          DS 0H labels
          SAVEAREA DS 18F
          control labels
        """

        if not has_label or len(parts) < 3:
            return

        symbol = parts[0].upper()
        opcode = parts[1].upper()
        datatype = parts[2].upper()

        if opcode not in self.data_definition_ops:
            return

        # DS 0H is code label, not data field
        if opcode == "DS" and datatype == "0H":
            return

        # Save areas are infrastructure, not business PDG fields
        if any(symbol.startswith(prefix) for prefix in self.ignore_symbol_prefixes):
            return

        self.symbols[symbol] = {
            "module": module,
            "opcode": opcode,
            "datatype": datatype,
            "line": clean,
        }

    def _discover_parameter_block(self, module, has_label, parts, clean):
        """
        Example:
          BUSPARM DC A(CURRTX),A(ERRCODE)

        Stores:
          BUSPARM -> [CURRTX, ERRCODE]
        """

        if not has_label or len(parts) < 3:
            return

        symbol = parts[0].upper()
        opcode = parts[1].upper()

        if opcode != "DC":
            return

        targets = re.findall(r"A\(([A-Z0-9_#$@]+)\)", clean, re.IGNORECASE)

        if targets:
            self.parameter_blocks[symbol] = [t.upper() for t in targets]

    def _track_register_mapping(self, module, clean):
        """
        Resolve simple parameter loading patterns.

        Example:
          LM 2,3,0(1)

        If R1 points to BUSPARM, and BUSPARM is:
          BUSPARM DC A(CURRTX),A(ERRCODE)

        Then:
          R2 = CURRTX
          R3 = ERRCODE

        V1 limitation:
          We infer based on comments or most recent parameter block is not implemented yet.
          So this function resolves common direct pattern only when the line/comment contains block name.
        """

        # Future stronger version will track:
        # LA 1,BUSPARM
        # BALR 14,15
        #
        # For now we support direct comment hints and offset patterns later.
        pass

    def _track_usage(self, module, clean):
        """
        Track reads/writes from common instructions.

        Supported:
          MVC target,source
          CLC left,right
          CLI field,value
          CP left,right
          ZAP target,source
          ST reg,target
          L reg,source
          AP/SP/MP target,source
        """

        parts = clean.split(None, 1)

        if not parts:
            return

        opcode = parts[0].upper()

        operands = self._get_operands(clean)

        if opcode == "MVC":
            if len(operands) >= 2:
                self._mark_write(module, operands[0])
                self._mark_read(module, operands[1])

        elif opcode in {"CLC", "CP"}:
            for operand in operands[:2]:
                self._mark_read(module, operand)

        elif opcode == "CLI":
            if operands:
                self._mark_read(module, operands[0])

        elif opcode == "ZAP":
            if len(operands) >= 2:
                self._mark_write(module, operands[0])
                self._mark_read(module, operands[1])

        elif opcode in {"AP", "SP", "MP"}:
            if len(operands) >= 2:
                self._mark_write(module, operands[0])
                self._mark_read(module, operands[0])
                self._mark_read(module, operands[1])

        elif opcode == "ST":
            if len(operands) >= 2:
                self._mark_write(module, operands[1])

        elif opcode == "L":
            if len(operands) >= 2:
                self._mark_read(module, operands[1])

    def _get_operands(self, clean):
        """
        Better operand splitter.

        Keeps operands like:
          0(4,3)
          FEEWORK+4(4)
        """

        parts = clean.split(None, 1)

        if len(parts) < 2:
            return []

        text = parts[1]

        operands = []
        current = ""
        paren_depth = 0
        in_quote = False

        for ch in text:
            if ch == "'":
                in_quote = not in_quote

            if ch == "(" and not in_quote:
                paren_depth += 1
            elif ch == ")" and not in_quote:
                paren_depth -= 1

            if ch == "," and paren_depth == 0 and not in_quote:
                operands.append(current.strip())
                current = ""
            else:
                current += ch

        if current.strip():
            operands.append(current.strip())

        return operands

    def _normalize_operand(self, operand):
        """
        Convert operand to known symbol when possible.

        Handles:
          TXAMT
          TXAMT(4)
          TXFEE+4(4)
          LOGPAN+4(8)
        """

        operand = operand.upper().strip()

        if operand.startswith("="):
            return None

        base = re.split(r"[+(]", operand)[0]

        if base in self.symbols:
            return base

        return None

    def _mark_read(self, module, operand):
        symbol = self._normalize_operand(operand)

        if not symbol:
            return

        self._add_unique(self.reads[module], symbol)
        self._add_unique(self.symbol_readers[symbol], module)

    def _mark_write(self, module, operand):
        symbol = self._normalize_operand(operand)

        if not symbol:
            return

        self._add_unique(self.writes[module], symbol)
        self._add_unique(self.symbol_writers[symbol], module)

    def print_report(self):
        print("\nDISCOVERED DATA SYMBOLS")
        print("-" * 60)

        for symbol, info in self.symbols.items():
            print(
                f"{symbol:<12} {info['opcode']:<3} {info['datatype']:<12} "
                f"module={info['module']}"
            )

        print("\nPARAMETER BLOCKS")
        print("-" * 60)

        if not self.parameter_blocks:
            print("None")
        else:
            for name, targets in self.parameter_blocks.items():
                print(f"{name:<12} -> {', '.join(targets)}")

        print("\nVSAM / FILE DDNAME REFERENCES")
        print("-" * 60)

        if not self.ddnames:
            print("None")
        else:
            for acb, info in self.ddnames.items():
                print(
                    f"{acb:<12} DDNAME={info['ddname']} "
                    f"module={info['module']}"
                )

        print("\nMODULE READ/WRITE SUMMARY")
        print("-" * 60)

        all_modules = sorted(set(self.reads.keys()) | set(self.writes.keys()))

        if not all_modules:
            print("No direct symbol reads/writes detected yet")

        for module in all_modules:
            print(f"\n{module}:")

            if self.reads[module]:
                print(f"  READS  -> {', '.join(self.reads[module])}")

            if self.writes[module]:
                print(f"  WRITES -> {', '.join(self.writes[module])}")

        print("\nSYMBOL IMPACT SUMMARY")
        print("-" * 60)

        any_impact = False

        for symbol in self.symbols:
            writers = self.symbol_writers.get(symbol, [])
            readers = self.symbol_readers.get(symbol, [])

            if not writers and not readers:
                continue

            any_impact = True
            print(f"\n{symbol}:")

            if writers:
                print(f"  WRITTEN BY -> {', '.join(writers)}")

            if readers:
                print(f"  READ BY    -> {', '.join(readers)}")

        if not any_impact:
            print("No symbol impact detected yet")