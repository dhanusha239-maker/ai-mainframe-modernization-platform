import json
import os
from datetime import datetime


class DocumentationGenerator:
    """
    Generates a high-level project analysis report from analysis_report.json.

    Output:
      docs/project_analysis_report.md

    This is different from behavior_reporter.py:
      - behavior_reporter.py = module-by-module technical behavior
      - documentation_generator.py = executive/project-level summary
    """

    def __init__(self, report_path="analysis_report.json"):
        self.report_path = report_path
        self.report = self._load_report()

    def _load_report(self):
        with open(self.report_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_markdown(self):
        lines = []

        lines.append("# Legacy Program Intelligence + Verification Report")
        lines.append("")
        lines.append(f"Generated on: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
        lines.append("")
        lines.append("## 1. Project Purpose")
        lines.append("")
        lines.append(
            "This report summarizes analysis results from the HLASM codebase. "
            "The system scans assembler modules, identifies program flow, extracts "
            "data dependencies, detects parameter passing, captures return-code behavior, "
            "and highlights modernization risks before Java conversion."
        )
        lines.append("")

        self._add_repository_summary(lines)
        self._add_file_summary(lines)
        self._add_parameter_summary(lines)
        self._add_data_dependency_summary(lines)
        self._add_return_code_summary(lines)
        self._add_condition_summary(lines)
        self._add_impact_summary(lines)
        self._add_warning_summary(lines)
        self._add_next_steps(lines)

        return "\n".join(lines)

    def _add_repository_summary(self, lines):
        lines.append("## 2. Repository Analysis Summary")
        lines.append("")

        modules = self._all_modules()

        lines.append(f"- Total analyzed modules: `{len(modules)}`")
        lines.append("- Analysis artifacts generated:")
        lines.append("  - `analysis_report.json`")
        lines.append("  - `docs/generated_behavior_report.md`")
        lines.append("  - `docs/project_analysis_report.md`")
        lines.append("")

        if modules:
            lines.append("**Modules detected:**")
            lines.append("")
            for module in modules:
                lines.append(f"- `{module}`")
            lines.append("")

    def _add_file_summary(self, lines):
        lines.append("## 3. File / DDNAME Summary")
        lines.append("")

        ddnames = self.report.get("ddnames", {})

        if not ddnames:
            lines.append("No DDNAME references detected.")
            lines.append("")
            return

        for acb, info in ddnames.items():
            lines.append(
                f"- `{acb}` references DDNAME `{info.get('ddname')}` "
                f"in module `{info.get('module')}`"
            )

        lines.append("")

    def _add_parameter_summary(self, lines):
        lines.append("## 4. Parameter Passing Summary")
        lines.append("")

        parameter_blocks = self.report.get("parameter_blocks", {})
        context = self.report.get("module_parameter_context", {})
        register_map = self.report.get("register_map", {})

        if not parameter_blocks:
            lines.append("No parameter blocks detected.")
            lines.append("")
        else:
            lines.append("**Parameter blocks:**")
            lines.append("")
            for block, params in parameter_blocks.items():
                lines.append(
                    f"- `{block}` → "
                    + ", ".join(f"`{p}`" for p in params)
                )
            lines.append("")

        if context:
            lines.append("**Module parameter context:**")
            lines.append("")
            for module, block in context.items():
                params = parameter_blocks.get(block, [])
                lines.append(
                    f"- `{module}` receives `{block}` → "
                    + ", ".join(f"`{p}`" for p in params)
                )
            lines.append("")

        if register_map:
            lines.append("**Resolved register maps:**")
            lines.append("")
            for module, regs in register_map.items():
                if not regs:
                    continue
                mapped = ", ".join(f"`{reg}`→`{sym}`" for reg, sym in regs.items())
                lines.append(f"- `{module}`: {mapped}")
            lines.append("")

    def _add_data_dependency_summary(self, lines):
        lines.append("## 5. Business Data Dependency Summary")
        lines.append("")

        reads = self.report.get("reads", {})
        writes = self.report.get("writes", {})

        modules = sorted(set(reads.keys()) | set(writes.keys()))

        if not modules:
            lines.append("No data reads/writes detected.")
            lines.append("")
            return

        for module in modules:
            lines.append(f"### `{module}`")
            lines.append("")

            module_reads = reads.get(module, [])
            module_writes = writes.get(module, [])

            lines.append(
                "- Business Fields Read: "
                + (", ".join(f"`{x}`" for x in module_reads) if module_reads else "None")
            )
            lines.append(
                "- Business Fields Written: "
                + (", ".join(f"`{x}`" for x in module_writes) if module_writes else "None")
            )
            lines.append("")

    def _add_return_code_summary(self, lines):
        lines.append("## 6. Return Code Summary")
        lines.append("")

        return_codes = self.report.get("return_codes", {})

        if not return_codes:
            lines.append("No return-code settings detected.")
            lines.append("")
            return

        for module, codes in return_codes.items():
            lines.append(
                f"- `{module}` sets RC/R15 values: "
                + ", ".join(f"`{code}`" for code in codes)
            )

        lines.append("")

    def _add_condition_summary(self, lines):
        lines.append("## 7. Condition Check Summary")
        lines.append("")

        conditions = self.report.get("conditions", {})

        if not conditions:
            lines.append("No condition checks detected.")
            lines.append("")
            return

        for module, module_conditions in conditions.items():
            lines.append(f"### `{module}`")
            lines.append("")

            for condition in module_conditions:
                instr = condition.get("instruction")
                operands = condition.get("operands", [])
                pretty = ", ".join(f"`{op}`" for op in operands)
                lines.append(f"- `{instr}` {pretty}")

            lines.append("")

    def _add_impact_summary(self, lines):
        lines.append("## 8. Impact Analysis Summary")
        lines.append("")

        symbols = self.report.get("symbols", {})
        readers = self.report.get("symbol_readers", {})
        writers = self.report.get("symbol_writers", {})

        found = False

        for symbol in symbols:
            symbol_readers = readers.get(symbol, [])
            symbol_writers = writers.get(symbol, [])

            if not symbol_readers and not symbol_writers:
                continue

            found = True

            impacted = []
            for module in symbol_readers + symbol_writers:
                if module not in impacted:
                    impacted.append(module)

            lines.append(f"### `{symbol}`")
            lines.append("")
            lines.append(
                "- Written by: "
                + (", ".join(f"`{x}`" for x in symbol_writers) if symbol_writers else "None")
            )
            lines.append(
                "- Read by: "
                + (", ".join(f"`{x}`" for x in symbol_readers) if symbol_readers else "None")
            )
            lines.append(
                "- Impacted modules: "
                + ", ".join(f"`{x}`" for x in impacted)
            )
            lines.append("")

        if not found:
            lines.append("No symbol-level impact detected.")
            lines.append("")

    def _add_warning_summary(self, lines):
        lines.append("## 9. Analyzer Notes / Modernization Risks")
        lines.append("")

        warnings = self.report.get("warnings", [])

        if not warnings:
            lines.append("No warnings detected.")
            lines.append("")
            return

        for warning in warnings:
            lines.append(f"- {warning}")

        lines.append("")
        lines.append(
            "These warnings indicate areas that should be reviewed before automatic "
            "Java conversion. They may represent register ambiguity, suspicious "
            "parameter offsets, or data-flow uncertainty."
        )
        lines.append("")

    def _add_next_steps(self, lines):
        lines.append("## 10. Recommended Next Steps")
        lines.append("")
        lines.append("1. Review analyzer warnings before Java generation.")
        lines.append("2. Use `generated_behavior_report.md` for module-level understanding.")
        lines.append("3. Use `analysis_report.json` as the source for Java code generation.")
        lines.append("4. Generate Java translation candidates module by module.")
        lines.append("5. Validate Java behavior against expected assembler behavior using test cases.")
        lines.append("6. Add ML-based behavioral validation after deterministic test harness is stable.")
        lines.append("")

    def _all_modules(self):
        modules = set()

        for section in [
            "reads",
            "writes",
            "return_codes",
            "conditions",
            "module_parameter_context",
            "register_map",
        ]:
            for module in self.report.get(section, {}):
                modules.add(module)

        return sorted(modules)

    def save_markdown(self, output_path="docs/project_analysis_report.md"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        content = self.generate_markdown()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path


if __name__ == "__main__":
    generator = DocumentationGenerator("analysis_report.json")

    output = generator.save_markdown("docs/project_analysis_report.md")

    print(f"Project documentation generated: {output}")