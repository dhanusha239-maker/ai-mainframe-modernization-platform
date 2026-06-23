import re

from instruction_semantics import get_semantics


class InstructionTranslator:
    """
    Helper-based HLASM instruction translator.

    This translator does NOT directly guess business Java logic.
    It generates calls to AsmRuntime helpers.

    Example:
      MVC A(5),B
        -> AsmRuntime.Memory.mvc(ctx, "A", 5, "B");

      ZAP TXFEE,TXAMT
        -> AsmRuntime.Packed.zap(ctx, "TXFEE", "TXAMT", 7, 2, cc);
    """

    def __init__(self, symbol_metadata=None):
        self.symbol_metadata = symbol_metadata or {}

    def translate_line(self, line):
        clean = line.strip()

        if not clean or clean.startswith("*"):
            return None

        opcode, operands = self._parse_instruction(clean)

        if not opcode:
            return None

        opcode = opcode.upper()
        semantics = get_semantics(opcode)

        if semantics.get("translation_status") == "manual_review":
            return f"// TODO manual review required: {clean}"

        handler = getattr(self, f"_translate_{opcode.lower()}", None)

        if handler:
            return handler(operands, clean)

        helper = semantics.get("java_helper")
        return f"// TODO implement helper translation for {opcode}: {helper} // {clean}"

    # ------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------

    def _parse_instruction(self, line):
        parts = line.split(None, 2)

        if not parts:
            return None, []

        first = parts[0].upper()

        if get_semantics(first).get("translation_status") != "manual_review":
            opcode = first
            operand_text = parts[1] if len(parts) > 1 else ""
            return opcode, self._split_operands(operand_text)

        if len(parts) >= 2:
            second = parts[1].upper()
            if get_semantics(second).get("translation_status") != "manual_review":
                opcode = second
                operand_text = parts[2] if len(parts) > 2 else ""
                return opcode, self._split_operands(operand_text)

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

    def _base_field(self, operand):
        """
        FIELD(5) -> FIELD
        16(4,3) -> unresolved memory reference, keep original
        """
        operand = operand.strip()

        if re.match(r"^[A-Z0-9_#$@]+\(", operand, re.IGNORECASE):
            return operand.split("(", 1)[0].upper()

        return operand.upper()

    def _length_from_operand(self, operand, default=1):
        """
        FIELD(10) -> 10
        If no explicit length, use symbol metadata if available.
        """

        match = re.search(r"\((\d+)\)", operand)
        if match:
            return int(match.group(1))

        field = self._base_field(operand)
        meta = self.symbol_metadata.get(field, {})

        return meta.get("length", default)

    def _packed_digits(self, field):
        meta = self.symbol_metadata.get(field.upper(), {})
        return meta.get("digits", 15)

    def _packed_scale(self, field):
        meta = self.symbol_metadata.get(field.upper(), {})
        return meta.get("scale", 0)

    def _is_char_literal(self, operand):
        return operand.startswith("=C'") and operand.endswith("'")

    def _char_literal_value(self, operand):
        return operand[3:-1]

    def _is_packed_literal(self, operand):
        return operand.startswith("=P'") and operand.endswith("'")

    def _packed_literal_value(self, operand):
        return operand[3:-1]

    def _is_fullword_literal(self, operand):
        return operand.startswith("=F'") and operand.endswith("'")

    def _fullword_literal_value(self, operand):
        return operand[3:-1]

    # ------------------------------------------------------------
    # Character/data movement
    # ------------------------------------------------------------

    def _translate_mvc(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid MVC: {clean}"

        target = self._base_field(operands[0])
        length = self._length_from_operand(operands[0], default=1)
        source = operands[1]

        if self._is_char_literal(source):
            literal = self._char_literal_value(source)
            return (
                f'AsmRuntime.Memory.mvcLiteral(ctx, "{target}", '
                f'{length}, "{literal}");'
            )

        source_field = self._base_field(source)

        return (
            f'AsmRuntime.Memory.mvc(ctx, "{target}", '
            f'{length}, "{source_field}");'
        )

    def _translate_mvi(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid MVI: {clean}"

        target = self._base_field(operands[0])
        source = operands[1]

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

        left = self._base_field(operands[0])
        length = self._length_from_operand(operands[0], default=1)
        right = operands[1]

        if self._is_char_literal(right):
            literal = self._char_literal_value(right)
            return (
                f'AsmRuntime.Memory.clcLiteral(ctx, "{left}", '
                f'{length}, "{literal}", cc);'
            )

        right_field = self._base_field(right)

        return (
            f'AsmRuntime.Memory.clc(ctx, "{left}", '
            f'{length}, "{right_field}", cc);'
        )

    def _translate_cli(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid CLI: {clean}"

        left = self._base_field(operands[0])
        right = operands[1]

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

        target = self._base_field(operands[0])
        source = self._base_field(operands[1])

        digits = self._packed_digits(target)
        scale = self._packed_scale(target)

        return (
            f'AsmRuntime.Packed.zap(ctx, "{target}", "{source}", '
            f'{digits}, {scale}, cc);'
        )

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

        target = self._base_field(operands[0])
        source = self._base_field(operands[1])

        digits = self._packed_digits(target)
        scale = self._packed_scale(target)

        return (
            f'AsmRuntime.Packed.{op}(ctx, "{target}", "{source}", '
            f'{digits}, {scale}, cc);'
        )

    def _translate_cp(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid CP: {clean}"

        left = self._base_field(operands[0])
        right = operands[1]

        if self._is_packed_literal(right):
            literal = self._packed_literal_value(right)
            temp_name = f"{left}_LITERAL_COMPARE"

            return (
                f'ctx.setDecimal("{temp_name}", new java.math.BigDecimal("{literal}"));\n'
                f'        AsmRuntime.Packed.cp(ctx, "{left}", "{temp_name}", cc);'
            )

        right_field = self._base_field(right)

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
        return f"// TODO LH requires memory address resolution before exact helper call: {clean}"

    def _translate_l(self, operands, clean):
        return f"// TODO L requires memory/address resolution before exact helper call: {clean}"

    def _translate_la(self, operands, clean):
        return f"// TODO LA requires address/register model integration: {clean}"

    def _translate_lm(self, operands, clean):
        return f"// TODO LM requires parameter/register block resolution: {clean}"

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

    # ------------------------------------------------------------
    # Fallbacks for supported-but-not-yet-implemented helpers
    # ------------------------------------------------------------

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
            "ERRCODE": {"length": 4},
            "TXCUST": {"length": 10},
            "TXAMT": {"digits": 7, "scale": 2},
            "TXFEE": {"digits": 7, "scale": 2},
        }
    )

    samples = [
        "MVC ERRCODE,=C'E001'",
        "MVC TXCUST(4),=C'CUST'",
        "CLC TXCUST(4),=C'CUST'",
        "CLI TXSTAT,C'A'",
        "ZAP TXFEE,TXAMT",
        "AP TXAMT,TXFEE",
        "CP TXAMT,TXFEE",
        "XR 15,15",
        "BCT 5,LOOP",
    ]

    for sample in samples:
        print(sample)
        print("  ->", translator.translate_line(sample))