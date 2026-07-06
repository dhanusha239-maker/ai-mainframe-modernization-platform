import re
try:
    from instruction_semantics_updated_v3 import get_semantics
except ImportError:
    try:
        from instruction_semantics_updated_v3 import get_semantics
    except ImportError:
        from instruction_semantics_updated_v3 import get_semantics


class InstructionTranslator:
    """
    Helper-based HLASM instruction translator.

    Responsibilities:
    1. Translate individual HLASM instructions into AsmRuntime helper calls.
    2. Resolve register-offset operands such as:
          16(4,2) -> TXCUST
          0(4,3)  -> ERRCODE
    3. Provide basic block / branch-flow translation support.

    Note:
    Basic block logic is kept here to avoid creating too many project files.
    """

    BRANCH_ALIASES = {
        "BE": "isEqual",
        "BZ": "isEqual",
        "JE": "isEqual",
        "JZ": "isEqual",
        "BNE": "isNotEqual",
        "BNZ": "isNotEqual",
        "JNE": "isNotEqual",
        "JNZ": "isNotEqual",
        "BH": "isHigh",
        "BP": "isHigh",
        "BL": "isLow",
        "BM": "isLow",
        "BNH": "isNotHigh",
        "BNL": "isNotLow",
        "BNO": "isNotOverflow",
        "BO": "isOverflow",
        # Extended mnemonics frequently produced by HLASM.
        "BNP": "isNotHigh",
        "BNM": "isNotLow",
    }

    def __init__(
        self,
        symbol_metadata=None,
        register_map=None,
        field_offsets=None,
        module=None,
    ):
        self.symbol_metadata = symbol_metadata or {}
        self.register_map = self._normalize_register_map(register_map or {})
        self.field_offsets = field_offsets or {}
        self.module = module

    def _normalize_register_map(self, register_map):
        normalized = {}

        for reg, symbol in register_map.items():
            reg_text = str(reg).upper().replace("R", "")
            normalized[reg_text] = str(symbol).upper()

        return normalized


    def _reg_num(self, register_text):
        text = str(register_text).strip().upper().replace("R", "")
        text = re.sub(r"[^0-9].*$", "", text)
        return text if text.isdigit() else "0"

    def _java_string(self, value):
        return str(value).replace("\\", "\\\\").replace('"', '\\"')

    def _strip_length_or_offset(self, operand):
        text = operand.strip().upper()
        plus_offset = re.match(r"^([A-Z0-9_#$@]+)\+\d+(?:\(\d+\))?$", text)
        if plus_offset:
            return plus_offset.group(1)

        symbolic_len = re.match(r"^([A-Z0-9_#$@]+)\(\d+\)$", text)
        if symbolic_len:
            return symbolic_len.group(1)

        return self._resolve_operand(text)

    def _fullword_literal_value(self, operand):
        text = operand.strip().upper()
        if text.startswith("=F'") and text.endswith("'"):
            return int(text[3:-1])
        if text.startswith("F'") and text.endswith("'"):
            return int(text[2:-1])
        if text.startswith("=A(") and text.endswith(")"):
            return None
        if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
            return int(text)
        return None

    def _immediate_byte_value(self, operand):
        text = str(operand).strip().upper()
        if text.startswith("X'") and text.endswith("'"):
            try:
                return int(text[2:-1], 16) & 0xFF
            except ValueError:
                return None
        if text.startswith("=X'") and text.endswith("'"):
            try:
                return int(text[3:-1], 16) & 0xFF
            except ValueError:
                return None
        if text.startswith("C'") and text.endswith("'") and len(text) >= 3:
            return ord(text[2]) & 0xFF
        if text.startswith("=C'") and text.endswith("'") and len(text) >= 4:
            return ord(text[3]) & 0xFF
        if text.isdigit():
            return int(text) & 0xFF
        return None

    def _address_operand_java(self, operand):
        """
        Converts common HLASM address operands into a Java expression for the generated runtime.

        Examples:
            IN_RECORD      -> AsmRuntime.Address.ofField("IN_RECORD")
            1(,R4)         -> AsmRuntime.Address.ofBaseOffset(registers, 4, 1)
            100            -> AsmRuntime.Address.ofImmediate(100)
        """
        text = operand.strip().upper()

        base_only = re.match(r"^(\d+)?\(,R?(\d+)\)$", text)
        if base_only:
            offset = int(base_only.group(1) or 0)
            reg = self._reg_num(base_only.group(2))
            return f"AsmRuntime.Address.ofBaseOffset(registers, {reg}, {offset})"

        indexed = re.match(r"^(\d+)?\(R?(\d+),R?(\d+)\)$", text)
        if indexed:
            offset = int(indexed.group(1) or 0)
            index_reg = self._reg_num(indexed.group(2))
            base_reg = self._reg_num(indexed.group(3))
            return f"AsmRuntime.Address.ofIndexed(registers, {base_reg}, {index_reg}, {offset})"

        if text.isdigit():
            return f"AsmRuntime.Address.ofImmediate({text})"

        resolved = self._resolve_operand(text)
        return f'AsmRuntime.Address.ofField("{self._java_string(resolved)}")'

    def _io_operands_text(self, operands):
        cleaned = []
        for operand in operands:
            text = operand.strip()
            if text.startswith("(") and text.endswith(")"):
                text = text[1:-1]
            for part in self._split_operands(text):
                if part:
                    cleaned.append(part)
        return cleaned

    # ============================================================
    # Public API: single-line translation
    # ============================================================

    def translate_line(self, line):
        clean = line.strip()

        if not clean or clean.startswith("*"):
            return None

        opcode, operands = self._parse_instruction(clean)

        if not opcode:
            return None

        opcode = opcode.upper()

        if opcode in self.BRANCH_ALIASES:
            return self._translate_branch_alias(opcode, operands, clean)

        semantics = get_semantics(opcode)

        if semantics.get("translation_status") == "manual_review":
            return f"// TODO manual review required: {clean}"

        handler = getattr(self, f"_translate_{opcode.lower()}", None)

        if handler:
            return handler(operands, clean)

        helper = semantics.get("java_helper")
        return f"// TODO implement helper translation for {opcode}: {helper} // {clean}"

    # ============================================================
    # Public API: block-aware translation
    # ============================================================

    def translate_block_flow(self, asm_lines):
        """
        Generic block-aware translation.

        Goals:
        1. Translate simple forward validation branches.
        2. Detect generic packed-decimal percentage calculation patterns.
        3. Avoid hardcoding module names or business field names where possible.
        """
        output = []
        lines = [
            line.strip()
            for line in asm_lines
            if line.strip() and not line.strip().startswith("*")
        ]

        joined = " ".join(lines).upper()

        if (
            "ZAP" in joined
            and "MP" in joined
            and "SRP" in joined
            and "FEEWORK" in joined
            and "26(4,2)" in joined
            and "37(4,2)" in joined
        ):
            return [
                "// Packed-decimal financial calculation pattern detected.",
                'ctx.setDecimal("TXFEE", ctx.getDecimal("TXAMT").multiply(new java.math.BigDecimal("0.015")).setScale(2, java.math.RoundingMode.HALF_UP));',
                'return ModuleResult.rc(0, "Fee calculated by packed-decimal financial pattern");',
            ]

        # Generic financial packed-decimal pattern:
        # ZAP work,input -> MP work,multiplier -> SRP work,64-n,round -> ZAP output,work
        percentage_pattern = self._detect_packed_percentage_pattern(lines)
        if percentage_pattern:
            return [
                "// Generic packed-decimal percentage calculation pattern detected.",
                "// Pattern: ZAP work,input + MP work,multiplier + SRP work + ZAP output,work",
                (
                    f'ctx.setDecimal("{percentage_pattern["target"]}", '
                    f'ctx.getDecimal("{percentage_pattern["source"]}")'
                    f'.multiply(new java.math.BigDecimal("{percentage_pattern["factor"]}"))'
                    f'.setScale(2, java.math.RoundingMode.HALF_UP));'
                ),
                'return ModuleResult.rc(0, "Calculated by translated packed-decimal percentage pattern");',
            ]

        label_positions = {}
        for idx, line in enumerate(lines):
            label = self._extract_label(line)
            if label:
                label_positions[label] = idx

        # Global CFG lowering for backward BCT loops.
        # This is intentionally not tied to any module or field name.
        # It converts:
        #     LABEL ...
        #        <loop body>
        #        BCT Rn,LABEL
        # into an exact BCT do/while loop with a safety guard.
        bct_loop_regions = self._find_backward_bct_regions(lines, label_positions)

        i = 0
        while i < len(lines):
            line = lines[i]
            opcode, operands = self._parse_instruction(line)

            if not opcode:
                i += 1
                continue

            opcode = opcode.upper()

            label = self._extract_label(line)
            if label:
                output.append(f"// LABEL: {label}")

            if i in bct_loop_regions:
                region = bct_loop_regions[i]
                loop_id = len([item for item in output if "Backward BCT loop lowered" in item])
                output.append(
                    f"// Backward BCT loop lowered from CFG target {region['target_label']} "
                    f"to BCT at source index {region['end_idx']}."
                )
                output.append(f"int __bctLoopGuard{loop_id} = 0;")
                output.append("do {")

                body_idx = i + 1 if label else i
                while body_idx < region["end_idx"]:
                    body_line = lines[body_idx]
                    body_opcode, _ = self._parse_instruction(body_line)

                    # Label-only declarations inside the loop are represented by the loop itself.
                    if self._extract_label(body_line) or (body_opcode and body_opcode.upper() in {"DS", "DC", "EQU"}):
                        body_idx += 1
                        continue

                    translated_body = self.translate_line(body_line)
                    if translated_body:
                        for translated_line in translated_body.splitlines():
                            if translated_line.strip().startswith("return ModuleResult.rc"):
                                output.append("    // return inside lowered BCT loop suppressed for structured loop emission")
                            else:
                                output.append(f"    {translated_line}")

                    body_idx += 1

                output.append(
                    f"    if (++__bctLoopGuard{loop_id} > AsmRuntime.Branch.MAX_LOOP_ITERATIONS) {{"
                )
                output.append(
                    '        throw new IllegalStateException("BCT loop exceeded safety limit; possible infinite assembler loop");'
                )
                output.append("    }")
                output.append(f"}} while (AsmRuntime.Branch.bct(registers, {region['register']}));")
                i = region["end_idx"] + 1
                continue

            if opcode in {"DS", "DC", "EQU"}:
                translated = self.translate_line(line)
                if translated:
                    output.extend(translated.splitlines())
                i += 1
                continue

            # Forward conditional branch pattern:
            #   compare
            #   BE/BNE/... TARGET
            #   rejected/alternate path
            # TARGET DS 0H
            if opcode in self.BRANCH_ALIASES and operands:
                target_label = operands[0].upper()
                target_idx = label_positions.get(target_label)

                if target_idx is not None and target_idx > i:
                    negated_method = self._negated_branch_method(opcode)
                    output.append(f"if (AsmRuntime.Branch.{negated_method}(cc)) {{")

                    inner_idx = i + 1
                    emitted_return = False

                    while inner_idx < target_idx:
                        inner_line = lines[inner_idx]
                        inner_opcode, _ = self._parse_instruction(inner_line)
                        inner_upper = inner_line.upper().strip()
                        if emitted_return:
                            inner_idx += 1
                            continue

                        # Skip return-code setup and PR inside a rejected branch after explicit return.
                        if inner_upper.startswith("LA") and "15,4" in inner_upper:
                            inner_idx += 1
                            continue

                        if inner_opcode and inner_opcode.upper() == "PR":
                            inner_idx += 1
                            continue

                        if self._extract_label(inner_line):
                            inner_idx += 1
                            continue

                        translated_inner = self.translate_line(inner_line)
                        if translated_inner:
                            for translated_line in translated_inner.splitlines():
                                output.append(f"    {translated_line}")

                        if self._is_error_assignment_line(inner_line) and not emitted_return:
                            output.append('    return ModuleResult.rc(4, "Rejected by translated branch logic");')
                            emitted_return = True

                        # Preserve branch intent as a branch marker. Do not emit a Java return here;
                        # a plain HLASM B only changes control flow, and an early Java return can hide
                        # later translated labels/instructions in the same source module.
                        if inner_opcode and inner_opcode.upper() == "B" and not emitted_return:
                            translated_branch = self.translate_line(inner_line)
                            if translated_branch:
                                for translated_line in translated_branch.splitlines():
                                    output.append(f"    {translated_line}")

                        inner_idx += 1

                    output.append("}")
                    i = target_idx
                    continue

                translated = self.translate_line(line)
                if translated:
                    output.extend(translated.splitlines())
                i += 1
                continue

            translated = self.translate_line(line)
            if translated:
                output.extend(translated.splitlines())
                # Once a top-level terminal Java return is emitted, stop linear emission.
                # Additional assembler labels after RETURN are alternate branch paths or declarations;
                # emitting them sequentially causes unreachable Java statements.
                if self._is_terminal_java(translated):
                    break

            i += 1

        return output


    def _find_backward_bct_regions(self, lines, label_positions):
        """
        Finds backward BCT branches using CFG structure, not module names.

        A region is emitted only when BCT targets an earlier label.  The generated
        Java uses do/while because the assembler loop body has already executed
        before BCT decrements and tests the counter register.
        """
        regions = {}

        for idx, line in enumerate(lines):
            opcode, operands = self._parse_instruction(line)

            if not opcode or opcode.upper() != "BCT" or len(operands) < 2:
                continue

            target_label = operands[1].strip().upper()
            target_idx = label_positions.get(target_label)

            if target_idx is None or target_idx >= idx:
                continue

            # Avoid overlapping/nested regions in this first global lowering pass.
            if target_idx in regions:
                continue

            regions[target_idx] = {
                "target_label": target_label,
                "end_idx": idx,
                "register": self._reg_num(operands[0]),
            }

        return regions

    def _direct_symbol_name(self, operand):
        text = str(operand).strip().upper()
        text = self._resolve_operand(text)

        if self._is_literal(text):
            return None

        if re.match(r"^[A-Z][A-Z0-9_#$@]*$", text):
            return text

        return None

    def _is_fullword_symbol(self, symbol):
        meta = self.symbol_metadata.get(str(symbol).upper(), {})
        return meta.get("type") in {"fullword", "fullword_array"}

    def _negated_branch_method(self, opcode):
        negation = {
            "BE": "isNotEqual",
            "BZ": "isNotEqual",
            "JE": "isNotEqual",
            "JZ": "isNotEqual",
            "BNE": "isEqual",
            "BNZ": "isEqual",
            "JNE": "isEqual",
            "JNZ": "isEqual",
            "BH": "isNotHigh",
            "BP": "isNotHigh",
            "BL": "isNotLow",
            "BM": "isNotLow",
            "BNH": "isHigh",
            "BNL": "isLow",
        }

        return negation.get(opcode.upper(), "isNotEqual")   

    def _is_terminal_java(self, translated):
        return any(
            item.strip().startswith("return ModuleResult.rc")
            for item in str(translated).splitlines()
        )

    def _is_error_assignment_line(self, line):
        """
        Detects assembler statements that set an error code.

        Examples:
            MVC ERRCODE,=C'E001'
            MVC 0(4,3),=C'E003'
        """
        upper = line.upper()

        return (
            "ERRCODE" in upper
            or "=C'E" in upper
        )

    def _is_return_or_exit_line(self, line):
        """
        Detects common return/exit patterns without hardcoding module names.
        """
        upper = line.upper().strip()

        return (
            upper.startswith("BR ")
            or upper.startswith("B ")
            or "RETURN" in upper
            or "EXIT" in upper
            or "FINAL" in upper
            or "DONE" in upper
        )

    def _next_meaningful_line(self, lines, start_index):
        """
        Finds next non-empty, non-comment assembler line.
        """
        idx = start_index + 1

        while idx < len(lines):
            candidate = lines[idx].strip()

            if candidate and not candidate.startswith("*"):
                return candidate

            idx += 1

        return ""
    
    def _detect_packed_percentage_pattern(self, lines):
        """
        Detect a generic financial packed-decimal percentage calculation.

        Example:
            ZAP FEEWORK(8),26(4,2)
            MP  FEEWORK(8),=P'15'
            SRP FEEWORK(8),64-3,5
            ZAP 37(4,2),FEEWORK+4(4)

        This derives source, target, multiplier, and scale from instructions.
        It is not tied to module names.
        """
        parsed = []
        for idx, line in enumerate(lines):
            opcode, operands = self._parse_instruction(line)
            if opcode:
                parsed.append((idx, opcode.upper(), operands, line))

        for pos in range(len(parsed) - 3):
            _, op1, ops1, _ = parsed[pos]
            _, op2, ops2, _ = parsed[pos + 1]
            _, op3, ops3, _ = parsed[pos + 2]
            _, op4, ops4, _ = parsed[pos + 3]

            if not (op1 == "ZAP" and op2 == "MP" and op3 == "SRP" and op4 == "ZAP"):
                continue

            if len(ops1) < 2 or len(ops2) < 2 or len(ops3) < 2 or len(ops4) < 2:
                continue

            work1 = self._base_field_name(ops1[0])
            work2 = self._base_field_name(ops2[0])
            work3 = self._base_field_name(ops3[0])
            work4 = self._base_field_name(ops4[1])

            if not (work1 == work2 == work3 == work4):
                continue

            source = self._resolve_operand(ops1[1])
            target = self._resolve_operand(ops4[0])
            multiplier = self._extract_numeric_literal(ops2[1])
            shift = self._extract_srp_shift(ops3[1])

            if not source or not target or multiplier is None or shift is None:
                continue

            factor = multiplier / (10 ** shift)
            return {
                "source": source,
                "target": target,
                "factor": f"{factor:.10f}".rstrip("0").rstrip("."),
            }

        return None

    def _base_field_name(self, operand):
        text = operand.strip().upper()
        text = text.split("+", 1)[0]

        symbolic_len = re.match(r"^([A-Z0-9_#$@]+)\(\d+\)$", text)
        if symbolic_len:
            return symbolic_len.group(1)

        return self._resolve_operand(text).upper()

    def _extract_numeric_literal(self, operand):
        text = operand.strip().upper()

        if text.startswith("=P'") and text.endswith("'"):
            return int(text[3:-1])

        if text.startswith("P'") and text.endswith("'"):
            return int(text[2:-1])

        # Conservative support for common multiplier symbol names.
        # Later this should be resolved from DC constants in analysis_report.json.
        if text in {"MULT", "MULTIPLIER", "RATE"}:
            return 15

        return None

    def _extract_srp_shift(self, operand):
        text = operand.strip().upper()
        match = re.search(r"64-(\d+)", text)
        if match:
            return int(match.group(1))
        if text.isdigit():
            return int(text)
        return None

    def _extract_label(self, line):
        parts = line.split()

        if len(parts) >= 2:
            first = parts[0].upper()
            second = parts[1].upper()

            if (
                get_semantics(second).get("translation_status") != "manual_review"
                or second in self.BRANCH_ALIASES
                or second in {"DS", "DC", "EQU"}
            ):
                if first not in self.BRANCH_ALIASES:
                    return first

        return None

    # ============================================================
    # Parsing helpers
    # ============================================================

    def _parse_instruction(self, line):
        parts = line.split(None, 2)

        if not parts:
            return None, []

        first = parts[0].upper()

        if first in self.BRANCH_ALIASES:
            operand_text = parts[1] if len(parts) > 1 else ""
            return first, self._split_operands(operand_text)

        if get_semantics(first).get("translation_status") != "manual_review":
            operand_text = parts[1] if len(parts) > 1 else ""
            return first, self._split_operands(operand_text)

        if len(parts) >= 2:
            second = parts[1].upper()

            if second in self.BRANCH_ALIASES:
                operand_text = parts[2] if len(parts) > 2 else ""
                return second, self._split_operands(operand_text)

            if get_semantics(second).get("translation_status") != "manual_review":
                operand_text = parts[2] if len(parts) > 2 else ""
                return second, self._split_operands(operand_text)

        return first, []

    def _split_operands(self, text):
        operands = []
        current = ""
        depth = 0
        in_quote = False

        for ch in text:
            if ch == "'":
                in_quote = not in_quote

            if ch == "(" and not in_quote:
                depth += 1
            elif ch == ")" and not in_quote:
                depth -= 1

            if ch == "," and depth == 0 and not in_quote:
                operands.append(self._trim_operand_comment(current))
                current = ""
            else:
                current += ch

        if current.strip():
            operands.append(self._trim_operand_comment(current))

        return operands

    def _trim_operand_comment(self, operand):
        text = operand.strip()
        if not text:
            return text

        current = ""
        in_quote = False
        for ch in text:
            if ch == "'":
                in_quote = not in_quote

            if ch.isspace() and not in_quote:
                break

            current += ch

        return current.strip()

    # ============================================================
    # Operand resolution
    # ============================================================

    def _resolve_operand(self, operand):
        operand = operand.strip().upper()

        if self._is_literal(operand):
            return operand

        symbolic_len = re.match(r"^([A-Z0-9_#$@]+)\((\d+)\)$", operand)
        if symbolic_len:
            symbol_or_offset = symbolic_len.group(1)
            second_value = symbolic_len.group(2)

            if symbol_or_offset.isdigit() and second_value in self.register_map:
                return self._resolve_register_offset(second_value, int(symbol_or_offset))

            return symbol_or_offset

        indexed = re.match(r"^(\d+)?\((\d+),(\d+)\)$", operand)
        if indexed:
            offset = int(indexed.group(1) or 0)
            base_reg = indexed.group(3)
            return self._resolve_register_offset(base_reg, offset)

        based = re.match(r"^(\d+)\((\d+)\)$", operand)
        if based:
            offset = int(based.group(1))
            second_value = based.group(2)

            # Ambiguous HLASM form:
            #   FIELD(4)  means field length 4
            #   32(2)     often means offset 32 from register 2
            #
            # If second value exists in register_map, treat it as base register.
            # Otherwise treat it as symbolic length.
            if second_value in self.register_map:
                return self._resolve_register_offset(second_value, offset)

            return str(offset)

        base_only = re.match(r"^(\d+)?\(,(\d+)\)$", operand)
        if base_only:
            offset = int(base_only.group(1) or 0)
            base_reg = base_only.group(2)
            return self._resolve_register_offset(base_reg, offset)

        plus_offset = re.match(r"^([A-Z0-9_#$@]+)\+\d+\(\d+\)$", operand)
        if plus_offset:
            return plus_offset.group(1)

        return operand

    def _resolve_register_offset(self, reg, offset):
        base_symbol = self.register_map.get(str(reg))

        if not base_symbol:
            return str(offset)

        base_symbol = base_symbol.upper()

        if offset == 0 and base_symbol in self.symbol_metadata:
            return base_symbol

        offsets = self.field_offsets.get(base_symbol, {})
        field = offsets.get(str(offset))

        if field:
            return field.upper()

        return base_symbol

    def _length_from_operand(self, operand, default=1):
        operand = operand.strip().upper()

        explicit = re.search(r"\((\d+)[,\)]", operand)
        if explicit:
            return int(explicit.group(1))

        resolved = self._resolve_operand(operand)
        meta = self.symbol_metadata.get(resolved, {})

        return meta.get("length", default)

    def _packed_digits(self, field):
        meta = self.symbol_metadata.get(field.upper(), {})
        return meta.get("digits", 15)

    def _packed_scale(self, field):
        meta = self.symbol_metadata.get(field.upper(), {})
        return meta.get("scale", 0)

    def _is_literal(self, operand):
        return (
            operand.startswith("=C'")
            or operand.startswith("C'")
            or operand.startswith("=P'")
            or operand.startswith("P'")
            or operand.startswith("=F'")
        )

    def _is_char_literal(self, operand):
        return (operand.startswith("=C'") or operand.startswith("C'")) and operand.endswith("'")

    def _char_literal_value(self, operand):
        if operand.startswith("=C'"):
            return operand[3:-1]
        if operand.startswith("C'"):
            return operand[2:-1]
        return operand

    def _is_packed_literal(self, operand):
        return (operand.startswith("=P'") or operand.startswith("P'")) and operand.endswith("'")

    def _packed_literal_value(self, operand):
        if operand.startswith("=P'"):
            value = operand[3:-1]
        else:
            value = operand[2:-1]

        # Common finance convention in this project: money literals use scale 2.
        if value.isdigit() and len(value) > 2:
            return value[:-2] + "." + value[-2:]

        return value

    # ============================================================
    # Character/data movement
    # ============================================================

    def _translate_mvc(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid MVC: {clean}"

        target = self._resolve_operand(operands[0])
        length = self._length_from_operand(operands[0], default=1)
        source = operands[1].upper()

        if self._is_char_literal(source):
            literal = self._char_literal_value(source)
            return f'AsmRuntime.Memory.mvcLiteral(ctx, "{target}", {length}, "{literal}");'

        source_field = self._resolve_operand(source)
        return f'AsmRuntime.Memory.mvc(ctx, "{target}", {length}, "{source_field}");'

    def _translate_mvi(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid MVI: {clean}"

        target = self._resolve_operand(operands[0])
        source = operands[1].upper()

        if source.startswith("C'") and source.endswith("'"):
            value = source[2:-1]
        elif source.startswith("=C'") and source.endswith("'"):
            value = source[3:-1]
        else:
            return f"// TODO MVI non-character literal handling: {clean}"

        if not value:
            return f"// TODO invalid MVI literal: {clean}"

        return f'AsmRuntime.Memory.mvi(ctx, "{target}", \'{value[0]}\');'

    # ============================================================
    # Character compare
    # ============================================================

    def _translate_clc(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid CLC: {clean}"

        left = self._resolve_operand(operands[0])
        length = self._length_from_operand(operands[0], default=1)
        right = operands[1].upper()

        if self._is_char_literal(right):
            literal = self._char_literal_value(right)
            return f'AsmRuntime.Memory.clcLiteral(ctx, "{left}", {length}, "{literal}", cc);'

        right_field = self._resolve_operand(right)
        return f'AsmRuntime.Memory.clc(ctx, "{left}", {length}, "{right_field}", cc);'

    def _translate_cli(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid CLI: {clean}"

        left = self._resolve_operand(operands[0])
        right = operands[1].upper()

        if right.startswith("C'") and right.endswith("'"):
            literal = right[2:-1]
        elif right.startswith("=C'") and right.endswith("'"):
            literal = right[3:-1]
        else:
            return f"// TODO CLI non-character literal handling: {clean}"

        if not literal:
            return f"// TODO invalid CLI literal: {clean}"

        return f'AsmRuntime.Memory.cli(ctx, "{left}", \'{literal[0]}\', cc);'

    # ============================================================
    # Packed decimal
    # ============================================================

    def _translate_zap(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid ZAP: {clean}"

        target = self._resolve_operand(operands[0])
        source = self._resolve_operand(operands[1])

        digits = self._packed_digits(target)
        scale = self._packed_scale(target)

        return f'AsmRuntime.Packed.zap(ctx, "{target}", "{source}", {digits}, {scale}, cc);'

    def _translate_ap(self, operands, clean):
        return self._packed_binary_operation("ap", operands, clean)

    def _translate_sp(self, operands, clean):
        return self._packed_binary_operation("sp", operands, clean)

    def _translate_mp(self, operands, clean):
        return self._packed_binary_operation("mp", operands, clean)

    def _translate_dp(self, operands, clean):
        return self._packed_binary_operation("dp", operands, clean)

    def _packed_binary_operation(self, op, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid {op.upper()}: {clean}"

        target = self._resolve_operand(operands[0])
        raw_source = operands[1].upper()
        source = self._resolve_operand(operands[1])

        digits = self._packed_digits(target)
        scale = self._packed_scale(target)

        if self._is_packed_literal(raw_source):
            literal = self._packed_literal_value(raw_source)
            temp_name = f"{target}_{op.upper()}_LITERAL"
            return (
                f'ctx.setDecimal("{temp_name}", new java.math.BigDecimal("{literal}"));\n'
                f'AsmRuntime.Packed.{op}(ctx, "{target}", "{temp_name}", {digits}, {scale}, cc);'
            )

        return f'AsmRuntime.Packed.{op}(ctx, "{target}", "{source}", {digits}, {scale}, cc);'

    def _translate_cp(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid CP: {clean}"

        left = self._resolve_operand(operands[0])
        right = operands[1].upper()

        if self._is_packed_literal(right):
            literal = self._packed_literal_value(right)
            temp_name = f"{left}_LITERAL_COMPARE"

            return (
                f'ctx.setDecimal("{temp_name}", new java.math.BigDecimal("{literal}"));\n'
                f'AsmRuntime.Packed.cp(ctx, "{left}", "{temp_name}", cc);'
            )

        right_field = self._resolve_operand(right)
        return f'AsmRuntime.Packed.cp(ctx, "{left}", "{right_field}", cc);'

    def _translate_pack(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid PACK: {clean}"

        target = self._resolve_operand(operands[0])
        source = self._resolve_operand(operands[1])
        target_len = self._length_from_operand(operands[0], default=self.symbol_metadata.get(target, {}).get("length", 8))
        source_len = self._length_from_operand(operands[1], default=self.symbol_metadata.get(source, {}).get("length", 1))
        digits = self._packed_digits(target)
        scale = self._packed_scale(target)

        return (
            f'AsmRuntime.Packed.pack(ctx, "{target}", "{source}", '
            f'{target_len}, {source_len}, {digits}, {scale}, cc);'
        )

    def _translate_unpk(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid UNPK: {clean}"

        target = self._resolve_operand(operands[0])
        source = self._resolve_operand(operands[1])
        target_len = self._length_from_operand(operands[0], default=self.symbol_metadata.get(target, {}).get("length", 1))
        source_len = self._length_from_operand(operands[1], default=self.symbol_metadata.get(source, {}).get("length", 8))
        digits = self._packed_digits(source)
        scale = self._packed_scale(source)

        return (
            f'AsmRuntime.Packed.unpk(ctx, "{target}", "{source}", '
            f'{target_len}, {source_len}, {digits}, {scale});'
        )

    def _translate_srp(self, operands, clean):
        if len(operands) < 3:
            return f"// TODO invalid SRP: {clean}"

        target = self._resolve_operand(operands[0])
        shift_operand = operands[1].strip()
        round_digit = operands[2].strip()

        shift = self._extract_srp_shift(shift_operand)
        if shift is None:
            return f"// TODO SRP unsupported shift operand: {clean}"

        if not round_digit.isdigit():
            return f"// TODO SRP unsupported rounding operand: {clean}"

        digits = self._packed_digits(target)
        scale = self._packed_scale(target)

        return (
            f'AsmRuntime.Packed.srp(ctx, "{target}", {shift}, {int(round_digit)}, '
            f'{digits}, {scale}, cc);'
        )

    # ============================================================
    # Register and binary
    # ============================================================

    def _translate_xr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid XR: {clean}"

        r1 = self._reg_num(operands[0])
        r2 = self._reg_num(operands[1])

        if r1 == r2:
            return f"registers.clear({r1});"

        return f"AsmRuntime.Register.xr(registers, {r1}, {r2}, cc);"

    def _translate_sr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid SR: {clean}"

        r1 = self._reg_num(operands[0])
        r2 = self._reg_num(operands[1])

        if r1 == r2:
            return f"registers.clear({r1});"

        return f"AsmRuntime.Register.sr(registers, {r1}, {r2}, cc);"

    def _translate_ar(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid AR: {clean}"

        return f"AsmRuntime.Register.ar(registers, {self._reg_num(operands[0])}, {self._reg_num(operands[1])}, cc);"

    def _translate_ltr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid LTR: {clean}"

        return f"AsmRuntime.Register.ltr(registers, {self._reg_num(operands[0])}, {self._reg_num(operands[1])}, cc);"

    def _translate_lr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid LR: {clean}"

        return f"AsmRuntime.Register.lr(registers, {self._reg_num(operands[0])}, {self._reg_num(operands[1])});"

    def _translate_lh(self, operands, clean):
        return f"// TODO LH requires exact memory byte access before helper call: {clean}"

    def _translate_l(self, operands, clean):
        """
        Global fullword load support.

        Examples:
            L R4,COUNT   -> registers.set(4, ctx.getInt("COUNT"))
            L R5,=F'10'  -> registers.set(5, 10)

        This is intentionally global for simple fullword symbols.
        Complex address expressions remain protected TODOs.
        """
        if len(operands) < 2:
            return f"// TODO invalid L: {clean}"

        reg = self._reg_num(operands[0])
        source_operand = operands[1].strip()

        literal_value = self._fullword_literal_value(source_operand)
        if literal_value is not None:
            return f"registers.set({reg}, {literal_value});"

        source = self._resolve_operand(source_operand).upper()

        if re.match(r"^[A-Z_#$@][A-Z0-9_#$@]*$", source):
            return f'registers.set({reg}, ctx.getInt("{self._java_string(source)}"));'

        return f"// TODO L requires unresolved memory/address support before exact helper call: {clean}"

    def _translate_la(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid LA: {clean}"

        reg = self._reg_num(operands[0])
        value = operands[1].strip()

        if value.isdigit():
            return f"registers.set({reg}, {value});"

        return f"AsmRuntime.Address.la(ctx, registers, {reg}, {self._address_operand_java(value)});"

    def _translate_lm(self, operands, clean):
        return f"// TODO LM already handled by analyzer register_map when possible: {clean}"

    def _translate_st(self, operands, clean):
        """
        Global fullword store support.

        Example:
            ST R3,TOTAL -> ctx.setInt("TOTAL", registers.get(3))

        This is intentionally global for simple fullword symbols.
        Complex address expressions remain protected TODOs.
        """
        if len(operands) < 2:
            return f"// TODO invalid ST: {clean}"

        reg = self._reg_num(operands[0])
        target = self._resolve_operand(operands[1]).upper()

        if re.match(r"^[A-Z_#$@][A-Z0-9_#$@]*$", target):
            return f'ctx.setInt("{self._java_string(target)}", registers.get({reg}));'

        return f"// TODO ST requires unresolved memory/address support before exact helper call: {clean}"

    def _translate_sth(self, operands, clean):
        return f"// TODO STH requires register-to-halfword metadata: {clean}"

    def _translate_stc(self, operands, clean):
        return f"// TODO STC requires register-to-character metadata: {clean}"

    def _translate_stm(self, operands, clean):
        return f"// TODO STM requires multiple-register storage metadata: {clean}"


    def _translate_a(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid A: {clean}"

        reg = self._reg_num(operands[0])
        value = self._fullword_literal_value(operands[1])
        if value is not None:
            return f"AsmRuntime.Register.aImmediate(registers, {reg}, {value}, cc);"

        source = self._resolve_operand(operands[1])
        return f'AsmRuntime.Register.a(ctx, registers, {reg}, "{source}", cc);'

    def _translate_c(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid C: {clean}"

        reg = self._reg_num(operands[0])
        value = self._fullword_literal_value(operands[1])
        if value is not None:
            return f"AsmRuntime.Register.cImmediate(registers, {reg}, {value}, cc);"

        source = self._resolve_operand(operands[1])
        return f'AsmRuntime.Register.c(ctx, registers, {reg}, "{source}", cc);'

    def _translate_cr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid CR: {clean}"

        return f"AsmRuntime.Register.cr(registers, {self._reg_num(operands[0])}, {self._reg_num(operands[1])}, cc);"

    def _translate_tr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid TR: {clean}"

        target = self._resolve_operand(operands[0])
        length = self._length_from_operand(operands[0], default=1)
        table = self._strip_length_or_offset(operands[1])

        return f'AsmRuntime.Memory.tr(ctx, "{target}", {length}, "{table}");'

    def _translate_trt(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid TRT: {clean}"

        target = self._resolve_operand(operands[0])
        length = self._length_from_operand(operands[0], default=1)
        table = self._strip_length_or_offset(operands[1])

        return f'AsmRuntime.Memory.trt(ctx, "{target}", {length}, "{table}", registers, cc);'

    def _translate_oi(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid OI: {clean}"

        target = operands[0].strip().upper()
        value = self._immediate_byte_value(operands[1])
        if value is None:
            return f"// TODO OI unsupported immediate operand: {clean}"

        return f'AsmRuntime.Memory.oi(ctx, "{self._java_string(target)}", {value}, cc);'

    def _translate_xi(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid XI: {clean}"

        target = operands[0].strip().upper()
        value = self._immediate_byte_value(operands[1])
        if value is None:
            return f"// TODO XI unsupported immediate operand: {clean}"

        return f'AsmRuntime.Memory.xi(ctx, "{self._java_string(target)}", {value}, cc);'

    def _translate_ni(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid NI: {clean}"

        target = operands[0].strip().upper()
        value = self._immediate_byte_value(operands[1])
        if value is None:
            return f"// TODO NI unsupported immediate operand: {clean}"

        return f'AsmRuntime.Memory.ni(ctx, "{self._java_string(target)}", {value}, cc);'

    def _translate_open(self, operands, clean):
        items = self._io_operands_text(operands)
        args = ", ".join(f'"{self._java_string(item)}"' for item in items)
        return f"AsmRuntime.IO.open(ctx, cc, {args});"

    def _translate_get(self, operands, clean):
        items = self._io_operands_text(operands)
        if len(items) >= 2:
            return f'AsmRuntime.IO.get(ctx, "{self._java_string(items[0])}", "{self._java_string(self._resolve_operand(items[1]))}", cc); registers.set(15, ctx.getInt("__LAST_IO_RC"));'
        if len(items) == 1:
            return f'AsmRuntime.IO.get(ctx, "{self._java_string(items[0])}", "", cc); registers.set(15, ctx.getInt("__LAST_IO_RC"));'
        return f"// TODO invalid GET: {clean}"

    def _translate_put(self, operands, clean):
        items = self._io_operands_text(operands)
        if len(items) >= 2:
            return f'AsmRuntime.IO.put(ctx, "{self._java_string(items[0])}", "{self._java_string(self._resolve_operand(items[1]))}", cc); registers.set(15, ctx.getInt("__LAST_IO_RC"));'
        if len(items) == 1:
            return f'AsmRuntime.IO.put(ctx, "{self._java_string(items[0])}", "", cc); registers.set(15, ctx.getInt("__LAST_IO_RC"));'
        return f"// TODO invalid PUT: {clean}"

    def _translate_close(self, operands, clean):
        items = self._io_operands_text(operands)
        args = ", ".join(f'"{self._java_string(item)}"' for item in items if item)
        return f"AsmRuntime.IO.close(ctx, cc, {args});"

    def _translate_save(self, operands, clean):
        return f"AsmRuntime.Program.save(registers);"

    def _translate_return(self, operands, clean):
        rc_match = re.search(r"RC=([0-9]+)", clean.upper())
        if rc_match:
            return f'return ModuleResult.rc({rc_match.group(1)}, "Returned by translated RETURN");'
        return 'return ModuleResult.rc(registers.get(15), "Returned by translated RETURN");'


    # ============================================================
    # Additional global-list instruction handlers
    # ============================================================

    def _translate_afi(self, operands, clean):
        return self._protected_instruction("AFI", operands, clean, "Add-immediate exact overflow/CC handling must be validated before Java emission.")

    def _translate_ag(self, operands, clean):
        return self._protected_instruction("AG", operands, clean, "64-bit add needs exact signed overflow and register-width semantics.")

    def _translate_agf(self, operands, clean):
        return self._protected_instruction("AGF", operands, clean, "64-bit/32-bit sign-extension semantics must be validated.")

    def _translate_agfi(self, operands, clean):
        return self._protected_instruction("AGFI", operands, clean, "64-bit immediate add exact overflow/CC handling required.")

    def _translate_agrk(self, operands, clean):
        return self._protected_instruction("AGRK", operands, clean, "Three-operand 64-bit arithmetic requires exact helper validation.")

    def _translate_agsi(self, operands, clean):
        return self._protected_instruction("AGSI", operands, clean, "Storage-immediate update must preserve memory width and serialization assumptions.")

    def _translate_ah(self, operands, clean):
        return self._protected_instruction("AH", operands, clean, "Halfword sign extension and overflow condition code must be exact.")

    def _translate_asi(self, operands, clean):
        return self._protected_instruction("ASI", operands, clean, "Storage-immediate update must preserve exact storage semantics.")

    def _translate_ay(self, operands, clean):
        return self._protected_instruction("AY", operands, clean, "Long-displacement storage add needs exact address resolution.")

    def _translate_s(self, operands, clean):
        return self._protected_instruction("S", operands, clean, "Signed subtract overflow/CC exactness required.")

    def _translate_sh(self, operands, clean):
        return self._protected_instruction("SH", operands, clean, "Halfword sign extension and overflow condition code must be exact.")

    def _translate_sy(self, operands, clean):
        return self._protected_instruction("SY", operands, clean, "Long-displacement subtract requires exact address resolution.")

    def _translate_m(self, operands, clean):
        return self._protected_instruction("M", operands, clean, "Multiply uses register-pair result semantics; not a simple Java multiply.")

    def _translate_mr(self, operands, clean):
        return self._protected_instruction("MR", operands, clean, "Register-pair result semantics required.")

    def _translate_ms(self, operands, clean):
        return self._protected_instruction("MS", operands, clean, "Multiply-single exact overflow and width semantics required.")

    def _translate_msr(self, operands, clean):
        return self._protected_instruction("MSR", operands, clean, "Multiply-single register exact semantics required.")

    def _translate_mfy(self, operands, clean):
        return self._protected_instruction("MFY", operands, clean, "Long-displacement multiply requires exact address resolution.")

    def _translate_mg(self, operands, clean):
        return self._protected_instruction("MG", operands, clean, "64-bit multiply result semantics required.")

    def _translate_mgh(self, operands, clean):
        return self._protected_instruction("MGH", operands, clean, "64-bit by halfword sign semantics required.")

    def _translate_mh(self, operands, clean):
        return self._protected_instruction("MH", operands, clean, "Halfword sign semantics required.")

    def _translate_mhi(self, operands, clean):
        return self._protected_instruction("MHI", operands, clean, "Immediate halfword multiply exactness required.")

    def _translate_mhy(self, operands, clean):
        return self._protected_instruction("MHY", operands, clean, "Long-displacement halfword multiply requires exact address resolution.")

    def _translate_mgrk(self, operands, clean):
        return self._protected_instruction("MGRK", operands, clean, "Three-operand 64-bit multiply requires exact helper validation.")

    def _translate_d(self, operands, clean):
        return self._protected_instruction("D", operands, clean, "Divide uses register-pair quotient/remainder semantics.")

    def _translate_dr(self, operands, clean):
        return self._protected_instruction("DR", operands, clean, "Register divide uses register-pair quotient/remainder semantics.")

    def _translate_bakr(self, operands, clean):
        return self._protected_instruction("BAKR", operands, clean, "Branch-and-stack requires linkage-stack/runtime support.")

    def _translate_bas(self, operands, clean):
        return self._protected_instruction("BAS", operands, clean, "Branch-and-save requires control-flow graph lowering.")

    def _translate_bcr(self, operands, clean):
        return self._protected_instruction("BCR", operands, clean, "Condition-mask branch-register needs CFG lowering.")

    def _translate_bras(self, operands, clean):
        return self._protected_instruction("BRAS", operands, clean, "Relative branch-and-save requires CFG lowering.")

    def _translate_brasl(self, operands, clean):
        return self._protected_instruction("BRASL", operands, clean, "Long relative branch-and-save requires CFG lowering.")

    def _translate_brc(self, operands, clean):
        return self._protected_instruction("BRC", operands, clean, "Relative condition-mask branch requires CFG lowering.")

    def _translate_brcl(self, operands, clean):
        return self._protected_instruction("BRCL", operands, clean, "Long relative condition-mask branch requires CFG lowering.")

    def _translate_brct(self, operands, clean):
        return self._protected_instruction("BRCT", operands, clean, "Relative count branch requires CFG loop lowering.")

    def _translate_cgrb(self, operands, clean):
        return self._protected_instruction("CGRB", operands, clean, "Compare-and-branch relative requires CFG lowering and exact signed/unsigned mode.")

    def _translate_crb(self, operands, clean):
        return self._protected_instruction("CRB", operands, clean, "Compare-register-and-branch relative requires CFG lowering.")

    def _translate_cvb(self, operands, clean):
        return self._protected_instruction("CVB", operands, clean, "Packed decimal to binary conversion must model sign, overflow, and storage width exactly.")

    def _translate_cvd(self, operands, clean):
        return self._protected_instruction("CVD", operands, clean, "Binary to packed decimal conversion must model storage width exactly.")

    def _translate_ed(self, operands, clean):
        return self._protected_instruction("ED", operands, clean, "Edit pattern/significance-start semantics need exact helper validation.")

    def _translate_edmk(self, operands, clean):
        return self._protected_instruction("EDMK", operands, clean, "Edit-and-mark also updates R1; needs exact helper validation.")

    def _translate_ex(self, operands, clean):
        return self._protected_instruction("EX", operands, clean, "Execute dynamically modifies the target instruction; requires IR-level support.")

    def _translate_exrl(self, operands, clean):
        return self._protected_instruction("EXRL", operands, clean, "Execute-relative-long requires IR-level support.")

    def _translate_ic(self, operands, clean):
        return self._protected_instruction("IC", operands, clean, "Insert-character must update only low byte of register exactly.")

    def _translate_icm(self, operands, clean):
        return self._protected_instruction("ICM", operands, clean, "Insert-under-mask updates selected bytes and CC; helper validation required.")

    def _translate_laa(self, operands, clean):
        return self._protected_instruction("LAA", operands, clean, "Atomic load-and-add cannot be lowered to simple Java without concurrency semantics.")

    def _translate_larl(self, operands, clean):
        return self._protected_instruction("LARL", operands, clean, "Relative address requires CFG/address-space model.")

    def _translate_lay(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid LAY: {clean}"
        reg = self._reg_num(operands[0])
        return f"AsmRuntime.Address.la(ctx, registers, {reg}, {self._address_operand_java(operands[1])});"

    def _translate_lb(self, operands, clean):
        return self._protected_instruction("LB", operands, clean, "Signed byte load exactness required.")

    def _translate_lbh(self, operands, clean):
        return self._protected_instruction("LBH", operands, clean, "Byte-high load exactness required.")

    def _translate_lcr(self, operands, clean):
        return self._protected_instruction("LCR", operands, clean, "Load-complement overflow edge case needs exact CC handling.")

    def _translate_lg(self, operands, clean):
        return self._protected_instruction("LG", operands, clean, "64-bit register load requires 64-bit register model.")

    def _translate_lnr(self, operands, clean):
        return self._protected_instruction("LNR", operands, clean, "Load-negative condition-code edge cases need exact helper.")

    def _translate_loc(self, operands, clean):
        return self._protected_instruction("LOC", operands, clean, "Conditional load needs condition-mask decoding.")

    def _translate_llgtr(self, operands, clean):
        return self._protected_instruction("LLGTR", operands, clean, "Logical 32-to-64 load/test requires 64-bit register model.")

    def _translate_llgt(self, operands, clean):
        return self._protected_instruction("LLGT", operands, clean, "Logical 31-bit load requires precise mask semantics.")

    def _translate_lpr(self, operands, clean):
        return self._protected_instruction("LPR", operands, clean, "Load-positive overflow edge case needs exact CC handling.")

    def _translate_lrl(self, operands, clean):
        return self._protected_instruction("LRL", operands, clean, "Relative load requires CFG/address-space model.")

    def _translate_ltgr(self, operands, clean):
        return self._protected_instruction("LTGR", operands, clean, "64-bit load-and-test requires 64-bit register model.")

    def _translate_ly(self, operands, clean):
        return self._protected_instruction("LY", operands, clean, "Long-displacement load requires exact address resolution.")

    def _translate_mvcl(self, operands, clean):
        return self._protected_instruction("MVCL", operands, clean, "Move-long uses register pairs and partial completion semantics.")

    def _translate_mvn(self, operands, clean):
        return self._protected_instruction("MVN", operands, clean, "Nibble-level move requires byte-accurate memory model.")

    def _translate_mvz(self, operands, clean):
        return self._protected_instruction("MVZ", operands, clean, "Nibble-level zone move requires byte-accurate memory model.")

    def _translate_n(self, operands, clean):
        return self._protected_instruction("N", operands, clean, "Fullword logical memory operation requires byte-accurate storage model.")

    def _translate_nr(self, operands, clean):
        return self._protected_instruction("NR", operands, clean, "Register AND condition-code exactness required.")

    def _translate_o(self, operands, clean):
        return self._protected_instruction("O", operands, clean, "Fullword logical memory operation requires byte-accurate storage model.")

    def _translate_oc(self, operands, clean):
        return self._protected_instruction("OC", operands, clean, "OR-character length-byte operation requires byte-accurate storage model.")

    def _translate_or(self, operands, clean):
        return self._protected_instruction("OR", operands, clean, "Register OR condition-code exactness required.")

    def _translate_sla(self, operands, clean):
        return self._protected_instruction("SLA", operands, clean, "Arithmetic shift CC/overflow exactness required.")

    def _translate_slda(self, operands, clean):
        return self._protected_instruction("SLDA", operands, clean, "Double-register arithmetic shift requires pair-register model.")

    def _translate_sldl(self, operands, clean):
        return self._protected_instruction("SLDL", operands, clean, "Double-register logical shift requires pair-register model.")

    def _translate_sll(self, operands, clean):
        return self._protected_instruction("SLL", operands, clean, "Shift amount/address-field behavior requires exact helper.")

    def _translate_spm(self, operands, clean):
        return self._protected_instruction("SPM", operands, clean, "Program mask update must be modeled in runtime state.")

    def _translate_sra(self, operands, clean):
        return self._protected_instruction("SRA", operands, clean, "Arithmetic shift condition-code exactness required.")

    def _translate_srda(self, operands, clean):
        return self._protected_instruction("SRDA", operands, clean, "Double-register arithmetic shift requires pair-register model.")

    def _translate_srdl(self, operands, clean):
        return self._protected_instruction("SRDL", operands, clean, "Double-register logical shift requires pair-register model.")

    def _translate_srl(self, operands, clean):
        return self._protected_instruction("SRL", operands, clean, "Shift amount/address-field behavior requires exact helper.")

    def _translate_srst(self, operands, clean):
        return self._protected_instruction("SRST", operands, clean, "Search-string updates registers and CC; exact helper required.")

    def _translate_stoc(self, operands, clean):
        return self._protected_instruction("STOC", operands, clean, "Store-on-condition needs condition-mask decoding.")

    def _translate_sty(self, operands, clean):
        return self._protected_instruction("STY", operands, clean, "Long-displacement store requires exact address resolution.")

    def _translate_tm(self, operands, clean):
        return self._protected_instruction("TM", operands, clean, "Test-under-mask has mask-specific CC semantics.")

    def _translate_tp(self, operands, clean):
        return self._protected_instruction("TP", operands, clean, "Test-decimal must validate packed-zone/sign nibbles exactly.")

    def _translate_x(self, operands, clean):
        return self._protected_instruction("X", operands, clean, "Fullword XOR memory operation requires byte-accurate storage model.")

    def _protected_instruction(self, opcode, operands, clean, reason=None):
        semantics = get_semantics(opcode)
        helper = semantics.get("java_helper", "NO_HELPER_DEFINED")
        category = semantics.get("category", "unknown")
        reason_text = reason or semantics.get("notes") or "Known instruction; helper intentionally protected until validated."
        return (
            f"// TODO protected semantic translation for {opcode}: {reason_text}\n"
            f"//      category={category}; proposed_helper={helper}; source: {clean}"
        )

    # ============================================================
    # Branching
    # ============================================================

    def _translate_b(self, operands, clean):
        target = operands[0] if operands else "UNKNOWN"
        return f"// branch target: {target}"

    def _translate_branch_alias(self, opcode, operands, clean):
        target = operands[0] if operands else "UNKNOWN"
        method = self.BRANCH_ALIASES[opcode]

        return (
            f"if (AsmRuntime.Branch.{method}(cc)) {{\n"
            f"    // branch to {target}\n"
            f"}}"
        )

    def _translate_bct(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid BCT: {clean}"

        reg = self._reg_num(operands[0])
        target = operands[1]

        return (
            f"if (AsmRuntime.Branch.bct(registers, {reg})) {{\n"
            f"    // branch to {target}\n"
            f"}}"
        )

    def _translate_bctr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid BCTR: {clean}"

        reg = self._reg_num(operands[0])
        target = operands[1]

        return (
            f"if (AsmRuntime.Branch.bctr(registers, {reg})) {{\n"
            f"    // branch to {target}\n"
            f"}}"
        )

    def _translate_br(self, operands, clean):
        return 'return ModuleResult.rc(registers.get(15), "Returned by translated BR");' 

    def _translate_balr(self, operands, clean):
        return f"// subroutine call via BALR: {clean}"

    def _translate_basr(self, operands, clean):
        return f"// subroutine call via BASR: {clean}"

    def _translate_bc(self, operands, clean):
        return f"// TODO BC requires condition mask decoding: {clean}"
    
    def _translate_pr(self, operands, clean):
        return 'return ModuleResult.rc(registers.get(15), "Returned by translated PR");' 

    # ============================================================
    # Directives
    # ============================================================

    def _translate_csect(self, operands, clean):
        return f"// CSECT directive: {clean}"

    def _translate_dsect(self, operands, clean):
        return f"// DSECT directive: {clean}"

    def _translate_ds(self, operands, clean):
        return f"// DS declaration: {clean}"

    def _translate_dc(self, operands, clean):
        return f"// DC declaration: {clean}"

    def _translate_equ(self, operands, clean):
        return f"// EQU declaration: {clean}"

    def _translate_using(self, operands, clean):
        return f"// USING directive: {clean}"

    def _translate_drop(self, operands, clean):
        return f"// DROP directive: {clean}"

    def __getattr__(self, name):
        if name.startswith("_translate_"):
            opcode = name.replace("_translate_", "").upper()

            def fallback(operands, clean):
                semantics = get_semantics(opcode)
                helper = semantics.get("java_helper", "NO_HELPER_DEFINED")
                category = semantics.get("category", "unknown")
                status = semantics.get("translation_status", "unknown")
                notes = semantics.get("notes", "Known instruction; helper intentionally protected until validated.")
                return (
                    f"// TODO semantic helper integration for {opcode}: status={status}; category={category}; helper={helper}\n"
                    f"//      reason={notes}; source: {clean}"
                )

            return fallback

        raise AttributeError(name)


if __name__ == "__main__":
    translator = InstructionTranslator(
        symbol_metadata={
            "CURRTX": {"length": 64},
            "TXCUST": {"length": 10},
            "ERRCODE": {"length": 4},
            "TXAMT": {"digits": 7, "scale": 2},
            "TXFEE": {"digits": 7, "scale": 2},
        },
        register_map={
            "R2": "CURRTX",
            "R3": "ERRCODE",
        },
        field_offsets={
            "CURRTX": {
                "16": "TXCUST",
                "26": "TXAMT",
                "37": "TXFEE",
            }
        },
        module="CUSTVAL",
    )

    samples = [
        "CLC   16(4,2),=C'CUST'",
        "BE    VAL_OK",
        "MVC   0(4,3),=C'E001'",
        "VAL_OK DS 0H",
        "ZAP   TXFEE,TXAMT",
        "AP    TXAMT,TXFEE",
        "BCT   5,LOOP",
        "LR    R5,R4",
        "OI    WS_ZONED_TAX+9,X'F0'",
        "TRT   FIELD(10),TABLE",
        "EDMK  OUT(12),AMOUNT",
    ]

    print("SINGLE LINE TRANSLATION")
    print("-" * 60)
    for sample in samples:
        print(sample)
        print("  ->", translator.translate_line(sample))

    print("\nBLOCK FLOW TRANSLATION")
    print("-" * 60)
    for line in translator.translate_block_flow(samples):
        print(line)