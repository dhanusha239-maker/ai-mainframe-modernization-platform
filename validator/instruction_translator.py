import re


class InstructionTranslator:
    """
    HLASM instruction translator foundation.

    Goal:
    Convert common HLASM instructions into Java candidate statements.

    This version supports a broad opcode list and safely marks unsupported
    or complex instructions with TODO comments instead of failing.
    """

    SUPPORTED_OPCODES = {
        "A", "AH", "AP", "AR",
        "B", "BALR", "BASR", "BC", "BCT", "BCTR", "BR",
        "C", "CH", "CLC", "CLI", "CP", "CR",
        "CSECT", "CVB", "CVD",
        "DC", "DP", "DROP", "DS", "DSECT",
        "ED", "EQU",
        "IC", "ICM",
        "L", "LA", "LH", "LM", "LTR",
        "M", "MP",
        "MVC", "MVI",
        "N", "NI", "NR",
        "O", "OI", "OR",
        "PACK",
        "S", "SH", "SP", "SR",
        "ST", "STC", "STH", "STM",
        "TM", "TR",
        "UNPK", "USING",
        "XC", "XR",
        "ZAP",
    }

    def translate_line(self, line):
        clean = line.strip()

        if not clean or clean.startswith("*"):
            return None

        opcode, operands = self._parse_instruction(clean)

        if not opcode:
            return None

        opcode = opcode.upper()

        if opcode not in self.SUPPORTED_OPCODES:
            return f"// TODO unsupported opcode: {clean}"

        handler = getattr(self, f"_translate_{opcode.lower()}", None)

        if handler:
            return handler(operands, clean)

        return self._generic_todo(opcode, operands, clean)

    def _parse_instruction(self, line):
        parts = line.split(None, 2)

        if not parts:
            return None, []

        # Format: OPCODE OPERANDS
        if parts[0].upper() in self.SUPPORTED_OPCODES:
            opcode = parts[0].upper()
            operand_text = parts[1] if len(parts) > 1 else ""
            return opcode, self._split_operands(operand_text)

        # Format: LABEL OPCODE OPERANDS
        if len(parts) >= 2 and parts[1].upper() in self.SUPPORTED_OPCODES:
            opcode = parts[1].upper()
            operand_text = parts[2] if len(parts) > 2 else ""
            return opcode, self._split_operands(operand_text)

        return parts[0].upper(), []

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

    def _java_field(self, operand):
        """
        Convert resolved field/symbol name into ExecutionContext access.
        """
        operand = operand.strip()

        if operand.startswith("=C'") and operand.endswith("'"):
            return '"' + operand[3:-1] + '"'

        if operand.startswith("C'") and operand.endswith("'"):
            return '"' + operand[2:-1] + '"'

        if operand.startswith("=P'") and operand.endswith("'"):
            return 'new java.math.BigDecimal("' + operand[3:-1] + '")'

        if operand.startswith("=F'") and operand.endswith("'"):
            return operand[3:-1]

        if operand.isdigit():
            return operand

        return f'ctx.get("{operand}")'

    def _ctx_string(self, operand):
        return f'ctx.getString("{operand}")'

    def _ctx_decimal(self, operand):
        return f'ctx.getDecimal("{operand}")'

    def _ctx_set(self, operand, value):
        return f'ctx.set("{operand}", {value});'

    def _generic_todo(self, opcode, operands, clean):
        return f"// TODO translate {opcode}: {clean}"

    # ------------------------------------------------------------
    # Data movement
    # ------------------------------------------------------------

    def _translate_mvc(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid MVC: {clean}"

        target = operands[0].split("(")[0]
        source = operands[1]

        return self._ctx_set(target, self._java_field(source))

    def _translate_mvi(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid MVI: {clean}"

        target = operands[0].split("(")[0]
        value = self._java_field(operands[1])

        return self._ctx_set(target, value)

    def _translate_zap(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid ZAP: {clean}"

        target = operands[0].split("(")[0]
        source = operands[1]

        return f'ctx.setDecimal("{target}", {self._ctx_decimal(source)});'

    def _translate_pack(self, operands, clean):
        return f"// PACK detected: use packed_decimal.py / BigDecimal mapping for {clean}"

    def _translate_unpk(self, operands, clean):
        return f"// UNPK detected: unpack packed decimal value for {clean}"

    # ------------------------------------------------------------
    # Decimal arithmetic
    # ------------------------------------------------------------

    def _translate_ap(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid AP: {clean}"

        target = operands[0]
        source = operands[1]

        return (
            f'ctx.setDecimal("{target}", '
            f'{self._ctx_decimal(target)}.add({self._ctx_decimal(source)}));'
        )

    def _translate_sp(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid SP: {clean}"

        target = operands[0]
        source = operands[1]

        return (
            f'ctx.setDecimal("{target}", '
            f'{self._ctx_decimal(target)}.subtract({self._ctx_decimal(source)}));'
        )

    def _translate_mp(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid MP: {clean}"

        target = operands[0]
        source = operands[1]

        return (
            f'ctx.setDecimal("{target}", '
            f'{self._ctx_decimal(target)}.multiply({self._ctx_decimal(source)}));'
        )

    def _translate_dp(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid DP: {clean}"

        target = operands[0]
        source = operands[1]

        return (
            f'ctx.setDecimal("{target}", '
            f'{self._ctx_decimal(target)}.divide({self._ctx_decimal(source)}, '
            f'2, java.math.RoundingMode.HALF_UP));'
        )

    # ------------------------------------------------------------
    # Binary/integer arithmetic
    # ------------------------------------------------------------

    def _translate_a(self, operands, clean):
        return f"// Integer add detected: {clean}"

    def _translate_ah(self, operands, clean):
        return f"// Halfword add detected: {clean}"

    def _translate_ar(self, operands, clean):
        return f"// Register add detected: {clean}"

    def _translate_s(self, operands, clean):
        return f"// Integer subtract detected: {clean}"

    def _translate_sh(self, operands, clean):
        return f"// Halfword subtract detected: {clean}"

    def _translate_sr(self, operands, clean):
        if len(operands) >= 2 and operands[0] == operands[1]:
            return f"// {clean} -> clear register {operands[0]}"
        return f"// Register subtract detected: {clean}"

    def _translate_m(self, operands, clean):
        return f"// Binary multiply detected: {clean}"

    # ------------------------------------------------------------
    # Compare instructions
    # ------------------------------------------------------------

    def _translate_clc(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid CLC: {clean}"

        left = operands[0].split("(")[0]
        right = operands[1]

        return f'// compare string: {self._ctx_string(left)} with {self._java_field(right)}'

    def _translate_cli(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid CLI: {clean}"

        left = operands[0].split("(")[0]
        right = self._java_field(operands[1])

        return f'// compare character/string: {self._ctx_string(left)} with {right}'

    def _translate_cp(self, operands, clean):
        if len(operands) < 2:
            return f"// TODO invalid CP: {clean}"

        left = operands[0]
        right = operands[1]

        return f'// compare decimal: {self._ctx_decimal(left)}.compareTo({self._ctx_decimal(right)})'

    def _translate_c(self, operands, clean):
        return f"// binary compare detected: {clean}"

    def _translate_ch(self, operands, clean):
        return f"// halfword compare detected: {clean}"

    def _translate_cr(self, operands, clean):
        return f"// register compare detected: {clean}"

    def _translate_ltr(self, operands, clean):
        return f"// test register and set condition code: {clean}"

    # ------------------------------------------------------------
    # Branching
    # ------------------------------------------------------------

    def _translate_b(self, operands, clean):
        target = operands[0] if operands else "UNKNOWN"
        return f"// unconditional branch to {target}"

    def _translate_bc(self, operands, clean):
        return f"// conditional branch: {clean}"

    def _translate_br(self, operands, clean):
        return f"// return/branch register: {clean}"

    def _translate_balr(self, operands, clean):
        return f"// subroutine call using BALR: {clean}"

    def _translate_basr(self, operands, clean):
        return f"// subroutine call using BASR: {clean}"

    def _translate_bct(self, operands, clean):
        return f"// branch on count: {clean}"

    def _translate_bctr(self, operands, clean):
        return f"// branch on count register: {clean}"

    # ------------------------------------------------------------
    # Load/store/register
    # ------------------------------------------------------------

    def _translate_l(self, operands, clean):
        return f"// load register/address: {clean}"

    def _translate_la(self, operands, clean):
        return f"// load address/immediate: {clean}"

    def _translate_lh(self, operands, clean):
        return f"// load halfword: {clean}"

    def _translate_lm(self, operands, clean):
        return f"// load multiple registers: {clean}"

    def _translate_st(self, operands, clean):
        return f"// store register: {clean}"

    def _translate_stc(self, operands, clean):
        return f"// store character: {clean}"

    def _translate_sth(self, operands, clean):
        return f"// store halfword: {clean}"

    def _translate_stm(self, operands, clean):
        return f"// store multiple registers: {clean}"

    def _translate_ic(self, operands, clean):
        return f"// insert character: {clean}"

    def _translate_icm(self, operands, clean):
        return f"// insert characters under mask: {clean}"

    # ------------------------------------------------------------
    # Logical operations
    # ------------------------------------------------------------

    def _translate_xr(self, operands, clean):
        if len(operands) >= 2 and operands[0] == operands[1]:
            return f"// {clean} -> clear register {operands[0]}"
        return f"// exclusive OR registers: {clean}"

    def _translate_xc(self, operands, clean):
        return f"// exclusive OR character fields: {clean}"

    def _translate_n(self, operands, clean):
        return f"// AND operation: {clean}"

    def _translate_ni(self, operands, clean):
        return f"// AND immediate: {clean}"

    def _translate_nr(self, operands, clean):
        return f"// AND registers: {clean}"

    def _translate_o(self, operands, clean):
        return f"// OR operation: {clean}"

    def _translate_oi(self, operands, clean):
        return f"// OR immediate: {clean}"

    def _translate_or(self, operands, clean):
        return f"// OR registers: {clean}"

    def _translate_tm(self, operands, clean):
        return f"// test under mask: {clean}"

    # ------------------------------------------------------------
    # Conversion/editing
    # ------------------------------------------------------------

    def _translate_cvb(self, operands, clean):
        return f"// convert decimal to binary: {clean}"

    def _translate_cvd(self, operands, clean):
        return f"// convert binary to decimal: {clean}"

    def _translate_ed(self, operands, clean):
        return f"// edit/format decimal field: {clean}"

    def _translate_tr(self, operands, clean):
        return f"// translate characters using table: {clean}"

    # ------------------------------------------------------------
    # Assembler directives
    # ------------------------------------------------------------

    def _translate_csect(self, operands, clean):
        return f"// CSECT directive: {clean}"

    def _translate_dsect(self, operands, clean):
        return f"// DSECT directive: {clean}"

    def _translate_ds(self, operands, clean):
        return f"// DS storage declaration: {clean}"

    def _translate_dc(self, operands, clean):
        return f"// DC constant declaration: {clean}"

    def _translate_equ(self, operands, clean):
        return f"// EQU symbol definition: {clean}"

    def _translate_using(self, operands, clean):
        return f"// USING base register directive: {clean}"

    def _translate_drop(self, operands, clean):
        return f"// DROP base register directive: {clean}"


if __name__ == "__main__":
    translator = InstructionTranslator()

    samples = [
        "MVC ERRCODE,=C'E001'",
        "CLC TXCUST,=C'CUST'",
        "CP TXAMT,TXLIMIT",
        "ZAP TXFEE,TXAMT",
        "AP TXAMT,TXFEE",
        "XR 15,15",
        "B FINAL_RETURN",
    ]

    for sample in samples:
        print(sample)
        print("  ->", translator.translate_line(sample))