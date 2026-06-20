from cfg_builder import HLASMGraphBuilder

code = """
MAINDRV CSECT
L 15,=V(TXREAD)
L 15,=V(CUSTVAL)

TXREAD CSECT
BASR 14,15

CUSTVAL CSECT
BALR 14,15
"""

lines = code.split("\n")

builder = HLASMGraphBuilder()
graph = builder.parse(lines)

builder.print_graph()

missing = builder.detect_missing()
print("\nMISSING MODULES:", missing)