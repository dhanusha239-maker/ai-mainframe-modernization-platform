import json
import re
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from instruction_translator import InstructionTranslator


class JavaGenerator:
    def __init__(
        self,
        report_path="analysis_report.json",
        output_dir="generated_java",
        asm_dir="HLASM",
    ):
        self.report_path = report_path
        self.output_dir = Path(output_dir)
        self.asm_dir = Path(asm_dir)
        self.report = self._load_report()
        self.symbol_metadata = self._build_symbol_metadata()
        self.module_source_lines = self._load_module_source_lines()

    def _load_report(self):
        with open(self.report_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

        for old_file in self.output_dir.glob("*.java"):
            old_file.unlink()

        modules = self._discover_modules()

        print("Discovered modules for Java generation:")
        for module in modules:
            print(f"  - {module}")

        self._write("ExecutionContext.java", self._execution_context())
        self._write("ModuleResult.java", self._module_result())
        self._write("AssemblerModule.java", self._assembler_module())
        self._write("AsmRuntime.java", self._asm_runtime())
        self._write("ModernizationRuntime.java", self._runtime(modules))

        for module in modules:
            class_name = self._to_class_name(module)
            self._write(
                f"{class_name}.java",
                self._module_class(module, class_name),
            )

        print(f"\nGenerated Java files in: {self.output_dir}")

    def _discover_modules(self):
        modules = set()

        for section in [
            "reads",
            "writes",
            "return_codes",
            "conditions",
            "module_parameter_context",
            "register_map",
            "record_buffer_reads",
            "record_buffer_writes",
            "condition_branches",
        ]:
            value = self.report.get(section, {})
            if isinstance(value, dict):
                for module in value:
                    modules.add(module.upper())

        for _, info in self.report.get("symbols", {}).items():
            if isinstance(info, dict) and info.get("module"):
                modules.add(info["module"].upper())

        for _, info in self.report.get("ddnames", {}).items():
            if isinstance(info, dict) and info.get("module"):
                modules.add(info["module"].upper())

        for _, info in self.report.get("rpl_areas", {}).items():
            if isinstance(info, dict) and info.get("module"):
                modules.add(info["module"].upper())

        for module in self.module_source_lines:
            modules.add(module.upper())

        return sorted(modules)

    def _build_symbol_metadata(self):
        metadata = {}

        for symbol, info in self.report.get("symbols", {}).items():
            datatype = str(info.get("datatype", "")).upper()

            meta = {}

            cl_match = re.match(r"CL(\d+)", datatype)
            xl_match = re.match(r"XL(\d+)", datatype)
            pl_match = re.match(r"PL(\d+)", datatype)

            if cl_match:
                meta["type"] = "char"
                meta["length"] = int(cl_match.group(1))

            elif xl_match:
                meta["type"] = "hex"
                meta["length"] = int(xl_match.group(1))

            elif pl_match:
                packed_bytes = int(pl_match.group(1))
                meta["type"] = "packed_decimal"
                meta["length"] = packed_bytes
                meta["digits"] = (packed_bytes * 2) - 1

                # No safe universal way to infer scale from PLn alone.
                # Keep scale 0 unless future metadata explicitly provides it.
                meta["scale"] = int(info.get("scale", 0) or 0)

            elif datatype == "F":
                meta["type"] = "fullword"
                meta["length"] = 4

            f_match = re.match(r"(\d+)F", datatype)
            if f_match:
                meta["type"] = "fullword_array"
                meta["length"] = int(f_match.group(1)) * 4

            if meta:
                metadata[symbol.upper()] = meta

        return metadata

    def _load_module_source_lines(self):
        modules = {}

        if not self.asm_dir.exists():
            return modules

        files = sorted(
            [
                path
                for path in self.asm_dir.iterdir()
                if path.is_file()
                and path.name.lower().endswith((".asm", ".asm.txt", ".txt"))
            ]
        )

        current_module = None

        for file_path in files:
            current_module = None

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for raw_line in f:
                    line = raw_line.rstrip("\n")

                    if not line.strip():
                        continue

                    if line.startswith("*"):
                        continue

                    parts = line.strip().split()

                    if len(parts) >= 2 and parts[1].upper() == "CSECT":
                        current_module = parts[0].upper()
                        modules[current_module] = []
                        modules[current_module].append(line)
                        continue

                    if current_module:
                        modules[current_module].append(line)

        return modules

    def _to_class_name(self, module_name):
        parts = re.split(r"[^A-Za-z0-9]+", module_name.lower())
        name = "".join(part.capitalize() for part in parts if part)

        if not name:
            name = "GeneratedModule"

        if name[0].isdigit():
            name = "Module" + name

        return name

    def _write(self, filename, content):
        path = self.output_dir / filename
        path.write_text(content.strip() + "\n", encoding="utf-8")

    def _header(self, name):
        return f"""
/*
 * Generated by Legacy Assembler Modernization Intelligence Platform.
 * Artifact: {name}
 */
"""

    def _execution_context(self):
        return self._header("ExecutionContext") + """
import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

public class ExecutionContext {

    private final Map<String, Object> fields = new HashMap<>();

    public Object get(String fieldName) {
        return fields.get(fieldName);
    }

    public void set(String fieldName, Object value) {
        fields.put(fieldName, value);
    }

    public String getString(String fieldName) {
        Object value = fields.get(fieldName);
        return value == null ? "" : value.toString();
    }

    public void setString(String fieldName, String value) {
        fields.put(fieldName, value);
    }

    public BigDecimal getDecimal(String fieldName) {
        Object value = fields.get(fieldName);

        if (value == null) {
            return BigDecimal.ZERO;
        }

        if (value instanceof BigDecimal) {
            return (BigDecimal) value;
        }

        return new BigDecimal(value.toString());
    }

    public void setDecimal(String fieldName, BigDecimal value) {
        fields.put(fieldName, value);
    }

    public Map<String, Object> snapshot() {
        return new HashMap<>(fields);
    }
}
"""

    def _module_result(self):
        return self._header("ModuleResult") + """
public class ModuleResult {

    private final int returnCode;
    private final String message;

    public ModuleResult(int returnCode, String message) {
        this.returnCode = returnCode;
        this.message = message;
    }

    public int getReturnCode() {
        return returnCode;
    }

    public String getMessage() {
        return message;
    }

    public boolean isOk() {
        return returnCode == 0;
    }

    public static ModuleResult ok() {
        return new ModuleResult(0, "OK");
    }

    public static ModuleResult rc(int rc, String message) {
        return new ModuleResult(rc, message);
    }
}
"""

    def _assembler_module(self):
        return self._header("AssemblerModule") + """
public interface AssemblerModule {

    String name();

    ModuleResult execute(ExecutionContext ctx);
}
"""

    def _asm_runtime(self):
        return self._header("AsmRuntime") + """
import java.math.BigDecimal;
import java.math.RoundingMode;

public class AsmRuntime {

    public static class ConditionCode {
        public static final int EQUAL = 0;
        public static final int LOW = 1;
        public static final int HIGH = 2;
        public static final int OVERFLOW = 3;

        private int value = EQUAL;

        public int get() {
            return value;
        }

        public void setEqual() {
            value = EQUAL;
        }

        public void setLow() {
            value = LOW;
        }

        public void setHigh() {
            value = HIGH;
        }

        public void setOverflow() {
            value = OVERFLOW;
        }
    }

    public static class Registers {
        private final int[] gpr = new int[16];

        public int get(int register) {
            return gpr[register];
        }

        public void set(int register, int value) {
            gpr[register] = value;
        }

        public void clear(int register) {
            gpr[register] = 0;
        }

        public void decrement(int register) {
            gpr[register] = gpr[register] - 1;
        }
    }

    public static class Memory {

        public static String normalize(String value, int length) {
            if (value == null) {
                value = "";
            }

            if (value.length() > length) {
                return value.substring(0, length);
            }

            return String.format("%-" + length + "s", value);
        }

        public static void mvc(ExecutionContext ctx, String target, int length, String source) {
            ctx.setString(target, normalize(ctx.getString(source), length));
        }

        public static void mvcLiteral(ExecutionContext ctx, String target, int length, String literal) {
            ctx.setString(target, normalize(literal, length));
        }

        public static void mvi(ExecutionContext ctx, String target, char value) {
            ctx.setString(target, String.valueOf(value));
        }

        public static int clc(ExecutionContext ctx, String left, int length, String right, ConditionCode cc) {
            String l = normalize(ctx.getString(left), length);
            String r = normalize(ctx.getString(right), length);
            int result = l.compareTo(r);
            setCompareCondition(result, cc);
            return result;
        }

        public static int clcLiteral(ExecutionContext ctx, String left, int length, String literal, ConditionCode cc) {
            String l = normalize(ctx.getString(left), length);
            String r = normalize(literal, length);
            int result = l.compareTo(r);
            setCompareCondition(result, cc);
            return result;
        }

        public static int cli(ExecutionContext ctx, String left, char literal, ConditionCode cc) {
            String value = ctx.getString(left);
            char first = value.isEmpty() ? 0 : value.charAt(0);
            int result = Character.compare(first, literal);
            setCompareCondition(result, cc);
            return result;
        }

        public static void xc(ExecutionContext ctx, String target, int length, String source) {
            byte[] left = normalize(ctx.getString(target), length).getBytes();
            byte[] right = normalize(ctx.getString(source), length).getBytes();
            byte[] out = new byte[length];

            for (int i = 0; i < length; i++) {
                out[i] = (byte) (left[i] ^ right[i]);
            }

            ctx.setString(target, new String(out));
        }

        private static void setCompareCondition(int result, ConditionCode cc) {
            if (result == 0) {
                cc.setEqual();
            } else if (result < 0) {
                cc.setLow();
            } else {
                cc.setHigh();
            }
        }
    }

    public static class Packed {

        public static void zap(
                ExecutionContext ctx,
                String target,
                String source,
                int targetDigits,
                int scale,
                ConditionCode cc) {

            BigDecimal value = ctx.getDecimal(source);
            BigDecimal normalized = fitPacked(value, targetDigits, scale);
            ctx.setDecimal(target, normalized);
            setDecimalCondition(normalized, cc);
        }

        public static void ap(
                ExecutionContext ctx,
                String target,
                String source,
                int targetDigits,
                int scale,
                ConditionCode cc) {

            BigDecimal result = ctx.getDecimal(target).add(ctx.getDecimal(source));
            result = fitPacked(result, targetDigits, scale);
            ctx.setDecimal(target, result);
            setDecimalCondition(result, cc);
        }

        public static void sp(
                ExecutionContext ctx,
                String target,
                String source,
                int targetDigits,
                int scale,
                ConditionCode cc) {

            BigDecimal result = ctx.getDecimal(target).subtract(ctx.getDecimal(source));
            result = fitPacked(result, targetDigits, scale);
            ctx.setDecimal(target, result);
            setDecimalCondition(result, cc);
        }

        public static void mp(
                ExecutionContext ctx,
                String target,
                String source,
                int targetDigits,
                int scale,
                ConditionCode cc) {

            BigDecimal result = ctx.getDecimal(target).multiply(ctx.getDecimal(source));
            result = fitPacked(result, targetDigits, scale);
            ctx.setDecimal(target, result);
            setDecimalCondition(result, cc);
        }

        public static void dp(
                ExecutionContext ctx,
                String target,
                String source,
                int targetDigits,
                int scale,
                ConditionCode cc) {

            BigDecimal divisor = ctx.getDecimal(source);

            if (BigDecimal.ZERO.compareTo(divisor) == 0) {
                throw new ArithmeticException("Packed decimal divide by zero");
            }

            BigDecimal result = ctx.getDecimal(target).divide(divisor, scale, RoundingMode.HALF_UP);
            result = fitPacked(result, targetDigits, scale);
            ctx.setDecimal(target, result);
            setDecimalCondition(result, cc);
        }

        public static int cp(ExecutionContext ctx, String left, String right, ConditionCode cc) {
            int result = ctx.getDecimal(left).compareTo(ctx.getDecimal(right));
            setCompareCondition(result, cc);
            return result;
        }

        public static BigDecimal fitPacked(BigDecimal value, int totalDigits, int scale) {
            BigDecimal scaled = value.setScale(scale, RoundingMode.HALF_UP);
            BigDecimal absolute = scaled.abs();

            String digitsOnly = absolute
                    .movePointRight(scale)
                    .toPlainString()
                    .replace(".", "");

            if (digitsOnly.length() > totalDigits) {
                throw new ArithmeticException(
                        "Packed decimal overflow: value=" + value + " totalDigits=" + totalDigits);
            }

            return scaled;
        }

        private static void setDecimalCondition(BigDecimal value, ConditionCode cc) {
            int result = value.compareTo(BigDecimal.ZERO);

            if (result == 0) {
                cc.setEqual();
            } else if (result < 0) {
                cc.setLow();
            } else {
                cc.setHigh();
            }
        }

        private static void setCompareCondition(int result, ConditionCode cc) {
            if (result == 0) {
                cc.setEqual();
            } else if (result < 0) {
                cc.setLow();
            } else {
                cc.setHigh();
            }
        }
    }

    public static class Register {

        public static void xr(Registers registers, int r1, int r2, ConditionCode cc) {
            int result = registers.get(r1) ^ registers.get(r2);
            registers.set(r1, result);
            setBinaryCondition(result, cc);
        }

        public static void sr(Registers registers, int r1, int r2, ConditionCode cc) {
            int result = registers.get(r1) - registers.get(r2);
            registers.set(r1, result);
            setBinaryCondition(result, cc);
        }

        public static void ar(Registers registers, int r1, int r2, ConditionCode cc) {
            int result = registers.get(r1) + registers.get(r2);
            registers.set(r1, result);
            setBinaryCondition(result, cc);
        }

        public static void ltr(Registers registers, int r1, int r2, ConditionCode cc) {
            int value = registers.get(r2);
            registers.set(r1, value);
            setBinaryCondition(value, cc);
        }

        public static void lh(Registers registers, int register, short halfword) {
            registers.set(register, halfword);
        }

        public static void l(Registers registers, int register, int fullword) {
            registers.set(register, fullword);
        }

        private static void setBinaryCondition(int value, ConditionCode cc) {
            if (value == 0) {
                cc.setEqual();
            } else if (value < 0) {
                cc.setLow();
            } else {
                cc.setHigh();
            }
        }
    }

    public static class Branch {

        public static boolean isEqual(ConditionCode cc) {
            return cc.get() == ConditionCode.EQUAL;
        }

        public static boolean isNotEqual(ConditionCode cc) {
            return cc.get() != ConditionCode.EQUAL;
        }

        public static boolean isLow(ConditionCode cc) {
            return cc.get() == ConditionCode.LOW;
        }

        public static boolean isHigh(ConditionCode cc) {
            return cc.get() == ConditionCode.HIGH;
        }

        public static boolean bct(Registers registers, int register) {
            registers.decrement(register);
            return registers.get(register) != 0;
        }

        public static boolean bctr(Registers registers, int register) {
            registers.decrement(register);
            return registers.get(register) != 0;
        }
    }
}
"""

    def _runtime(self, modules):
        registrations = "\n".join(
            f"        modules.add(new {self._to_class_name(module)}());"
            for module in modules
        )

        return self._header("ModernizationRuntime") + f"""
import java.util.ArrayList;
import java.util.List;

public class ModernizationRuntime {{

    private final List<AssemblerModule> modules = new ArrayList<>();

    public ModernizationRuntime() {{
{registrations}
    }}

    public List<ModuleResult> execute(ExecutionContext ctx) {{
        List<ModuleResult> results = new ArrayList<>();

        for (AssemblerModule module : modules) {{
            ModuleResult result = module.execute(ctx);
            results.add(result);

            if (!result.isOk()) {{
                break;
            }}
        }}

        return results;
    }}
}}
"""

    def _module_class(self, module, class_name):
        reads = self.report.get("reads", {}).get(module, [])
        writes = self.report.get("writes", {}).get(module, [])
        return_codes = self.report.get("return_codes", {}).get(module, [])
        conditions = self.report.get("conditions", {}).get(module, [])

        default_rc = "0" if "0" in return_codes else (return_codes[0] if return_codes else "0")

        comment = self._module_comment(module, reads, writes, conditions)
        translated_code = self._translated_module_code(module)

        return self._header(class_name) + f"""
public class {class_name} implements AssemblerModule {{

    private final AsmRuntime.ConditionCode cc = new AsmRuntime.ConditionCode();
    private final AsmRuntime.Registers registers = new AsmRuntime.Registers();

    @Override
    public String name() {{
        return "{module}";
    }}

    @Override
    public ModuleResult execute(ExecutionContext ctx) {{

{comment}

{translated_code}

        return ModuleResult.rc({default_rc}, "{module} executed as generated candidate");
    }}
}}
"""

    def _module_comment(self, module, reads, writes, conditions):
        lines = [
            "        /*",
            f"         * HLASM Module: {module}",
            "         *",
        ]

        if reads:
            lines.append("         * Business fields read:")
            for item in reads:
                lines.append(f"         *   - {item}")

        if writes:
            lines.append("         * Business fields written:")
            for item in writes:
                lines.append(f"         *   - {item}")

        if conditions:
            lines.append("         * Conditions:")
            for condition in conditions:
                instr = condition.get("instruction")
                operands = ", ".join(condition.get("operands", []))
                lines.append(f"         *   - {instr} {operands}")

        lines.append("         */")

        return "\n".join(lines)

    def _translated_module_code(self, module):
        lines = self.module_source_lines.get(module.upper(), [])

        if not lines:
            return "        // No HLASM source lines found for this module."

        translator = InstructionTranslator(
            symbol_metadata=self.symbol_metadata,
            register_map=self.report.get("register_map", {}).get(module.upper(), {}),
            field_offsets=self.report.get("field_offsets", {}),
            module=module.upper(),
      )

        java_lines = []
        java_lines.append("        // Translated instruction candidates from HLASM source.")

        for asm_line in lines:
            stripped = asm_line.strip()

            if not stripped or stripped.startswith("*"):
                continue

            translated = translator.translate_line(asm_line)

            if translated is None:
                continue

            java_lines.append("")
            java_lines.append(f"        // ASM: {stripped}")

            for output_line in translated.splitlines():
                if output_line.strip():
                    java_lines.append(f"        {output_line}")

        if len(java_lines) == 1:
            java_lines.append("        // No translatable instructions found.")

        return "\n".join(java_lines)


if __name__ == "__main__":
    generator = JavaGenerator(
        report_path="analysis_report.json",
        output_dir="generated_java",
        asm_dir="HLASM",
    )
    generator.generate()