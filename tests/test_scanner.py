import sys
from pathlib import Path

# Project structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_DIR = PROJECT_ROOT / "validator"

# Allow importing validator modules
sys.path.insert(0, str(VALIDATOR_DIR))

from asm_scanner import ASMScanner


def main():
    scanner = ASMScanner(PROJECT_ROOT / "HLASM")

    scanner.scan_repository()

    print("\n" + "=" * 60)
    print("ASM SCANNER TEST")
    print("=" * 60)

    scanner.print_report()

    print("\nScanner test completed successfully.")


if __name__ == "__main__":
    main()