import csv
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_CASES_DIR = PROJECT_ROOT / "test_cases"
BATCH_DIR = TEST_CASES_DIR / "batch"
JAVA_DIR = PROJECT_ROOT / "generated_java"
DOCS_DIR = PROJECT_ROOT / "docs"

TEST_CASE_FILE = TEST_CASES_DIR / "behavior_test_cases.json"
JAVA_RUNNER_FILE = JAVA_DIR / "BehaviorTestRunner.java"
JAVA_OUTPUT_FILE = JAVA_DIR / "java_behavior_output.json"

REPORT_FILE = DOCS_DIR / "behavior_comparison_report.md"
RESULT_JSON_FILE = DOCS_DIR / "behavior_comparison_results.json"


# -------------------------------------------------------------------
# IMPORTANT FOR FUTURE DOMAINS / TEST CASES
# -------------------------------------------------------------------
# To test another domain or another business function:
#
# 1. Edit this file:
#       test_cases/behavior_test_cases.json
#
# 2. Add test cases like:
#       {
#         "case_id": "CUSTVAL_INVALID_001",
#         "mode": "module",
#         "module": "CUSTVAL",
#         "input": {
#           "TXCUST": "BAD000001",
#           "ERRCODE": "0000"
#         },
#         "expected_asm_output": {
#           "ERRCODE": "E001",
#           "RC": "4"
#         }
#       }
#
# 3. mode = "module"
#       Runs one generated Java module, for example:
#       CUSTVAL, LIMITCHK, CARDSTAT, FRDCHK, FEECALC, AUTHDEC
#
# 4. mode = "flow"
#       Runs the full ModernizationRuntime flow.
#
# 5. expected_asm_output means:
#       What the original assembler is expected to produce.
#
# 6. The comparator will:
#       - compile generated Java
#       - execute generated Java
#       - capture actual Java output
#       - compare ASM expected output vs Java actual output
#       - write markdown and JSON reports
# -------------------------------------------------------------------


def ensure_dirs():
    TEST_CASES_DIR.mkdir(parents=True, exist_ok=True)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    JAVA_DIR.mkdir(parents=True, exist_ok=True)


def create_sample_test_cases_if_missing():
    """
    Creates sample test cases only if behavior_test_cases.json does not exist.

    These are starter examples.
    For future domains, update test_cases/behavior_test_cases.json directly.
    """

    if TEST_CASE_FILE.exists():
        return

    sample_cases = [
        {
            "case_id": "CUSTVAL_INVALID_001",
            "mode": "module",
            "module": "CUSTVAL",
            "description": "Customer ID does not start with CUST; assembler should set E001.",
            "input": {
                "TXCUST": "BAD000001",
                "ERRCODE": "0000"
            },
            "expected_asm_output": {
                "ERRCODE": "E001",
                "RC": "4"
            }
        },
        {
            "case_id": "CUSTVAL_VALID_001",
            "mode": "module",
            "module": "CUSTVAL",
            "description": "Customer ID starts with CUST; assembler should leave ERRCODE as 0000.",
            "input": {
                "TXCUST": "CUST000001",
                "ERRCODE": "0000"
            },
            "expected_asm_output": {
                "ERRCODE": "0000",
                "RC": "0"
            }
        },
        {
            "case_id": "LIMITCHK_REJECT_001",
            "mode": "module",
            "module": "LIMITCHK",
            "description": "Transaction amount exceeds limit; assembler should set E003.",
            "input": {
                "TXAMT": "750.00",
                "TXLIMIT": "500.00",
                "ERRCODE": "0000"
            },
            "expected_asm_output": {
                "ERRCODE": "E003",
                "RC": "4"
            }
        }
    ]

    TEST_CASE_FILE.write_text(
        json.dumps(sample_cases, indent=2),
        encoding="utf-8",
    )


def load_test_cases():
    create_sample_test_cases_if_missing()

    with open(TEST_CASE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_batch_file(csv_file):
    """
    Load a batch transaction CSV file into a list of dictionaries.

    This is Step 1 of the batch validation engine.

    Expected CSV example:
        CASE_ID,TXCUST,TXSTAT,TXAMT,TXLIMIT,TXTYPE,
        EXPECTED_RC,EXPECTED_ERRCODE,EXPECTED_AUTHSTAT,EXPECTED_TXFEE

    Returns:
        [
            {
                "CASE_ID": "TX001",
                "TXCUST": "CUST000001",
                "TXSTAT": "A",
                ...
            }
        ]

    Notes:
        - This function only reads CSV data.
        - It does not run Java.
        - It does not compare expected vs actual output.
        - Later steps will use these rows for batch execution.
    """

    csv_path = Path(csv_file)

    if not csv_path.is_absolute():
        csv_path = PROJECT_ROOT / csv_path

    if not csv_path.exists():
        raise FileNotFoundError(f"Batch CSV file not found: {csv_path}")

    rows = []

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError(f"Batch CSV file has no header row: {csv_path}")

        for row_number, row in enumerate(reader, start=2):
            cleaned = {}

            for key, value in row.items():
                if key is None:
                    continue

                clean_key = str(key).strip()
                clean_value = "" if value is None else str(value).strip()

                cleaned[clean_key] = clean_value

            if not any(cleaned.values()):
                continue

            if not cleaned.get("CASE_ID"):
                raise ValueError(
                    f"Missing CASE_ID in batch CSV file {csv_path} at row {row_number}"
                )

            rows.append(cleaned)

    return rows


def java_class_name(module_name):
    """
    Matches java_generator.py naming style:
      CUSTVAL  -> Custval
      LIMITCHK -> Limitchk
      MAINDRV  -> Maindrv
    """

    module_name = module_name.strip().lower()
    return "".join(part.capitalize() for part in module_name.split("_"))


def java_string(value):
    """
    Safe Java string literal.
    """

    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def generate_java_runner(test_cases):
    """
    Dynamically writes generated_java/BehaviorTestRunner.java.

    This Java program:
      - loads each test case input into ExecutionContext
      - runs generated Java module or full flow
      - captures actual Java output
      - writes java_behavior_output.json
    """

    case_methods = []
    main_calls = []

    for idx, case in enumerate(test_cases):
        method_name = f"runCase{idx}"
        main_calls.append(f"        results.add({method_name}());")

        mode = case.get("mode", "module").lower()

        if mode == "application":
            module = case.get("entry_module", "MAINDRV")
        else:
            module = case.get("module", "")

        class_name = java_class_name(module)

        input_lines = []
        for field, value in case.get("input", {}).items():
            if is_decimal_value(value):
                input_lines.append(
                    f'        ctx.setDecimal("{field}", new java.math.BigDecimal("{java_string(value)}"));'
                )
            else:
                input_lines.append(
                    f'        ctx.setString("{field}", "{java_string(value)}");'
                )

        expected_fields = list(case.get("expected_asm_output", {}).keys())
        output_lines = []

        # Always capture expected fields.
        for field in expected_fields:
            if field == "RC":
                continue
            output_lines.append(
                f'        output.put("{field}", ctx.getString("{field}"));'
            )

        # Capture commonly used business fields if they exist.
        for field in [
            "ERRCODE",
            "AUTHSTAT",
            "TXFEE",
            "TXAMT",
            "TXLIMIT",
            "TXCUST",
            "TXSTAT",
            "TXTYPE",
        ]:
            if field not in expected_fields:
                output_lines.append(
                    f'        output.put("{field}", ctx.getString("{field}"));'
                )

        if mode == "application":
            execution_code = f"""
                AssemblerModule application = new {class_name}();
                ModuleResult result = application.execute(ctx);
                int rc = result.getReturnCode();
        """
        else:
            execution_code = f"""
                AssemblerModule module = new {class_name}();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        """
 
        method = f"""
    private static java.util.Map<String, String> {method_name}() {{
        ExecutionContext ctx = new ExecutionContext();

{chr(10).join(input_lines)}

{execution_code}

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "{java_string(case.get("case_id", "UNKNOWN"))}");
        output.put("module", "{java_string(module)}");
        output.put("RC", String.valueOf(rc));

{chr(10).join(output_lines)}

        return output;
    }}
"""
        case_methods.append(method)

    runner = f"""
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class BehaviorTestRunner {{

    public static void main(String[] args) throws Exception {{
        List<java.util.Map<String, String>> results = new ArrayList<>();

{chr(10).join(main_calls)}

        writeJson(results);
    }}

    private static void writeJson(List<java.util.Map<String, String>> results) throws IOException {{
        try (FileWriter writer = new FileWriter("java_behavior_output.json")) {{
            writer.write("[\\n");

            for (int i = 0; i < results.size(); i++) {{
                java.util.Map<String, String> item = results.get(i);

                writer.write("  {{\\n");

                int j = 0;
                for (java.util.Map.Entry<String, String> entry : item.entrySet()) {{
                    writer.write("    \\"" + escape(entry.getKey()) + "\\": \\"" + escape(entry.getValue()) + "\\"");

                    if (j < item.size() - 1) {{
                        writer.write(",");
                    }}

                    writer.write("\\n");
                    j++;
                }}

                writer.write("  }}");

                if (i < results.size() - 1) {{
                    writer.write(",");
                }}

                writer.write("\\n");
            }}

            writer.write("]\\n");
        }}
    }}

    private static String escape(String value) {{
        if (value == null) {{
            return "";
        }}

        return value.replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\"");
    }}

{chr(10).join(case_methods)}
}}
"""

    JAVA_RUNNER_FILE.write_text(runner.strip() + "\n", encoding="utf-8")


def is_decimal_value(value):
    """
    Decides whether to initialize Java ExecutionContext as decimal.
    """

    text = str(value)

    if text.startswith("-"):
        text = text[1:]

    return text.replace(".", "", 1).isdigit() and "." in text


def compile_java():
    print("Compiling generated Java...")

    result = subprocess.run(
        ["javac", "*.java"],
        cwd=JAVA_DIR,
        shell=True,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit("Java compilation failed.")


def run_java():
    print("Running generated Java behavior tests...")

    result = subprocess.run(
        ["java", "BehaviorTestRunner"],
        cwd=JAVA_DIR,
        shell=True,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit("Java behavior execution failed.")

    if not JAVA_OUTPUT_FILE.exists():
        raise FileNotFoundError(f"Expected Java output not found: {JAVA_OUTPUT_FILE}")

    with open(JAVA_OUTPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_value(value):
    if value is None:
        return ""

    return str(value).strip()


def compare_expected_actual(expected, actual):
    total = 0
    matched = 0
    mismatches = []

    for field, expected_value in expected.items():
        total += 1

        actual_value = actual.get(field)

        expected_norm = normalize_value(expected_value)
        actual_norm = normalize_value(actual_value)

        if expected_norm == actual_norm:
            matched += 1
        else:
            mismatches.append(
                {
                    "field": field,
                    "expected": expected_value,
                    "actual": actual_value,
                }
            )

    match_score = 100.0 if total == 0 else round((matched / total) * 100, 2)

    return {
        "total_fields": total,
        "matched_fields": matched,
        "mismatched_fields": mismatches,
        "match_score": match_score,
    }


def compare_all(test_cases, java_outputs):
    java_by_case = {
        item.get("case_id"): item
        for item in java_outputs
    }

    results = []

    for case in test_cases:
        case_id = case.get("case_id", "UNKNOWN")
        actual_java_output = java_by_case.get(case_id, {})

        comparison = compare_expected_actual(
            case.get("expected_asm_output", {}),
            actual_java_output,
        )

        results.append(
            {
                "case_id": case_id,
                "mode": case.get("mode", "module"),
                "module": case.get("module", "UNKNOWN"),
                "description": case.get("description", ""),
                "input": case.get("input", {}),
                "expected_asm_output": case.get("expected_asm_output", {}),
                "actual_java_output": actual_java_output,
                "comparison": comparison,
            }
        )

    return results


def generate_markdown_report(results):
    lines = []

    lines.append("# Behavior Comparison Report")
    lines.append("")
    lines.append("This report compares expected assembler behavior against actual generated Java execution output.")
    lines.append("")

    total_cases = len(results)
    passed_cases = sum(
        1 for item in results
        if item["comparison"]["match_score"] == 100.0
    )
    failed_cases = total_cases - passed_cases

    average_score = 0.0
    if total_cases:
        average_score = round(
            sum(item["comparison"]["match_score"] for item in results) / total_cases,
            2,
        )

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total test cases: `{total_cases}`")
    lines.append(f"- Passed cases: `{passed_cases}`")
    lines.append(f"- Failed cases: `{failed_cases}`")
    lines.append(f"- Average behavior match score: `{average_score}%`")
    lines.append("")

    lines.append("## Validation Flow")
    lines.append("")
    lines.append("1. Read expected assembler behavior from `test_cases/behavior_test_cases.json`.")
    lines.append("2. Generate `generated_java/BehaviorTestRunner.java` dynamically.")
    lines.append("3. Compile generated Java using `javac`.")
    lines.append("4. Execute generated Java using `java BehaviorTestRunner`.")
    lines.append("5. Capture actual Java output from `generated_java/java_behavior_output.json`.")
    lines.append("6. Compare expected assembler output vs actual Java output.")
    lines.append("")

    lines.append("## Detailed Results")
    lines.append("")

    for item in results:
        comparison = item["comparison"]

        lines.append(f"### Test Case: `{item['case_id']}`")
        lines.append("")
        lines.append(f"- Mode: `{item['mode']}`")
        lines.append(f"- Module: `{item['module']}`")
        lines.append(f"- Description: {item['description']}")
        lines.append(f"- Match score: `{comparison['match_score']}%`")
        lines.append(f"- Fields matched: `{comparison['matched_fields']}/{comparison['total_fields']}`")
        lines.append("")

        lines.append("**Input:**")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(item["input"], indent=2))
        lines.append("```")
        lines.append("")

        lines.append("**Expected ASM Output:**")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(item["expected_asm_output"], indent=2))
        lines.append("```")
        lines.append("")

        lines.append("**Actual Java Output:**")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(item["actual_java_output"], indent=2))
        lines.append("```")
        lines.append("")

        if comparison["mismatched_fields"]:
            lines.append("**Mismatches:**")
            lines.append("")
            for mismatch in comparison["mismatched_fields"]:
                lines.append(
                    f"- `{mismatch['field']}` expected `{mismatch['expected']}` "
                    f"but Java produced `{mismatch['actual']}`"
                )
            lines.append("")
        else:
            lines.append("No mismatches detected.")
            lines.append("")

    return "\n".join(lines)


def save_results(results):
    RESULT_JSON_FILE.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    REPORT_FILE.write_text(
        generate_markdown_report(results),
        encoding="utf-8",
    )


def print_summary(results):
    total_cases = len(results)
    passed_cases = sum(
        1 for item in results
        if item["comparison"]["match_score"] == 100.0
    )
    failed_cases = total_cases - passed_cases

    average_score = 0.0
    if total_cases:
        average_score = round(
            sum(item["comparison"]["match_score"] for item in results) / total_cases,
            2,
        )

    print()
    print("BEHAVIOR COMPARISON SUMMARY")
    print("=" * 60)
    print(f"Total test cases: {total_cases}")
    print(f"Passed cases: {passed_cases}")
    print(f"Failed cases: {failed_cases}")
    print(f"Average behavior match score: {average_score}%")
    print()
    print(f"Saved report to: {REPORT_FILE}")
    print(f"Saved JSON results to: {RESULT_JSON_FILE}")
    print(f"Saved Java runner to: {JAVA_RUNNER_FILE}")
    print(f"Saved Java execution output to: {JAVA_OUTPUT_FILE}")


def main():
    ensure_dirs()

    test_cases = load_test_cases()

    generate_java_runner(test_cases)
    compile_java()

    java_outputs = run_java()

    results = compare_all(test_cases, java_outputs)

    save_results(results)
    print_summary(results)


if __name__ == "__main__":
    main()