import json
import os
from collections import defaultdict


class BehaviorReporter:
    """
    Generates a clean module-by-module behavior report from analysis_report.json.

    Separates:
    - Parameter addresses received through parameter blocks/registers
    - Business/data fields actually read by instructions
    - Output fields written
    - Conditions
    - Return codes
    - Analyzer notes
    """

    def __init__(self, report_path="analysis_report.json"):
        self.report_path = report_path
        self.report = self._load_report()

    def _load_report(self):
        with open(self.report_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _all_modules(self):
        modules = set()

        sections = [
            "reads",
            "writes",
            "return_codes",
            "conditions",
            "module_parameter_context",
            "register_map",
        ]

        for section in sections:
            for module in self.report.get(section, {}):
                modules.add(module)

        return sorted(modules)

    def generate_markdown(self):
        lines = []

        lines.append("# HLASM Module Behavior Report")
        lines.append("")
        lines.append("Generated from `analysis_report.json`.")
        lines.append("")

        self._add_file_summary(lines)
        self._add_module_sections(lines)
        self._add_analyzer_notes(lines)

        return "\n".join(lines)

    def _add_file_summary(self, lines):
        lines.append("## File / DDNAME Summary")
        lines.append("")

        ddnames = self.report.get("ddnames", {})

        if not ddnames:
            lines.append("No DDNAME references detected.")
            lines.append("")
            return

        for acb, info in ddnames.items():
            lines.append(
                f"- `{acb}` uses DDNAME `{info.get('ddname')}` "
                f"in module `{info.get('module')}`"
            )

        lines.append("")

    def _add_module_sections(self, lines):
        lines.append("## Module Behavior Summary")
        lines.append("")

        reads = self.report.get("reads", {})
        writes = self.report.get("writes", {})
        return_codes = self.report.get("return_codes", {})
        conditions = self.report.get("conditions", {})
        parameter_context = self.report.get("module_parameter_context", {})
        parameter_blocks = self.report.get("parameter_blocks", {})
        register_map = self.report.get("register_map", {})

        module_notes = self._build_module_notes()

        for module in self._all_modules():
            lines.append(f"### Module: `{module}`")
            lines.append("")

            # Parameter block received
            if module in parameter_context:
                block = parameter_context[module]
                params = parameter_blocks.get(block, [])

                lines.append("**Parameter block received:**")
                lines.append("")
                lines.append(
                    f"- `{block}` → "
                    + ", ".join(f"`{p}`" for p in params)
                )
                lines.append("")

                lines.append("**Parameter addresses received:**")
                lines.append("")
                if params:
                    for param in params:
                        lines.append(f"- Address of `{param}`")
                else:
                    lines.append("- None detected")
                lines.append("")

            # Register map
            if module in register_map:
                regs = register_map[module]

                if regs:
                    lines.append("**Resolved register map:**")
                    lines.append("")

                    for reg, symbol in regs.items():
                        lines.append(f"- `{reg}` → address of `{symbol}`")

                    lines.append("")

            # Actual data/business reads
            module_reads = reads.get(module, [])

            lines.append("**Business/data fields read by instructions:**")
            lines.append("")

            if module_reads:
                for item in module_reads:
                    lines.append(f"- `{item}`")
            else:
                lines.append("- None detected")

            lines.append("")

            # Writes
            module_writes = writes.get(module, [])

            lines.append("**Output fields written by instructions:**")
            lines.append("")

            if module_writes:
                for item in module_writes:
                    lines.append(f"- `{item}`")
            else:
                lines.append("- None detected")

            lines.append("")

            # Conditions
            module_conditions = conditions.get(module, [])

            lines.append("**Condition checks:**")
            lines.append("")

            if module_conditions:
                for condition in module_conditions:
                    instr = condition.get("instruction")
                    operands = condition.get("operands", [])

                    pretty_operands = ", ".join(
                        f"`{op}`" for op in operands
                    )
                    lines.append(f"- `{instr}` {pretty_operands}")
            else:
                lines.append("- None detected")

            lines.append("")

            # Return codes
            module_rcs = return_codes.get(module, [])

            lines.append("**Return codes set:**")
            lines.append("")

            if module_rcs:
                for rc in module_rcs:
                    lines.append(f"- RC `{rc}`")
            else:
                lines.append("- None detected")

            lines.append("")

            # Analyzer notes
            if module in module_notes:
                lines.append("**Analyzer notes:**")
                lines.append("")

                for note in module_notes[module]:
                    lines.append(f"- {note}")

                lines.append("")

    def _build_module_notes(self):
        notes = defaultdict(list)

        warnings = self.report.get("warnings", [])
        register_map = self.report.get("register_map", {})
        parameter_context = self.report.get("module_parameter_context", {})
        parameter_blocks = self.report.get("parameter_blocks", {})
        conditions = self.report.get("conditions", {})

        for warning in warnings:
            module = warning.split(":", 1)[0].strip()

            notes[module].append(warning)

            if "mapped to multiple registers" in warning:
                self._add_duplicate_register_explanation(
                    notes,
                    module,
                    register_map,
                    parameter_context,
                    parameter_blocks,
                    conditions,
                )

        return notes

    def _add_duplicate_register_explanation(
        self,
        notes,
        module,
        register_map,
        parameter_context,
        parameter_blocks,
        conditions,
    ):
        regs = register_map.get(module, {})
        block = parameter_context.get(module)
        params = parameter_blocks.get(block, [])

        if block:
            notes[module].append(
                f"Parameter block `{block}` contains: "
                + ", ".join(f"`{p}`" for p in params)
                + "."
            )

        symbol_to_regs = defaultdict(list)

        for reg, symbol in regs.items():
            symbol_to_regs[symbol].append(reg)

        for symbol, reg_list in symbol_to_regs.items():
            if len(reg_list) > 1:
                pretty_regs = ", ".join(f"`{r}`" for r in reg_list)

                notes[module].append(
                    f"`{symbol}` is resolved through multiple registers: "
                    f"{pretty_regs}. This may indicate ambiguous or suspicious "
                    f"parameter offset usage."
                )

        module_conditions = conditions.get(module, [])

        if module_conditions:
            notes[module].append(
                "Review condition checks in this module before Java conversion, "
                "because register ambiguity can change which business field is "
                "actually being compared."
            )

        notes[module].append(
            "Recommendation: do not auto-convert this module without manual "
            "review of parameter offsets and register usage."
        )

    def _add_analyzer_notes(self, lines):
        lines.append("## Analyzer Notes / Warnings")
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
            "These warnings do not necessarily mean the program is invalid. "
            "They indicate areas where register usage, parameter offsets, or "
            "data-flow inference should be manually reviewed before Java "
            "conversion."
        )
        lines.append("")

    def save_markdown(self, output_path="docs/generated_behavior_report.md"):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        markdown = self.generate_markdown()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        return output_path


if __name__ == "__main__":
    reporter = BehaviorReporter("analysis_report.json")

    output = reporter.save_markdown("docs/generated_behavior_report.md")

    print(f"Behavior report generated: {output}")