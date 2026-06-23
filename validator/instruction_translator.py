import re
from instruction_semantics import get_semantics


class InstructionTranslator:
    """
    Helper-based HLASM instruction translator with register/offset resolution.

    Resolves examples:
      16(4,2) -> TXCUST when R2 -> CURRTX and CURRTX+16 -> TXCUST
      0(4,3)  -> ERRCODE when R3 -> ERRCODE
    """

    BRANCH_ALIASES = {
        "BE": "isEqual",
        "BZ": "isEqual",
        "BNE": "isNotEqual",
        "BNZ": "isNotEqual",
        "BH": "isHigh",
        "BL": "isLow",
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
                operands.append(current.strip())
                current = ""
            else:
                current += ch

        if current.strip():
            operands.append(current.strip())

        return operands

    # ------------------------------------------------------------
    # Operand resolution
    # ------------------------------------------------------------

    def _resolve_operand(self, operand):
        """
        Resolves:
          FIELD(4)     -> FIELD
          16(4,2)      -> field at base register R2 + offset 16
          0(4,3)       -> register R3 base symbol if no child offset
          8(,1)        -> parameter offset style, kept as base if unresolved
        """

        operand = operand.strip().upper()

        if self._is_literal(operand):
            return operand

        # FIELD(10)
        symbolic_len = re.match(r"^([A-Z0-9_#$@]+)\((\d+)\)$", operand)
        if symbolic_len:
            return symbolic_len.group(1)

        # 16(4,2)
        indexed = re.match(r"^(\d+)?\((\d+),(\d+)\)$", operand)
        if indexed:
            offset = int(indexed.group(1) or 0)
            base_reg = indexed.group(3)
            return self._resolve_register_offset(base_reg, offset)

        # 16(2)
        based = re.match(r"^(\d+)?\((\d+)\)$", operand)
        if based:
            offset = int(based.group(1) or 0)
            base_reg = based.group(2)
            return self._resolve_register_offset(base_reg, offset)

        # 8(,1)
        base_only = re.match(r"^(\d+)?\(,(\d+)\)$", operand)
        if base_only:
            offset = int(base_only.group(1) or 0)
            base_reg = base_only.group(2)
            return self._resolve_register_offset(base_reg, offset)

        return operand

    def _resolve_register_offset(self, reg, offset):
        base_symbol = self.register_map.get(str(reg))

        if not base_symbol:
            return str(offset)

        base_symbol = base_symbol.upper()

        # If offset is zero and base symbol is already a real field, use it.
        if offset == 0 and base_symbol in self.symbol_metadata:
            return base_symbol

        # If base has field offsets, resolve child field.
        offsets = self.field_offsets.get(base_symbol, {})
        field = offsets.get(str(offset))

        if field:
            return field.upper()

        # If no child found, return base symbol.
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
            or operand.startswith("=F'")
        )

    def _is_char_literal(self, operand):
        return operand.startswith("=C'") and operand.endswith("'")

    def _char_literal_value(self, operand):
        return operand[3:-1]

    def _is_packed_literal(self, operand):
        return operand.startswith("=P'") and operand.endswith("'")

    def _packed_literal_value(self, operand):
        return operand[3:-1]

    # ------------------------------------------------------------
    # Character/data movement
    # ------------------------------------------------------------

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

    # ------------------------------------------------------------
    # Character compare
    # ------------------------------------------------------------

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

    # ------------------------------------------------------------
    # Packed decimal
    # ------------------------------------------------------------

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
                f'        AsmRuntime.Packed.cp(ctx, "{left}", "{temp_name}", cc);'
            )

        right_field = self._resolve_operand(right)
        return f'AsmRuntime.Packed.cp(ctx, "{left}", "{right_field}", cc);'

    def _translate_pack(self, operands, clean):
        return f"// TODO PACK requires zoned/packed metadata: {clean}"

    def _translate_unpk(self, operands, clean):
        return f"// TODO UNPK requires packed/zoned metadata: {clean}"

    # ------------------------------------------------------------
    # Register and binary
    # ------------------------------------------------------------

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

    # ------------------------------------------------------------
    # Branching
    # ------------------------------------------------------------

    def _translate_b(self, operands, clean):
        target = operands[0] if operands else "UNKNOWN"
        return f"// branch target: {target}"

    def _translate_branch_alias(self, opcode, operands, clean):
        target = operands[0] if operands else "UNKNOWN"
        method = self.BRANCH_ALIASES[opcode]

        return (
            f"if (AsmRuntime.Branch.{method}(cc)) {{\n"
            f"            // branch to {target}\n"
            f"        }}"
        )

    def _translate_bct(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid BCT: {clean}"

        reg = operands[0]
        target = operands[1]

        return (
            f"if (AsmRuntime.Branch.bct(registers, {reg})) {{\n"
            f"            // branch to {target}\n"
            f"        }}"
        )

    def _translate_bctr(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid BCTR: {clean}"

        reg = operands[0]
        target = operands[1]

        return (
            f"if (AsmRuntime.Branch.bctr(registers, {reg})) {{\n"
            f"            // branch to {target}\n"
            f"        }}"
        )

    def _translate_br(self, operands, clean):
        return f"// branch register / return: {clean}"

    def _translate_balr(self, operands, clean):
        return f"// subroutine call via BALR: {clean}"

    def _translate_basr(self, operands, clean):
        return f"// subroutine call via BASR: {clean}"

    def _translate_bc(self, operands, clean):
        return f"// TODO BC requires condition mask decoding: {clean}"

    # ------------------------------------------------------------
    # Directives
    # ------------------------------------------------------------

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
        "MVC   0(4,3),=C'E001'",
        "MVC   TXCUST(4),=C'CUST'",
        "ZAP   TXFEE,TXAMT",
        "AP    TXAMT,TXFEE",
        "BE    VAL_OK",
        "BCT   5,LOOP",
    ]

    for sample in samples:
        print(sample)
        print("  ->", translator.translate_line(sample))