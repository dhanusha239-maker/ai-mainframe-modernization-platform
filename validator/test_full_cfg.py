from full_cfg_engine import CleanHLASMEngine

code = """
MAINDRV CSECT
L 15,=V(TXREAD)
L 15,=V(CUSTVAL)
BE TXREAD
B REJECT_PATH

TXREAD DS 0H
BNE CUSTVAL

CUSTVAL DS 0H
B AUDWRITE

REJECT_PATH DS 0H
B AUDWRITE

AUDWRITE DS 0H
"""

lines = code.split("\n")

engine = CleanHLASMEngine()
engine.parse(lines)

engine.print_all()