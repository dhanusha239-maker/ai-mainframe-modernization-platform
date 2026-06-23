"""
instruction_semantics.py

Financial-grade HLASM instruction semantics catalog.

Purpose:
- Do NOT guess Java translation directly.
- First classify each opcode by behavior type.
- Mark length-sensitive, sign-sensitive, register-sensitive,
  condition-code-sensitive, and manual-review instructions.

This catalog will be used later by:
- instruction_translator.py
- java_generator.py
- test/validation pipeline
"""


INSTRUCTION_SEMANTICS = {
    # ------------------------------------------------------------
    # Data movement / storage
    # ------------------------------------------------------------
    "MVC": {
        "name": "Move Character",
        "category": "character_move",
        "length_sensitive": True,
        "sign_sensitive": False,
        "condition_code": False,
        "reads_memory": True,
        "writes_memory": True,
        "java_helper": "AsmMemory.mvc",
        "translation_status": "needs_helper_runtime",
        "notes": "Copies exact operand length bytes/characters from source to target. Not simple assignment.",
    },
    "MVI": {
        "name": "Move Immediate",
        "category": "character_move",
        "length_sensitive": True,
        "sign_sensitive": False,
        "condition_code": False,
        "reads_memory": False,
        "writes_memory": True,
        "java_helper": "AsmMemory.mvi",
        "translation_status": "needs_helper_runtime",
        "notes": "Moves one immediate byte/character to target.",
    },
    "ST": {
        "name": "Store",
        "category": "register_store",
        "length_sensitive": True,
        "sign_sensitive": False,
        "condition_code": False,
        "reads_register": True,
        "writes_memory": True,
        "java_helper": "AsmRegister.storeFullword",
        "translation_status": "needs_helper_runtime",
    },
    "STH": {
        "name": "Store Halfword",
        "category": "register_store",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": False,
        "reads_register": True,
        "writes_memory": True,
        "java_helper": "AsmRegister.storeHalfword",
        "translation_status": "needs_helper_runtime",
    },
    "STC": {
        "name": "Store Character",
        "category": "register_store",
        "length_sensitive": True,
        "sign_sensitive": False,
        "condition_code": False,
        "reads_register": True,
        "writes_memory": True,
        "java_helper": "AsmRegister.storeCharacter",
        "translation_status": "needs_helper_runtime",
    },
    "STM": {
        "name": "Store Multiple",
        "category": "register_store",
        "length_sensitive": True,
        "register_sensitive": True,
        "condition_code": False,
        "java_helper": "AsmRegister.storeMultiple",
        "translation_status": "needs_helper_runtime",
    },

    # ------------------------------------------------------------
    # Load/register instructions
    # ------------------------------------------------------------
    "L": {
        "name": "Load",
        "category": "register_load",
        "length_sensitive": True,
        "sign_sensitive": False,
        "condition_code": False,
        "writes_register": True,
        "java_helper": "AsmRegister.loadFullword",
        "translation_status": "needs_helper_runtime",
    },
    "LA": {
        "name": "Load Address",
        "category": "address_load",
        "length_sensitive": False,
        "sign_sensitive": False,
        "condition_code": False,
        "writes_register": True,
        "java_helper": "AsmRegister.loadAddress",
        "translation_status": "needs_helper_runtime",
    },
    "LH": {
        "name": "Load Halfword",
        "category": "register_load",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": False,
        "writes_register": True,
        "java_helper": "AsmRegister.loadHalfwordSigned",
        "translation_status": "needs_helper_runtime",
        "notes": "Loads 2 bytes and sign-extends into target register.",
    },
    "LM": {
        "name": "Load Multiple",
        "category": "register_load",
        "length_sensitive": True,
        "register_sensitive": True,
        "condition_code": False,
        "java_helper": "AsmRegister.loadMultiple",
        "translation_status": "needs_helper_runtime",
    },
    "LTR": {
        "name": "Load and Test Register",
        "category": "register_test",
        "condition_code": True,
        "register_sensitive": True,
        "java_helper": "AsmCompare.ltr",
        "translation_status": "needs_helper_runtime",
    },

    # ------------------------------------------------------------
    # Character / logical comparison
    # ------------------------------------------------------------
    "CLC": {
        "name": "Compare Logical Characters",
        "category": "character_compare",
        "length_sensitive": True,
        "sign_sensitive": False,
        "condition_code": True,
        "reads_memory": True,
        "java_helper": "AsmCompare.clc",
        "translation_status": "needs_helper_runtime",
        "notes": "Compares exact byte/character length. Different from binary compare.",
    },
    "CLI": {
        "name": "Compare Logical Immediate",
        "category": "character_compare",
        "length_sensitive": True,
        "sign_sensitive": False,
        "condition_code": True,
        "reads_memory": True,
        "java_helper": "AsmCompare.cli",
        "translation_status": "needs_helper_runtime",
    },

    # ------------------------------------------------------------
    # Binary/integer comparison
    # ------------------------------------------------------------
    "C": {
        "name": "Compare",
        "category": "binary_compare",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": True,
        "java_helper": "AsmCompare.c",
        "translation_status": "needs_helper_runtime",
    },
    "CH": {
        "name": "Compare Halfword",
        "category": "binary_compare",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": True,
        "java_helper": "AsmCompare.ch",
        "translation_status": "needs_helper_runtime",
    },
    "CL": {
        "name": "Compare Logical",
        "category": "binary_logical_compare",
        "length_sensitive": True,
        "sign_sensitive": False,
        "condition_code": True,
        "java_helper": "AsmCompare.cl",
        "translation_status": "needs_helper_runtime",
        "notes": "Logical binary compare. Not same as CLC.",
    },
    "CR": {
        "name": "Compare Register",
        "category": "register_compare",
        "register_sensitive": True,
        "sign_sensitive": True,
        "condition_code": True,
        "java_helper": "AsmCompare.cr",
        "translation_status": "needs_helper_runtime",
    },

    # ------------------------------------------------------------
    # Packed decimal compare/arithmetic
    # ------------------------------------------------------------
    "CP": {
        "name": "Compare Decimal",
        "category": "packed_decimal_compare",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": True,
        "reads_memory": True,
        "java_helper": "AsmPacked.cp",
        "translation_status": "needs_helper_runtime",
    },
    "ZAP": {
        "name": "Zero and Add Packed",
        "category": "packed_decimal_move",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": True,
        "reads_memory": True,
        "writes_memory": True,
        "java_helper": "AsmPacked.zap",
        "translation_status": "needs_helper_runtime",
        "notes": "Clears target, then copies packed source respecting target length/precision/sign.",
    },
    "AP": {
        "name": "Add Packed",
        "category": "packed_decimal_arithmetic",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": True,
        "java_helper": "AsmPacked.ap",
        "translation_status": "needs_helper_runtime",
    },
    "SP": {
        "name": "Subtract Packed",
        "category": "packed_decimal_arithmetic",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": True,
        "java_helper": "AsmPacked.sp",
        "translation_status": "needs_helper_runtime",
    },
    "MP": {
        "name": "Multiply Packed",
        "category": "packed_decimal_arithmetic",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": True,
        "java_helper": "AsmPacked.mp",
        "translation_status": "needs_helper_runtime",
    },
    "DP": {
        "name": "Divide Packed",
        "category": "packed_decimal_arithmetic",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": True,
        "java_helper": "AsmPacked.dp",
        "translation_status": "needs_helper_runtime",
    },
    "PACK": {
        "name": "Pack",
        "category": "packed_decimal_conversion",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": False,
        "java_helper": "AsmPacked.pack",
        "translation_status": "needs_helper_runtime",
    },
    "UNPK": {
        "name": "Unpack",
        "category": "packed_decimal_conversion",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": False,
        "java_helper": "AsmPacked.unpk",
        "translation_status": "needs_helper_runtime",
    },

    # ------------------------------------------------------------
    # Binary arithmetic
    # ------------------------------------------------------------
    "A": {"name": "Add", "category": "binary_arithmetic", "sign_sensitive": True, "condition_code": True, "java_helper": "AsmBinary.a", "translation_status": "needs_helper_runtime"},
    "AH": {"name": "Add Halfword", "category": "binary_arithmetic", "length_sensitive": True, "sign_sensitive": True, "condition_code": True, "java_helper": "AsmBinary.ah", "translation_status": "needs_helper_runtime"},
    "AR": {"name": "Add Register", "category": "register_arithmetic", "register_sensitive": True, "sign_sensitive": True, "condition_code": True, "java_helper": "AsmBinary.ar", "translation_status": "needs_helper_runtime"},
    "S": {"name": "Subtract", "category": "binary_arithmetic", "sign_sensitive": True, "condition_code": True, "java_helper": "AsmBinary.s", "translation_status": "needs_helper_runtime"},
    "SH": {"name": "Subtract Halfword", "category": "binary_arithmetic", "length_sensitive": True, "sign_sensitive": True, "condition_code": True, "java_helper": "AsmBinary.sh", "translation_status": "needs_helper_runtime"},
    "SR": {"name": "Subtract Register", "category": "register_arithmetic", "register_sensitive": True, "sign_sensitive": True, "condition_code": True, "java_helper": "AsmBinary.sr", "translation_status": "needs_helper_runtime"},
    "M": {"name": "Multiply", "category": "binary_arithmetic", "sign_sensitive": True, "condition_code": True, "java_helper": "AsmBinary.m", "translation_status": "needs_helper_runtime"},

    # ------------------------------------------------------------
    # Branching/control flow
    # ------------------------------------------------------------
    "B": {"name": "Branch", "category": "control_flow", "condition_code": False, "java_helper": "AsmBranch.b", "translation_status": "control_flow"},
    "BC": {"name": "Branch on Condition", "category": "control_flow", "condition_code": True, "java_helper": "AsmBranch.bc", "translation_status": "control_flow"},
    "BR": {"name": "Branch Register", "category": "control_flow", "register_sensitive": True, "java_helper": "AsmBranch.br", "translation_status": "control_flow"},
    "BALR": {"name": "Branch and Link Register", "category": "call_control", "register_sensitive": True, "java_helper": "AsmBranch.balr", "translation_status": "control_flow"},
    "BASR": {"name": "Branch and Save Register", "category": "call_control", "register_sensitive": True, "java_helper": "AsmBranch.basr", "translation_status": "control_flow"},
    "BCT": {
        "name": "Branch on Count",
        "category": "loop_control",
        "register_sensitive": True,
        "condition_code": False,
        "java_helper": "AsmBranch.bct",
        "translation_status": "control_flow",
        "notes": "Decrements register first; branches if result is non-zero.",
    },
    "BCTR": {
        "name": "Branch on Count Register",
        "category": "loop_control",
        "register_sensitive": True,
        "condition_code": False,
        "java_helper": "AsmBranch.bctr",
        "translation_status": "control_flow",
        "notes": "Decrements register first; branches if result is non-zero.",
    },

    # ------------------------------------------------------------
    # Logical operations
    # ------------------------------------------------------------
    "XR": {"name": "Exclusive OR Register", "category": "logical_register", "register_sensitive": True, "condition_code": True, "java_helper": "AsmLogical.xr", "translation_status": "needs_helper_runtime"},
    "XC": {"name": "Exclusive OR Character", "category": "logical_character", "length_sensitive": True, "condition_code": True, "java_helper": "AsmLogical.xc", "translation_status": "needs_helper_runtime"},
    "N": {"name": "And", "category": "logical", "condition_code": True, "java_helper": "AsmLogical.n", "translation_status": "needs_helper_runtime"},
    "NI": {"name": "And Immediate", "category": "logical", "condition_code": True, "java_helper": "AsmLogical.ni", "translation_status": "needs_helper_runtime"},
    "NR": {"name": "And Register", "category": "logical_register", "register_sensitive": True, "condition_code": True, "java_helper": "AsmLogical.nr", "translation_status": "needs_helper_runtime"},
    "O": {"name": "Or", "category": "logical", "condition_code": True, "java_helper": "AsmLogical.o", "translation_status": "needs_helper_runtime"},
    "OI": {"name": "Or Immediate", "category": "logical", "condition_code": True, "java_helper": "AsmLogical.oi", "translation_status": "needs_helper_runtime"},
    "OR": {"name": "Or Register", "category": "logical_register", "register_sensitive": True, "condition_code": True, "java_helper": "AsmLogical.or_", "translation_status": "needs_helper_runtime"},
    "TM": {"name": "Test Under Mask", "category": "logical_test", "condition_code": True, "java_helper": "AsmLogical.tm", "translation_status": "needs_helper_runtime"},

    # ------------------------------------------------------------
    # Conversion/editing
    # ------------------------------------------------------------
    "CVB": {"name": "Convert to Binary", "category": "conversion", "sign_sensitive": True, "condition_code": False, "java_helper": "AsmConvert.cvb", "translation_status": "needs_helper_runtime"},
    "CVD": {"name": "Convert to Decimal", "category": "conversion", "sign_sensitive": True, "condition_code": False, "java_helper": "AsmConvert.cvd", "translation_status": "needs_helper_runtime"},
    "ED": {"name": "Edit", "category": "decimal_formatting", "length_sensitive": True, "sign_sensitive": True, "condition_code": True, "java_helper": "AsmEdit.ed", "translation_status": "needs_helper_runtime"},
    "TR": {"name": "Translate", "category": "character_translation", "length_sensitive": True, "condition_code": False, "java_helper": "AsmMemory.tr", "translation_status": "needs_helper_runtime"},

    # ------------------------------------------------------------
    # Directives / declarations
    # ------------------------------------------------------------
    "CSECT": {"name": "Control Section", "category": "assembler_directive", "translation_status": "data_declaration"},
    "DSECT": {"name": "Dummy Section", "category": "assembler_directive", "translation_status": "data_declaration"},
    "DS": {"name": "Define Storage", "category": "data_declaration", "translation_status": "data_declaration"},
    "DC": {"name": "Define Constant", "category": "data_declaration", "translation_status": "data_declaration"},
    "EQU": {"name": "Equate", "category": "assembler_directive", "translation_status": "data_declaration"},
    "USING": {"name": "Using", "category": "assembler_directive", "translation_status": "addressing_directive"},
    "DROP": {"name": "Drop", "category": "assembler_directive", "translation_status": "addressing_directive"},
}


def get_semantics(opcode: str) -> dict:
    return INSTRUCTION_SEMANTICS.get(opcode.upper(), {
        "name": opcode.upper(),
        "category": "unknown",
        "translation_status": "manual_review",
        "notes": "Opcode not yet in semantics catalog.",
    })


def print_semantics_report():
    print("HLASM INSTRUCTION SEMANTICS CATALOG")
    print("=" * 70)

    for opcode in sorted(INSTRUCTION_SEMANTICS):
        item = INSTRUCTION_SEMANTICS[opcode]
        print(f"{opcode:<6} {item.get('category'):<28} {item.get('translation_status')}")


if __name__ == "__main__":
    print_semantics_report()