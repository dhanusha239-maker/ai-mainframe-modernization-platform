"""
instruction_semantics_updated_v3.py

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
    "LR": {
        "name": "Load Register",
        "category": "register_load",
        "condition_code": False,
        "register_sensitive": True,
        "java_helper": "AsmRegister.lr",
        "translation_status": "needs_helper_runtime",
        "notes": "Copies the second register to the first; condition code is unchanged.",
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


# ------------------------------------------------------------
# Additional global semantics added for reusable translation.
# These are intentionally generic and not tied to any module/file name.
# ------------------------------------------------------------
INSTRUCTION_SEMANTICS.update({
    "SRP": {
        "name": "Shift and Round Packed",
        "category": "packed_decimal_arithmetic",
        "length_sensitive": True,
        "sign_sensitive": True,
        "condition_code": True,
        "reads_memory": True,
        "writes_memory": True,
        "java_helper": "AsmPacked.srp",
        "translation_status": "needs_helper_runtime",
        "notes": "Shifts packed decimal by decimal positions and rounds using the third operand.",
    },
    "TRT": {
        "name": "Translate and Test",
        "category": "character_translation",
        "length_sensitive": True,
        "condition_code": True,
        "register_sensitive": True,
        "java_helper": "AsmMemory.trt",
        "translation_status": "needs_helper_runtime",
        "notes": "Scans operand 1 using table operand 2. Sets CC and updates R1/R2-style scan registers in real HLASM.",
    },
    "OPEN": {"name": "Open", "category": "io_macro", "condition_code": True, "java_helper": "AsmIO.open", "translation_status": "needs_helper_runtime"},
    "GET": {"name": "Get", "category": "io_macro", "condition_code": True, "java_helper": "AsmIO.get", "translation_status": "needs_helper_runtime"},
    "PUT": {"name": "Put", "category": "io_macro", "condition_code": True, "java_helper": "AsmIO.put", "translation_status": "needs_helper_runtime"},
    "CLOSE": {"name": "Close", "category": "io_macro", "condition_code": True, "java_helper": "AsmIO.close", "translation_status": "needs_helper_runtime"},
    "SAVE": {"name": "Save Registers", "category": "program_macro", "register_sensitive": True, "java_helper": "AsmProgram.save", "translation_status": "needs_helper_runtime"},
    "RETURN": {"name": "Return", "category": "program_macro", "register_sensitive": True, "java_helper": "AsmProgram.returnCode", "translation_status": "needs_helper_runtime"},
    "PR": {"name": "Program Return", "category": "control_flow", "register_sensitive": True, "java_helper": "AsmProgram.pr", "translation_status": "control_flow"},
})


# ---------------------------------------------------------------------------
# v3 supplemental catalog for the user's attached global migration list.
#
# Important design rule:
# - An opcode being present here means the translator recognizes it and will not
#   treat it as an unknown instruction.
# - It does NOT mean we blindly emit Java. Instructions with tricky binary,
#   condition-code, pair-register, PER/AR-mode, branch-relative, or edit semantics
#   remain protected TODOs until their helper is validated against IBM PoP tests.
# ---------------------------------------------------------------------------
ATTACHED_OPCODE_LIST = [
    "A", "AFI", "AG", "AGF", "AGFI", "AGRK", "AGSI", "AH", "AP", "AR", "ASI", "AY",
    "BAKR", "BAS", "BASR", "BC", "BCR", "BCT", "BCTR", "BRAS", "BRASL", "BRC", "BRCL", "BRCT",
    "CGRB", "CLC", "CLI", "CH", "CP", "CR", "C", "CRB", "CVB", "CVD",
    "D", "DP", "DR",
    "ED", "EDMK", "EX", "EXRL",
    "IC", "ICM",
    "L", "LA", "LAA", "LARL", "LAY", "LB", "LBH", "LCR", "LG", "LH",
    "LM", "LNR", "LOC", "LLGTR", "LLGT", "LPR", "LR", "LRL", "LTGR", "LTR", "LY",
    "M", "MFY", "MG", "MGH", "MGRK", "MH", "MHI", "MHY",
    "MP", "MR", "MS", "MSR", "MVC", "MVCL", "MVI", "MVN", "MVZ",
    "N", "NI", "NR",
    "O", "OC", "OI", "OR",
    "PACK",
    "S", "SLA", "SLDA", "SLDL", "SLL", "SPM", "SR", "SRA", "SRDA", "SRDL", "SRL", "SRP", "SRST",
    "ST", "STC", "STH", "STM", "STOC", "STY", "SH", "SP", "SY",
    "TM", "TP", "TR", "TRT",
    "UNPK",
    "X", "XC", "XI", "XR",
    "ZAP",
]

SUPPORTED_AUTOTRANSLATE_HINTS = {
    "MVC", "MVI", "CLC", "CLI", "ZAP", "AP", "SP", "MP", "DP", "CP", "PACK", "UNPK", "SRP",
    "XR", "SR", "AR", "LTR", "LR", "LA", "A", "C", "CR", "TR", "TRT", "OI", "XI", "NI",
    "OPEN", "GET", "PUT", "CLOSE", "SAVE", "RETURN", "B", "BCT", "BCTR", "BR", "BALR", "BASR",
    "CSECT", "DSECT", "DS", "DC", "EQU", "USING", "DROP",
}

SUPPLEMENTAL_INSTRUCTION_SEMANTICS = {
    # Binary arithmetic - memory/immediate/register variants. Protected because exact overflow/CC behavior matters.
    "AFI": {"name": "Add Immediate", "category": "binary_arithmetic_immediate", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.addImmediateChecked", "notes": "Exact overflow and condition-code behavior must be validated against z/Architecture PoP."},
    "AG": {"name": "Add 64-bit", "category": "binary_arithmetic_64", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.ag"},
    "AGF": {"name": "Add 64-bit from 32-bit", "category": "binary_arithmetic_64", "condition_code": True, "register_sensitive": True, "sign_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.agf"},
    "AGFI": {"name": "Add 64-bit Immediate", "category": "binary_arithmetic_64_immediate", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.agfi"},
    "AGRK": {"name": "Add Register 64-bit Three Operand", "category": "binary_arithmetic_64_register", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.agrk"},
    "AGSI": {"name": "Add 64-bit Storage Immediate", "category": "binary_arithmetic_storage_immediate", "condition_code": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.agsi"},
    "ASI": {"name": "Add Storage Immediate", "category": "binary_arithmetic_storage_immediate", "condition_code": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.asi"},
    "AY": {"name": "Add with Long Displacement", "category": "binary_arithmetic", "condition_code": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.ay"},
    "M": {"name": "Multiply", "category": "binary_multiply", "condition_code": False, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.m", "notes": "Uses register-pair result semantics; do not lower to simple Java multiply without validation."},
    "MFY": {"name": "Multiply with Long Displacement", "category": "binary_multiply", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.mfy"},
    "MG": {"name": "Multiply 64-bit", "category": "binary_multiply_64", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.mg"},
    "MGH": {"name": "Multiply 64-bit by Halfword", "category": "binary_multiply_64", "register_sensitive": True, "sign_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.mgh"},
    "MGRK": {"name": "Multiply 64-bit Three Operand", "category": "binary_multiply_64_register", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.mgrk"},
    "MH": {"name": "Multiply Halfword", "category": "binary_multiply", "sign_sensitive": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.mh"},
    "MHI": {"name": "Multiply Halfword Immediate", "category": "binary_multiply_immediate", "sign_sensitive": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.mhi"},
    "MHY": {"name": "Multiply Halfword Long Displacement", "category": "binary_multiply", "sign_sensitive": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.mhy"},
    "MR": {"name": "Multiply Register", "category": "register_multiply", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.mr", "notes": "Register-pair result semantics."},
    "MS": {"name": "Multiply Single", "category": "binary_multiply", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.ms"},
    "MSR": {"name": "Multiply Single Register", "category": "register_multiply", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.msr"},
    "D": {"name": "Divide", "category": "binary_divide", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.d", "notes": "Register-pair quotient/remainder semantics."},
    "DR": {"name": "Divide Register", "category": "register_divide", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.dr", "notes": "Register-pair quotient/remainder semantics."},

    # Branch/control variants.
    "BAKR": {"name": "Branch and Stack", "category": "control_flow_linkage", "register_sensitive": True, "translation_status": "protected_control_flow", "java_helper": "AsmRuntime.Branch.bakr"},
    "BAS": {"name": "Branch and Save", "category": "control_flow_linkage", "register_sensitive": True, "translation_status": "protected_control_flow", "java_helper": "AsmRuntime.Branch.bas"},
    "BCR": {"name": "Branch on Condition Register", "category": "control_flow", "condition_code": True, "register_sensitive": True, "translation_status": "protected_control_flow", "java_helper": "AsmRuntime.Branch.bcr"},
    "BRAS": {"name": "Branch Relative and Save", "category": "relative_branch_linkage", "register_sensitive": True, "translation_status": "protected_control_flow", "java_helper": "AsmRuntime.Branch.bras"},
    "BRASL": {"name": "Branch Relative and Save Long", "category": "relative_branch_linkage", "register_sensitive": True, "translation_status": "protected_control_flow", "java_helper": "AsmRuntime.Branch.brasl"},
    "BRC": {"name": "Branch Relative on Condition", "category": "relative_branch", "condition_code": True, "translation_status": "protected_control_flow", "java_helper": "AsmRuntime.Branch.brc"},
    "BRCL": {"name": "Branch Relative on Condition Long", "category": "relative_branch", "condition_code": True, "translation_status": "protected_control_flow", "java_helper": "AsmRuntime.Branch.brcl"},
    "BRCT": {"name": "Branch Relative on Count", "category": "loop_control", "register_sensitive": True, "translation_status": "protected_control_flow", "java_helper": "AsmRuntime.Branch.brct"},

    # Compare variants.
    "CGRB": {"name": "Compare 64-bit and Branch Relative", "category": "compare_and_branch", "condition_code": True, "register_sensitive": True, "translation_status": "protected_control_flow", "java_helper": "AsmRuntime.Branch.cgrb"},
    "CRB": {"name": "Compare Register and Branch Relative", "category": "compare_and_branch", "condition_code": True, "register_sensitive": True, "translation_status": "protected_control_flow", "java_helper": "AsmRuntime.Branch.crb"},

    # Conversion/edit/execute.
    "EDMK": {"name": "Edit and Mark", "category": "decimal_formatting", "length_sensitive": True, "sign_sensitive": True, "condition_code": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Edit.edmk", "notes": "Updates R1 mark position; helper must model edit patterns exactly."},
    "EX": {"name": "Execute", "category": "dynamic_instruction", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Execute.ex", "notes": "Dynamically modifies/executes target instruction; requires IR-level support."},
    "EXRL": {"name": "Execute Relative Long", "category": "dynamic_instruction", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Execute.exrl", "notes": "Dynamic instruction execution; requires IR-level support."},

    # Insert/load variants.
    "IC": {"name": "Insert Character", "category": "insert_register", "length_sensitive": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.ic"},
    "ICM": {"name": "Insert Characters under Mask", "category": "insert_register", "length_sensitive": True, "register_sensitive": True, "condition_code": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.icm"},
    "LAA": {"name": "Load and Add", "category": "atomic_storage", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Atomic.laa"},
    "LARL": {"name": "Load Address Relative Long", "category": "address_load", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Address.larl"},
    "LAY": {"name": "Load Address Long Displacement", "category": "address_load", "register_sensitive": True, "translation_status": "needs_helper_runtime", "java_helper": "AsmRuntime.Address.lay"},
    "LB": {"name": "Load Byte", "category": "register_load", "length_sensitive": True, "sign_sensitive": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.lb"},
    "LBH": {"name": "Load Byte High", "category": "register_load", "length_sensitive": True, "sign_sensitive": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.lbh"},
    "LCR": {"name": "Load Complement Register", "category": "register_arithmetic", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.lcr"},
    "LG": {"name": "Load 64-bit", "category": "register_load_64", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.lg"},
    "LNR": {"name": "Load Negative Register", "category": "register_arithmetic", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.lnr"},
    "LOC": {"name": "Load on Condition", "category": "conditional_load", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.loc"},
    "LLGTR": {"name": "Load Logical 32 to 64 and Test", "category": "register_load_64", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.llgtr"},
    "LLGT": {"name": "Load Logical Thirty One Bits", "category": "register_load", "condition_code": False, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.llgt"},
    "LPR": {"name": "Load Positive Register", "category": "register_arithmetic", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.lpr"},
    "LRL": {"name": "Load Relative Long", "category": "register_load", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.lrl"},
    "LTGR": {"name": "Load and Test 64-bit Register", "category": "register_test_64", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.ltgr"},
    "LY": {"name": "Load Long Displacement", "category": "register_load", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.ly"},

    # Character/logical moves and logical operations.
    "MVCL": {"name": "Move Long", "category": "character_move_long", "length_sensitive": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Memory.mvcl"},
    "MVN": {"name": "Move Numerics", "category": "character_move_nibble", "length_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Memory.mvn"},
    "MVZ": {"name": "Move Zones", "category": "character_move_nibble", "length_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Memory.mvz"},
    "N": {"name": "And", "category": "logical_memory", "condition_code": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Logical.n"},
    "OC": {"name": "Or Character", "category": "logical_character", "length_sensitive": True, "condition_code": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Memory.oc"},
    "X": {"name": "Exclusive OR", "category": "logical_memory", "condition_code": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Logical.x"},

    # Shift/search/store variants.
    "SLA": {"name": "Shift Left Single", "category": "shift", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Shift.sla"},
    "SLDA": {"name": "Shift Left Double", "category": "shift_pair", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Shift.slda"},
    "SLDL": {"name": "Shift Left Double Logical", "category": "shift_pair", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Shift.sldl"},
    "SLL": {"name": "Shift Left Logical", "category": "shift", "condition_code": False, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Shift.sll"},
    "SPM": {"name": "Set Program Mask", "category": "program_mask", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Program.spm"},
    "SRA": {"name": "Shift Right Single", "category": "shift", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Shift.sra"},
    "SRDA": {"name": "Shift Right Double", "category": "shift_pair", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Shift.srda"},
    "SRDL": {"name": "Shift Right Double Logical", "category": "shift_pair", "condition_code": False, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Shift.srdl"},
    "SRL": {"name": "Shift Right Logical", "category": "shift", "condition_code": False, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Shift.srl"},
    "SRST": {"name": "Search String", "category": "string_search", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Memory.srst"},
    "STOC": {"name": "Store on Condition", "category": "conditional_store", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.stoc"},
    "STY": {"name": "Store Long Displacement", "category": "register_store", "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.sty"},
    "SY": {"name": "Subtract Long Displacement", "category": "binary_arithmetic", "condition_code": True, "register_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Register.sy"},
    "TP": {"name": "Test Decimal", "category": "packed_decimal_test", "condition_code": True, "sign_sensitive": True, "length_sensitive": True, "translation_status": "protected_helper", "java_helper": "AsmRuntime.Packed.tp"},
}

for _opcode in ATTACHED_OPCODE_LIST:
    if _opcode not in INSTRUCTION_SEMANTICS and _opcode in SUPPLEMENTAL_INSTRUCTION_SEMANTICS:
        INSTRUCTION_SEMANTICS[_opcode] = SUPPLEMENTAL_INSTRUCTION_SEMANTICS[_opcode]
    elif _opcode not in INSTRUCTION_SEMANTICS:
        INSTRUCTION_SEMANTICS[_opcode] = {
            "name": _opcode,
            "category": "known_from_global_instruction_list",
            "translation_status": "protected_helper",
            "java_helper": f"AsmRuntime.Unsupported.{_opcode.lower()}",
            "notes": "Known opcode from the global migration instruction list, but helper is intentionally protected until validated.",
        }

for _opcode, _data in SUPPLEMENTAL_INSTRUCTION_SEMANTICS.items():
    INSTRUCTION_SEMANTICS[_opcode] = {**INSTRUCTION_SEMANTICS.get(_opcode, {}), **_data}

for _opcode in SUPPORTED_AUTOTRANSLATE_HINTS:
    if _opcode in INSTRUCTION_SEMANTICS:
        INSTRUCTION_SEMANTICS[_opcode]["auto_translate_candidate"] = True


def instruction_coverage_summary():
    """Return opcode coverage for the attached global migration list."""
    rows = []
    for opcode in ATTACHED_OPCODE_LIST:
        sem = INSTRUCTION_SEMANTICS.get(opcode, {})
        rows.append({
            "opcode": opcode,
            "category": sem.get("category", "unknown"),
            "translation_status": sem.get("translation_status", "unknown"),
            "java_helper": sem.get("java_helper", ""),
            "auto_translate_candidate": bool(sem.get("auto_translate_candidate", False)),
        })
    return rows

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