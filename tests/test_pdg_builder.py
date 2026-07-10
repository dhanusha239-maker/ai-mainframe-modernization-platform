import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_DIR = PROJECT_ROOT / "validator"

sys.path.insert(0, str(VALIDATOR_DIR))

from pdg_builder import PDGBuilder


def main():
    builder = PDGBuilder(PROJECT_ROOT / "HLASM")

    builder.scan_repository()

    print("\n" + "=" * 60)
    print("PDG BUILDER TEST")
    print("=" * 60)

    builder.print_report()

    output_file = PROJECT_ROOT / "analysis_report.json"
    builder.export_json(output_file)

    print(f"\nSaved JSON report to {output_file}")


if __name__ == "__main__":
    main()