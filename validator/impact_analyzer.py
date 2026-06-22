import json
from collections import defaultdict


class ImpactAnalyzer:
    """
    Reads analysis_report.json from PDGBuilder and answers:

    - If a symbol changes, which modules are affected?
    - Who writes this symbol?
    - Who reads this symbol?
    - What warnings exist?
    """

    def __init__(self, report_path="analysis_report.json"):
        self.report_path = report_path
        self.report = self._load_report()

    def _load_report(self):
        with open(self.report_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def analyze_symbol(self, symbol):
        symbol = symbol.upper()

        writers = self.report.get("symbol_writers", {}).get(symbol, [])
        readers = self.report.get("symbol_readers", {}).get(symbol, [])

        impacted = []

        for module in writers + readers:
            if module not in impacted:
                impacted.append(module)

        return {
            "symbol": symbol,
            "written_by": writers,
            "read_by": readers,
            "impacted_modules": impacted,
        }

    def print_symbol_impact(self, symbol):
        result = self.analyze_symbol(symbol)

        print("\nIMPACT ANALYSIS")
        print("-" * 60)
        print(f"Symbol: {result['symbol']}")

        print("\nWritten by:")
        if result["written_by"]:
            for module in result["written_by"]:
                print(f"  - {module}")
        else:
            print("  None")

        print("\nRead by:")
        if result["read_by"]:
            for module in result["read_by"]:
                print(f"  - {module}")
        else:
            print("  None")

        print("\nImpacted modules:")
        if result["impacted_modules"]:
            for module in result["impacted_modules"]:
                print(f"  - {module}")
        else:
            print("  None")

    def print_all_impacts(self):
        symbols = self.report.get("symbols", {})

        print("\nFULL IMPACT ANALYSIS REPORT")
        print("=" * 70)

        for symbol in symbols:
            result = self.analyze_symbol(symbol)

            if not result["impacted_modules"]:
                continue

            print(f"\n{symbol}:")
            print(f"  Written by -> {', '.join(result['written_by']) if result['written_by'] else 'None'}")
            print(f"  Read by    -> {', '.join(result['read_by']) if result['read_by'] else 'None'}")
            print(f"  Impacted   -> {', '.join(result['impacted_modules'])}")

    def print_warnings(self):
        warnings = self.report.get("warnings", [])

        print("\nANALYSIS WARNINGS")
        print("-" * 60)

        if not warnings:
            print("None")
            return

        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    analyzer = ImpactAnalyzer("analysis_report.json")

    analyzer.print_all_impacts()
    analyzer.print_warnings()

    # Example specific checks
    analyzer.print_symbol_impact("ERRCODE")
    analyzer.print_symbol_impact("TXAMT")
    analyzer.print_symbol_impact("AUTHSTAT")