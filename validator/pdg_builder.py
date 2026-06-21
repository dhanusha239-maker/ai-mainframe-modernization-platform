import os
import re
import json
from collections import defaultdict


class PDGBuilder:
    """
    Program Dependency Graph Builder for HLASM.

    Tracks:
    - Data symbols from DS/DC
    - Parameter blocks
    - VSAM DDNAMEs
    - R1 parameter passing
    - Register mappings from LM x,y,0(1)
    - Field offsets inside layouts like CURRTX
    - Reads/writes
    - Return codes
    - Conditions
    - JSON export
    """

    def __init__(self, asm_folder="HLASM"):
        self.asm_folder = asm_folder

        self.symbols = {}
        self.parameter_blocks = {}
        self.ddnames = {}

        self.module_param_block = {}
        self.register_map = defaultdict(dict)

        self.reads = defaultdict(list)
        self.writes = defaultdict(list)
        self.symbol_readers = defaultdict(list)
        self.symbol_writers = defaultdict(list)

        self.return_codes = defaultdict(list)
        self.return_code_checks = defaultdict(list)
        self.conditions = defaultdict(list)

        self.field_offsets = defaultdict(dict)

        self.data_definition_ops = {"DS", "DC"}
        self.control_block_ops = {"ACB", "RPL", "DCB"}
        self.ignore_symbol_prefixes = {"SAVE", "SAVEAREA"}

    def _add_unique(self, items, value):
        if value not in items:
            items.append(value)

    def scan_repository(self):
        files = [
            os.path.join(self.asm_folder, f)
            for f in os.listdir(self.asm_folder)
            if f.lower().endswith((".asm", ".asm.txt"))
        ]

        for filepath in files:
            self._pass1_discovery(filepath)

        self._build_field_offsets()

        for filepath in files:
            self._pass2_call_context(filepath)

        for filepath in files:
            self._pass3_usage(filepath)

    def _remove_comment(self, clean):
        """
        Keep full HLASM statement.

        Do NOT split on multiple spaces because assembler uses spacing
        between label, opcode, operands, and comments.

        Operand cleanup happens in _clean_operand().
        """
        return clean.strip()

    def _clean_operand(self, operand):
        """
        Remove trailing human comments from operands without breaking
        literals or address expressions.
        """

        operand = operand.strip()

        if not operand:
            return operand

        # Keep literal constants only:
        # =C'0000' comment  -> =C'0000'
        # =P'50000' comment -> =P'50000'
        literal_match = re.match(r"(=[A-Z]?'.*?')", operand, re.IGNORECASE)
        if literal_match:
            return literal_match.group(1)

        # Otherwise keep first token.
        # Example:
        # "33(4,2) Compare Transaction Amount" -> "33(4,2)"
        return operand.split()[0] if operand.split() else operand

    # ------------------------------------------------------------
    # PASS 1
    # ------------------------------------------------------------
    def _pass1_discovery(self, filepath):
        current_module = None

        with open(filepath, "r", encoding="utf-8") as f:
            for raw_line in f:
                raw = raw_line.rstrip("\n")

                if not raw.strip() or raw.startswith("*"):
                    continue

                has_label = not raw.startswith(" ")
                clean = self._remove_comment(raw.strip())
                parts = clean.split()

                if not parts:
                    continue

                if has_label and len(parts) >= 2 and parts[1].upper() == "CSECT":
                    current_module = parts[0].upper()
                    continue

                if current_module is None:
                    continue

                self._capture_ddname(current_module, has_label, parts, clean)
                self._discover_symbol(current_module, has_label, parts, clean)
                self._discover_parameter_block(has_label, parts, clean)

    def _capture_ddname(self, module, has_label, parts, clean):
        if not has_label or len(parts) < 2:
            return

        symbol = parts[0].upper()
        opcode = parts[1].upper()

        if opcode not in self.control_block_ops:
            return

        match = re.search(r"DDNAME=([A-Z0-9_#$@]+)", clean, re.IGNORECASE)
        if match:
            self.ddnames[symbol] = {
                "module": module,
                "ddname": match.group(1).upper(),
                "line": clean,
            }

    def _discover_symbol(self, module, has_label, parts, clean):
        if not has_label or len(parts) < 3:
            return

        symbol = parts[0].upper()
        opcode = parts[1].upper()
        datatype = parts[2].upper()

        if opcode not in self.data_definition_ops:
            return

        if opcode == "DS" and datatype == "0H":
            return

        if any(symbol.startswith(prefix) for prefix in self.ignore_symbol_prefixes):
            return

        self.symbols[symbol] = {
            "module": module,
            "opcode": opcode,
            "datatype": datatype,
            "line": clean,
        }

    def _discover_parameter_block(self, has_label, parts, clean):
        if not has_label or len(parts) < 3:
            return

        symbol = parts[0].upper()
        opcode = parts[1].upper()

        if opcode != "DC":
            return

        targets = re.findall(r"A\(([A-Z0-9_#$@]+)\)", clean, re.IGNORECASE)

        if targets:
            self.parameter_blocks[symbol] = [t.upper() for t in targets]

    # ------------------------------------------------------------
    # FIELD OFFSET MAP
    # ------------------------------------------------------------
    def _build_field_offsets(self):
        current_base = None
        current_offset = 0

        for symbol, info in self.symbols.items():
            datatype = info["datatype"]

            if datatype.startswith("0"):
                current_base = symbol
                current_offset = 0
                continue

            if current_base is None:
                continue

            size = self._datatype_size(datatype)

            if size is None:
                continue

            self.field_offsets[current_base][current_offset] = symbol
            current_offset += size

    def _datatype_size(self, datatype):
        datatype = datatype.upper()

        m = re.match(r"CL(\d+)", datatype)
        if m:
            return int(m.group(1))

        m = re.match(r"XL(\d+)", datatype)
        if m:
            return int(m.group(1))

        m = re.match(r"PL(\d+)", datatype)
        if m:
            return int(m.group(1))

        if datatype == "F":
            return 4

        m = re.match(r"(\d+)F", datatype)
        if m:
            return int(m.group(1)) * 4

        return None

    # ------------------------------------------------------------
    # PASS 2
    # ------------------------------------------------------------
    def _pass2_call_context(self, filepath):
        current_module = None
        current_param_block = None
        pending_target_module = None

        with open(filepath, "r", encoding="utf-8") as f:
            for raw_line in f:
                raw = raw_line.rstrip("\n")

                if not raw.strip() or raw.startswith("*"):
                    continue

                has_label = not raw.startswith(" ")
                clean = self._remove_comment(raw.strip())
                parts = clean.split()

                if not parts:
                    continue

                if has_label and len(parts) >= 2 and parts[1].upper() == "CSECT":
                    current_module = parts[0].upper()
                    continue

                if current_module is None:
                    continue

                la_match = re.search(
                    r"\bLA\s+1\s*,\s*([A-Z0-9_#$@]+)",
                    clean,
                    re.IGNORECASE,
                )
                if la_match:
                    block = la_match.group(1).upper()
                    if block in self.parameter_blocks:
                        current_param_block = block

                vcon_match = re.search(
                    r"=V\(([A-Z0-9_#$@]+)\)",
                    clean,
                    re.IGNORECASE,
                )
                if vcon_match:
                    pending_target_module = vcon_match.group(1).upper()

                if re.search(r"\b(BALR|BASR)\b", clean, re.IGNORECASE):
                    if pending_target_module and current_param_block:
                        self.module_param_block[pending_target_module] = current_param_block

                    pending_target_module = None
                    current_param_block = None

    # ------------------------------------------------------------
    # PASS 3
    # ------------------------------------------------------------
    def _pass3_usage(self, filepath):
        current_module = None
        last_condition = None

        with open(filepath, "r", encoding="utf-8") as f:
            for raw_line in f:
                raw = raw_line.rstrip("\n")

                if not raw.strip() or raw.startswith("*"):
                    continue

                has_label = not raw.startswith(" ")
                clean = self._remove_comment(raw.strip())
                parts = clean.split()

                if not parts:
                    continue

                if has_label and len(parts) >= 2 and parts[1].upper() == "CSECT":
                    current_module = parts[0].upper()
                    last_condition = None
                    continue

                if current_module is None:
                    continue

                self._track_register_mapping(current_module, clean)
                self._track_return_code_set(current_module, clean)
                self._track_usage(current_module, clean)

                condition = self._extract_condition(current_module, clean)
                if condition:
                    last_condition = condition
                    self.conditions[current_module].append(condition)

                branch = self._extract_branch(clean)
                if branch and last_condition:
                    self.return_code_checks[current_module].append({
                        "condition": last_condition,
                        "branch": branch,
                    })
                    last_condition = None

    def _track_register_mapping(self, module, clean):
        match = re.search(
            r"\bLM\s+(\d+)\s*,\s*(\d+)\s*,\s*0\(1\)",
            clean,
            re.IGNORECASE,
        )

        if not match:
            return

        start_reg = int(match.group(1))
        end_reg = int(match.group(2))

        block_name = self.module_param_block.get(module)
        if not block_name:
            return

        params = self.parameter_blocks.get(block_name, [])

        reg = start_reg
        idx = 0

        while reg <= end_reg and idx < len(params):
            self.register_map[module][reg] = params[idx]
            reg += 1
            idx += 1

    def _track_return_code_set(self, module, clean):
        if re.search(r"\bXR\s+15\s*,\s*15\b", clean, re.IGNORECASE):
            self._add_unique(self.return_codes[module], "0")
            return

        match = re.search(r"\bLA\s+15\s*,\s*([0-9]+)", clean, re.IGNORECASE)
        if match:
            self._add_unique(self.return_codes[module], match.group(1))

    def _track_usage(self, module, clean):
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

    def _extract_condition(self, module, clean):
        parts = clean.split(None, 1)

        if not parts:
            return None

        opcode = parts[0].upper()
        operands = self._get_operands(clean)

        if opcode in {"CLC", "CLI", "CP", "C", "LTR"}:
            resolved = []

            for op in operands:
                symbol = self._normalize_operand(module, op)
                resolved.append(symbol if symbol else op)

            return {
                "instruction": opcode,
                "operands": resolved,
                "line": clean,
            }

        return None

    def _extract_branch(self, clean):
        match = re.search(
            r"\b(B|BE|BNE|BNZ|BZ|BH|BL|BNH|BNL|JZ|JNZ)\s+([A-Z0-9_#$@]+)",
            clean,
            re.IGNORECASE,
        )
        if not match:
            return None

        return {
            "branch_op": match.group(1).upper(),
            "target": match.group(2).upper(),
            "line": clean,
        }

    # ------------------------------------------------------------
    # OPERANDS
    # ------------------------------------------------------------
    def _get_operands(self, clean):
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
                operands.append(self._clean_operand(current))
                current = ""
            else:
                current += ch

        if current.strip():
            operands.append(self._clean_operand(current))

        return operands

    def _normalize_operand(self, module, operand):
        operand = operand.upper().strip()

        if operand.startswith("="):
            return None

        base = re.split(r"[+(]", operand)[0]
        if base in self.symbols:
            return base

        reg_match = re.search(r"^(\d+)?(?:\(\d+,(\d+)\)|\((\d+)\))", operand)
        if reg_match:
            offset_text = reg_match.group(1)
            reg_text = reg_match.group(2) or reg_match.group(3)

            offset = int(offset_text) if offset_text else 0
            reg_num = int(reg_text)

            base_symbol = self.register_map[module].get(reg_num)

            if base_symbol:
                field_symbol = self.field_offsets.get(base_symbol, {}).get(offset)
                return field_symbol if field_symbol else base_symbol

        return None

    def _mark_read(self, module, operand):
        symbol = self._normalize_operand(module, operand)
        if not symbol:
            return

        self._add_unique(self.reads[module], symbol)
        self._add_unique(self.symbol_readers[symbol], module)

    def _mark_write(self, module, operand):
        symbol = self._normalize_operand(module, operand)
        if not symbol:
            return

        self._add_unique(self.writes[module], symbol)
        self._add_unique(self.symbol_writers[symbol], module)

    # ------------------------------------------------------------
    # REPORTING
    # ------------------------------------------------------------
    def to_dict(self):
        return {
            "symbols": self.symbols,
            "field_offsets": {
                base: {str(offset): field for offset, field in offsets.items()}
                for base, offsets in self.field_offsets.items()
            },
            "parameter_blocks": self.parameter_blocks,
            "ddnames": self.ddnames,
            "module_parameter_context": self.module_param_block,
            "register_map": {
                module: {f"R{reg}": sym for reg, sym in regs.items()}
                for module, regs in self.register_map.items()
            },
            "reads": dict(self.reads),
            "writes": dict(self.writes),
            "symbol_readers": dict(self.symbol_readers),
            "symbol_writers": dict(self.symbol_writers),
            "return_codes": dict(self.return_codes),
            "conditions": dict(self.conditions),
            "condition_branches": dict(self.return_code_checks),
        }

    def export_json(self, output_path="analysis_report.json"):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    def print_report(self):
        print("\nPDG REPORT")
        print("=" * 70)

        print("\nFIELD OFFSET MAP")
        print("-" * 70)
        for base, offsets in self.field_offsets.items():
            print(f"{base}:")
            for offset, field in offsets.items():
                print(f"  +{offset:<3} -> {field}")

        print("\nPARAMETER BLOCKS")
        print("-" * 70)
        for name, targets in self.parameter_blocks.items():
            print(f"{name:<12} -> {', '.join(targets)}")

        print("\nMODULE PARAMETER CONTEXT")
        print("-" * 70)
        if not self.module_param_block:
            print("None")
        else:
            for module, block in self.module_param_block.items():
                print(
                    f"{module:<12} receives {block} -> "
                    f"{', '.join(self.parameter_blocks.get(block, []))}"
                )

        print("\nREGISTER MAP")
        print("-" * 70)
        if not self.register_map:
            print("None")
        else:
            for module, regs in self.register_map.items():
                mapped = [f"R{reg}={sym}" for reg, sym in sorted(regs.items())]
                print(f"{module:<12} " + ", ".join(mapped))

        print("\nVSAM / FILE DDNAME REFERENCES")
        print("-" * 70)
        for acb, info in self.ddnames.items():
            print(f"{acb:<12} DDNAME={info['ddname']} module={info['module']}")

        print("\nMODULE READ/WRITE SUMMARY")
        print("-" * 70)
        modules = sorted(set(self.reads.keys()) | set(self.writes.keys()))
        if not modules:
            print("No direct symbol reads/writes detected yet")
        for module in modules:
            print(f"\n{module}:")
            if self.reads[module]:
                print(f"  READS  -> {', '.join(self.reads[module])}")
            if self.writes[module]:
                print(f"  WRITES -> {', '.join(self.writes[module])}")

        print("\nRETURN CODE SUMMARY")
        print("-" * 70)
        if not self.return_codes:
            print("None")
        else:
            for module, codes in self.return_codes.items():
                print(f"{module:<12} sets R15/RC -> {', '.join(codes)}")

        print("\nCONDITION SUMMARY")
        print("-" * 70)
        if not self.conditions:
            print("None")
        else:
            for module, conditions in self.conditions.items():
                print(f"\n{module}:")
                for condition in conditions:
                    print(f"  {condition['instruction']} {condition['operands']}")

        print("\nSYMBOL IMPACT SUMMARY")
        print("-" * 70)
        found = False
        for symbol in self.symbols:
            writers = self.symbol_writers.get(symbol, [])
            readers = self.symbol_readers.get(symbol, [])
            if not writers and not readers:
                continue

            found = True
            print(f"\n{symbol}:")
            if writers:
                print(f"  WRITTEN BY -> {', '.join(writers)}")
            if readers:
                print(f"  READ BY    -> {', '.join(readers)}")

        if not found:
            print("No symbol impact detected yet")