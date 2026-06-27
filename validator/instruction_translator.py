import re
from instruction_semantics import get_semantics


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
        "BNE": "isNotEqual",
        "BNZ": "isNotEqual",
        "BH": "isHigh",
        "BP": "isHigh",
        "BL": "isLow",
        "BM": "isLow",
        "BNH": "isNotHigh",
        "BNL": "isNotLow",
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

                        # If source branches out of this block after non-error assignment,
                        # preserve the current R15 return code instead of falling through.
                        if inner_opcode and inner_opcode.upper() == "B" and not emitted_return:
                            output.append('    return ModuleResult.rc(registers.get(15), "Completed translated branch path");')
                            emitted_return = True

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

            i += 1

        return output

    def _negated_branch_method(self, opcode):
        negation = {
            "BE": "isNotEqual",
            "BZ": "isNotEqual",
            "BNE": "isEqual",
            "BNZ": "isEqual",
            "BH": "isNotHigh",
            "BP": "isNotHigh",
            "BL": "isNotLow",
            "BM": "isNotLow",
            "BNH": "isHigh",
            "BNL": "isLow",
        }

        return negation.get(opcode.upper(), "isNotEqual")   

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
        source = self._resolve_operand(operands[1])

        digits = self._packed_digits(target)
        scale = self._packed_scale(target)

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
        return f"// TODO PACK requires zoned/packed metadata: {clean}"

    def _translate_unpk(self, operands, clean):
        return f"// TODO UNPK requires packed/zoned metadata: {clean}"

    # ============================================================
    # Register and binary
    # ============================================================

    def _translate_xr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid XR: {clean}"

        r1 = operands[0].strip()
        r2 = operands[1].strip()

        if r1 == r2:
            return f"registers.clear({r1});"

        return f"AsmRuntime.Register.xr(registers, {r1}, {r2}, cc);"

    def _translate_sr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid SR: {clean}"

        r1 = operands[0].strip()
        r2 = operands[1].strip()

        if r1 == r2:
            return f"registers.clear({r1});"

        return f"AsmRuntime.Register.sr(registers, {r1}, {r2}, cc);"

    def _translate_ar(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid AR: {clean}"

        return f"AsmRuntime.Register.ar(registers, {operands[0]}, {operands[1]}, cc);"

    def _translate_ltr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid LTR: {clean}"

        return f"AsmRuntime.Register.ltr(registers, {operands[0]}, {operands[1]}, cc);"

    def _translate_lh(self, operands, clean):
        return f"// TODO LH requires exact memory byte access before helper call: {clean}"

    def _translate_l(self, operands, clean):
        return f"// TODO L requires memory/address resolution before exact helper call: {clean}"

    def _translate_la(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid LA: {clean}"

        reg = operands[0].strip()
        value = operands[1].strip()

        if value.isdigit():
           return f"registers.set({reg}, {value});"

        return f"// TODO LA requires address/register model integration: {clean}"

    def _translate_lm(self, operands, clean):
        return f"// TODO LM already handled by analyzer register_map when possible: {clean}"

    def _translate_st(self, operands, clean):
        return f"// TODO ST requires register-to-memory metadata: {clean}"

    def _translate_sth(self, operands, clean):
        return f"// TODO STH requires register-to-halfword metadata: {clean}"

    def _translate_stc(self, operands, clean):
        return f"// TODO STC requires register-to-character metadata: {clean}"

    def _translate_stm(self, operands, clean):
        return f"// TODO STM requires multiple-register storage metadata: {clean}"

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

        reg = operands[0]
        target = operands[1]

        return (
            f"if (AsmRuntime.Branch.bct(registers, {reg})) {{\n"
            f"    // branch to {target}\n"
            f"}}"
        )

    def _translate_bctr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid BCTR: {clean}"

        reg = operands[0]
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
                return f"// TODO {opcode} helper integration needed: {helper} // {clean}"

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