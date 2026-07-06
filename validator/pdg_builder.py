import os
import re
import json
from collections import defaultdict


class PDGBuilder:
    """
    Global HLASM PDG Builder.

    Tracks:
    - Data symbols from DS/DC
    - Multi-line parameter blocks: PARM DC A(X) / DC A(Y)
    - VSAM DDNAMEs from ACB/DCB
    - RPL AREA mappings
    - GET/PUT/MODCB VSAM buffer effects
    - R1 parameter passing
    - LM/L register mapping from parameter blocks
    - Field offsets inside record layouts like CURRTX DS 0CL64
    - Reads/writes
    - Return codes in R15
    - Conditions
    - Warnings
    - JSON export
    """

    def __init__(self, asm_folder="HLASM"):
        self.asm_folder = asm_folder

        self.symbols = {}
        self.symbol_order = []

        self.parameter_blocks = {}
        self.current_parameter_block = None

        self.ddnames = {}
        self.rpl_areas = {}

        self.module_param_block = {}
        self.register_map = defaultdict(dict)

        self.reads = defaultdict(list)
        self.writes = defaultdict(list)

        self.symbol_readers = defaultdict(list)
        self.symbol_writers = defaultdict(list)

        self.return_codes = defaultdict(list)
        self.conditions = defaultdict(list)
        self.condition_branches = defaultdict(list)

        self.field_offsets = defaultdict(dict)

        # VSAM/RPL semantic effects
        self.record_buffer_reads = defaultdict(list)
        self.record_buffer_writes = defaultdict(list)
        self.active_rpl_area = defaultdict(dict)

        self.warnings = []

        self.data_definition_ops = {"DS", "DC"}
        self.control_block_ops = {"ACB", "RPL", "DCB"}

        self.ignore_symbol_prefixes = {"SAVE", "SAVEAREA"}

        self.branch_ops = {
            "B", "BE", "BNE", "BNZ", "BZ",
            "BH", "BL", "BNH", "BNL", "JZ", "JNZ", "JE", "JNE",
            "BCT", "BCTR", "BRCT"
        }

        self.known_opcodes = {
            "MVC", "CLC", "CLI", "CP", "C", "LTR",
            "ZAP", "AP", "SP", "MP", "ST", "L", "LA",
            "LM", "XR", "BALR", "BASR", "BAL", "BAS",
            "GET", "PUT", "OPEN", "CLOSE", "MODCB",
            "PR", "BR", "B", "BE", "BNE", "BNZ", "BZ",
            "BH", "BL", "BNH", "BNL", "JZ", "JNZ", "JE", "JNE",
            "BCT", "BCTR", "BRCT"
        }

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

        self._post_process_warnings()

    # ------------------------------------------------------------
    # General helpers
    # ------------------------------------------------------------
    def _clean_operand(self, operand):
        operand = operand.strip()

        if not operand:
            return operand

        literal_match = re.match(r"(=[A-Z]?'.*?')", operand, re.IGNORECASE)
        if literal_match:
            return literal_match.group(1)

        return operand.split()[0] if operand.split() else operand

    def _get_operands(self, clean):
        opcode, operand_text = self._split_opcode_operands(clean)

        if not opcode or not operand_text:
            return []

        operands = []
        current = ""
        paren_depth = 0
        in_quote = False

        for ch in operand_text:
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

    def _split_opcode_operands(self, clean):
        """
        Handles both:
          MVC A,B
          LABEL MVC A,B
        """

        parts = clean.split(None, 2)

        if not parts:
            return None, None

        first = parts[0].upper()

        if first in self.known_opcodes:
            split = clean.split(None, 1)
            opcode = first
            operand_text = split[1] if len(split) > 1 else ""
            return opcode, operand_text

        if len(parts) >= 2 and parts[1].upper() in self.known_opcodes:
            opcode = parts[1].upper()
            operand_text = parts[2] if len(parts) >= 3 else ""
            return opcode, operand_text

        split = clean.split(None, 1)
        return first, split[1] if len(split) > 1 else ""

    # ------------------------------------------------------------
    # PASS 1: Discover symbols, parameter blocks, files, RPL areas
    # ------------------------------------------------------------
    def _pass1_discovery(self, filepath):
        current_module = None
        self.current_parameter_block = None

        with open(filepath, "r", encoding="utf-8") as f:
            for raw_line in f:
                raw = raw_line.rstrip("\n")

                if not raw.strip() or raw.startswith("*"):
                    continue

                has_label = not raw.startswith(" ")
                clean = raw.strip()
                parts = clean.split()

                if not parts:
                    continue

                if has_label and len(parts) >= 2 and parts[1].upper() == "CSECT":
                    current_module = parts[0].upper()
                    self.current_parameter_block = None
                    continue

                if current_module is None:
                    continue

                self._capture_ddname(current_module, has_label, parts, clean)
                self._capture_rpl_area(current_module, has_label, parts, clean)
                self._discover_parameter_block(has_label, parts, clean)
                self._discover_symbol(current_module, has_label, parts, clean)

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

    def _capture_rpl_area(self, module, has_label, parts, clean):
        """
        Captures:
          INRPL RPL AM=VSAM,ACB=INACB,AREA=CURRTX,...
        """

        if not has_label or len(parts) < 2:
            return

        symbol = parts[0].upper()
        opcode = parts[1].upper()

        if opcode != "RPL":
            return

        area_match = re.search(r"AREA=([A-Z0-9_#$@]+)", clean, re.IGNORECASE)

        if area_match:
            self.rpl_areas[symbol] = {
                "module": module,
                "area": area_match.group(1).upper(),
                "line": clean,
            }

    def _discover_parameter_block(self, has_label, parts, clean):
        """
        Supports:
          AUDPARM DC A(OUTRPL)
                  DC A(CURRTX)
                  DC A(AUTHSTAT)

        and:
          BUSPARM DC A(CURRTX),A(ERRCODE)
        """

        # Labeled DC starts a parameter block
        if has_label and len(parts) >= 3:
            symbol = parts[0].upper()
            opcode = parts[1].upper()

            if opcode != "DC":
                self.current_parameter_block = None
                return

            targets = re.findall(r"A\(([A-Z0-9_#$@]+)\)", clean, re.IGNORECASE)

            if targets:
                self.parameter_blocks[symbol] = [t.upper() for t in targets]
                self.current_parameter_block = symbol
            else:
                self.current_parameter_block = None

            return

        # Unlabeled continuation DC
        if not has_label and self.current_parameter_block:
            opcode = parts[0].upper()

            if opcode != "DC":
                return

            targets = re.findall(r"A\(([A-Z0-9_#$@]+)\)", clean, re.IGNORECASE)

            if targets:
                for target in targets:
                    self._add_unique(
                        self.parameter_blocks[self.current_parameter_block],
                        target.upper(),
                    )

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

        # Parameter block declarations are captured separately.
        if symbol in self.parameter_blocks:
            return

        self.symbols[symbol] = {
            "module": module,
            "opcode": opcode,
            "datatype": datatype,
            "line": clean,
        }

        self.symbol_order.append({
            "module": module,
            "symbol": symbol,
            "opcode": opcode,
            "datatype": datatype,
            "line": clean,
            "has_label": has_label,
        })

    # ------------------------------------------------------------
    # Field offset mapping
    # ------------------------------------------------------------
    def _build_field_offsets(self):
        current_base = None
        current_module = None
        current_offset = 0
        current_limit = None

        for item in self.symbol_order:
            module = item["module"]
            symbol = item["symbol"]
            datatype = item["datatype"]

            if module != current_module:
                current_base = None
                current_module = module
                current_offset = 0
                current_limit = None

            # Base group like CURRTX DS 0CL64 or LOGBUFF DS 0CL80
            if datatype.startswith("0"):
                current_base = symbol
                current_offset = 0
                current_limit = self._datatype_size(datatype[1:])
                continue

            if current_base is None:
                continue

            if current_limit is not None and current_offset >= current_limit:
                current_base = None
                current_offset = 0
                current_limit = None
                continue

            size = self._datatype_size(datatype)
            if size is None:
                continue

            self.field_offsets[current_base][current_offset] = symbol
            current_offset += size

            if current_limit is not None and current_offset >= current_limit:
                current_base = None
                current_offset = 0
                current_limit = None

    def _datatype_size(self, datatype):
        datatype = datatype.upper().strip()

        m = re.match(r"CL(\d+)", datatype)
        if m:
            return int(m.group(1))

        m = re.match(r"XL(\d+)", datatype)
        if m:
            return int(m.group(1))

        m = re.match(r"PL(\d+)", datatype)
        if m:
            return int(m.group(1))

        m = re.match(r"C'(.*?)'", datatype)
        if m:
            return len(m.group(1))

        if datatype == "F":
            return 4

        m = re.match(r"(\d+)F", datatype)
        if m:
            return int(m.group(1)) * 4

        return None

    # ------------------------------------------------------------
    # PASS 2: Caller context
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
                clean = raw.strip()
                parts = clean.split()

                if not parts:
                    continue

                if has_label and len(parts) >= 2 and parts[1].upper() == "CSECT":
                    current_module = parts[0].upper()
                    continue

                if current_module is None:
                    continue

                # LA 1,PARMBLOCK
                la_match = re.search(
                    r"\bLA\s+1\s*,\s*([A-Z0-9_#$@]+)",
                    clean,
                    re.IGNORECASE,
                )
                if la_match:
                    block = la_match.group(1).upper()
                    if block in self.parameter_blocks:
                        current_param_block = block

                # L 15,=V(MODULE)
                vcon_match = re.search(
                    r"=V\(([A-Z0-9_#$@]+)\)",
                    clean,
                    re.IGNORECASE,
                )
                if vcon_match:
                    pending_target_module = vcon_match.group(1).upper()

                # BALR/BASR calls target in register
                if re.search(r"\b(BALR|BASR)\b", clean, re.IGNORECASE):
                    if pending_target_module and current_param_block:
                        self.module_param_block[pending_target_module] = current_param_block

                    pending_target_module = None
                    current_param_block = None

    # ------------------------------------------------------------
    # PASS 3: Usage, VSAM, return codes, conditions
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
                clean = raw.strip()
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
                self._track_vsam_io(current_module, clean)
                self._track_return_code_set(current_module, clean)
                self._track_usage(current_module, clean)

                condition = self._extract_condition(current_module, clean)
                if condition:
                    last_condition = condition
                    self.conditions[current_module].append(condition)

                branch = self._extract_branch(clean)
                if branch and last_condition:
                    self.condition_branches[current_module].append({
                        "condition": last_condition,
                        "branch": branch,
                    })
                    last_condition = None

    def _track_register_mapping(self, module, clean):
        block_name = self.module_param_block.get(module)
        if not block_name:
            return

        params = self.parameter_blocks.get(block_name, [])

        # LM 2,3,0(1) or LM 2,3,4(1)
        lm_match = re.search(
            r"\bLM\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\(1\)",
            clean,
            re.IGNORECASE,
        )

        if lm_match:
            start_reg = int(lm_match.group(1))
            end_reg = int(lm_match.group(2))
            offset = int(lm_match.group(3))
            param_index = offset // 4

            reg = start_reg
            idx = param_index

            while reg <= end_reg and idx < len(params):
                self.register_map[module][reg] = params[idx]
                reg += 1
                idx += 1

        # L 4,8(,1)
        l_match = re.search(
            r"\bL\s+(\d+)\s*,\s*(\d+)\(,?1\)",
            clean,
            re.IGNORECASE,
        )

        if l_match:
            reg = int(l_match.group(1))
            offset = int(l_match.group(2))
            param_index = offset // 4

            if param_index < len(params):
                self.register_map[module][reg] = params[param_index]

    def _track_vsam_io(self, module, clean):
        """
        Captures generic VSAM/RPL semantic effects.

        GET RPL=(2)
          If R2 -> INRPL and INRPL AREA=CURRTX,
          then module writes/populates CURRTX.

        MODCB RPL=(2),AREA=LOGBUFF
          dynamically changes OUTRPL active area to LOGBUFF.

        PUT RPL=(2)
          If R2 -> OUTRPL and active area is LOGBUFF,
          then module reads/writes out LOGBUFF.
        """

        opcode, _ = self._split_opcode_operands(clean)

        if opcode not in {"GET", "PUT", "MODCB"}:
            return

        # MODCB RPL=(2),AREA=LOGBUFF
        modcb_match = re.search(
            r"MODCB\s+RPL=\((\d+)\).*AREA=([A-Z0-9_#$@]+)",
            clean,
            re.IGNORECASE,
        )

        if modcb_match:
            reg = int(modcb_match.group(1))
            area = modcb_match.group(2).upper()

            rpl_symbol = self.register_map[module].get(reg)

            if rpl_symbol:
                self.active_rpl_area[module][rpl_symbol] = area

            return

        rpl_symbol = None

        # GET RPL=(2) / PUT RPL=(2)
        rpl_reg_match = re.search(r"RPL=\((\d+)\)", clean, re.IGNORECASE)
        if rpl_reg_match:
            reg = int(rpl_reg_match.group(1))
            rpl_symbol = self.register_map[module].get(reg)

        # GET RPL=INRPL / PUT RPL=OUTRPL
        direct_match = re.search(r"RPL=([A-Z0-9_#$@]+)", clean, re.IGNORECASE)
        if direct_match and not rpl_symbol:
            rpl_symbol = direct_match.group(1).upper()

        if not rpl_symbol:
            return

        area = self.active_rpl_area[module].get(rpl_symbol)

        if not area:
            area_info = self.rpl_areas.get(rpl_symbol)
            if area_info:
                area = area_info.get("area")

        if not area:
            return

        if opcode == "GET":
            self._add_unique(self.record_buffer_writes[module], area)
            self._mark_write(module, area)

        elif opcode == "PUT":
            self._add_unique(self.record_buffer_reads[module], area)
            self._mark_read(module, area)

    def _track_return_code_set(self, module, clean):
        if re.search(r"\bXR\s+15\s*,\s*15\b", clean, re.IGNORECASE):
            self._add_unique(self.return_codes[module], "0")
            return

        match = re.search(r"\bLA\s+15\s*,\s*([0-9]+)", clean, re.IGNORECASE)
        if match:
            self._add_unique(self.return_codes[module], match.group(1))

    def _track_usage(self, module, clean):
        opcode, _ = self._split_opcode_operands(clean)
        if not opcode:
            return

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
        opcode, _ = self._split_opcode_operands(clean)
        if not opcode:
            return None

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
        opcode, _ = self._split_opcode_operands(clean)

        if opcode not in self.branch_ops:
            return None

        operands = self._get_operands(clean)
        if not operands:
            return None

        if opcode in {"BCT", "BCTR", "BRCT"}:
            if len(operands) < 2:
                return None
            target = operands[1].upper()
        else:
            target = operands[0].upper()

        return {
            "branch_op": opcode,
            "target": target,
            "line": clean,
        }

    # ------------------------------------------------------------
    # Operand normalization
    # ------------------------------------------------------------
    def _normalize_operand(self, module, operand):
        operand = operand.upper().strip()

        if operand.startswith("="):
            return None

        base = re.split(r"[+(]", operand)[0]
        if base in self.symbols:
            return base

        # 26(4,2), 0(4,3), 16(3), 8(,1)
        reg_match = re.search(
            r"^(\d+)?(?:\((\d+),(\d+)\)|\((\d+)\)|\(,(\d+)\))$",
            operand,
        )

        if reg_match:
            offset_text = reg_match.group(1)
            base_reg_1 = reg_match.group(3)
            base_reg_2 = reg_match.group(4)
            base_reg_3 = reg_match.group(5)

            offset = int(offset_text) if offset_text else 0
            reg_text = base_reg_1 or base_reg_2 or base_reg_3

            if not reg_text:
                return None

            reg_num = int(reg_text)
            base_symbol = self.register_map[module].get(reg_num)

            if not base_symbol:
                return None

            if base_symbol in self.parameter_blocks:
                params = self.parameter_blocks[base_symbol]
                index = offset // 4
                return params[index] if index < len(params) else base_symbol

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
    # Warnings
    # ------------------------------------------------------------
    def _post_process_warnings(self):
        for module, regs in self.register_map.items():
            reverse = defaultdict(list)

            for reg, symbol in regs.items():
                reverse[symbol].append(reg)

            for symbol, reg_list in reverse.items():
                if len(reg_list) > 1:
                    self.warnings.append(
                        f"{module}: {symbol} mapped to multiple registers {reg_list}. "
                        f"Check LM/L parameter offsets."
                    )

    # ------------------------------------------------------------
    # Report / Export
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
            "rpl_areas": self.rpl_areas,
            "module_parameter_context": self.module_param_block,
            "register_map": {
                module: {f"R{reg}": sym for reg, sym in regs.items()}
                for module, regs in self.register_map.items()
            },
            "record_buffer_reads": dict(self.record_buffer_reads),
            "record_buffer_writes": dict(self.record_buffer_writes),
            "reads": dict(self.reads),
            "writes": dict(self.writes),
            "symbol_readers": dict(self.symbol_readers),
            "symbol_writers": dict(self.symbol_writers),
            "return_codes": dict(self.return_codes),
            "conditions": dict(self.conditions),
            "condition_branches": dict(self.condition_branches),
            "warnings": self.warnings,
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

        print("\nRPL AREA MAP")
        print("-" * 70)
        if not self.rpl_areas:
            print("None")
        else:
            for rpl, info in self.rpl_areas.items():
                print(f"{rpl:<12} AREA={info['area']} module={info['module']}")

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

        print("\nRECORD BUFFER EFFECTS")
        print("-" * 70)
        modules = sorted(
            set(self.record_buffer_reads.keys()) |
            set(self.record_buffer_writes.keys())
        )
        if not modules:
            print("None")
        else:
            for module in modules:
                print(f"\n{module}:")
                if self.record_buffer_reads[module]:
                    print(f"  RECORD BUFFERS READ    -> {', '.join(self.record_buffer_reads[module])}")
                if self.record_buffer_writes[module]:
                    print(f"  RECORD BUFFERS WRITTEN -> {', '.join(self.record_buffer_writes[module])}")

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

        print("\nWARNINGS")
        print("-" * 70)
        if not self.warnings:
            print("None")
        else:
            for warning in self.warnings:
                print(f"- {warning}")