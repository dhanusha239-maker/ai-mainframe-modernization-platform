import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_DIR = PROJECT_ROOT / "validator"

sys.path.insert(0, str(VALIDATOR_DIR))

from cfg_builder import CFGBuilder


def main():
    builder = CFGBuilder(PROJECT_ROOT / "HLASM")

    builder.scan_repository()

    print("\n" + "=" * 60)
    print("CFG BUILDER TEST")
    print("=" * 60)

    builder.print_report()

    print("\nCFG Builder test completed successfully.")


if __name__ == "__main__":
    main()