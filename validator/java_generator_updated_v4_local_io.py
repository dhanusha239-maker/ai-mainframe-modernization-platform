import json
import re
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from instruction_translator_updated_v3 import InstructionTranslator


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

    public int getInt(String fieldName) {
        Object value = fields.get(fieldName);

        if (value == null) {
            return 0;
        }

        if (value instanceof Number) {
            return ((Number) value).intValue();
        }

        return Integer.parseInt(value.toString().trim());
    }

    public void setInt(String fieldName, int value) {
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

        public static void tr(ExecutionContext ctx, String target, int length, String tableField) {
            String input = normalize(ctx.getString(target), length);
            String table = ctx.getString(tableField);

            if (table == null || table.isEmpty()) {
                ctx.setString(target, input);
                return;
            }

            StringBuilder out = new StringBuilder();

            for (int i = 0; i < input.length(); i++) {
                int idx = input.charAt(i) & 0xFF;

                if (idx < table.length()) {
                    out.append(table.charAt(idx));
                } else {
                    out.append(input.charAt(i));
                }
            }

            ctx.setString(target, out.toString());
        }

        public static void trt(
                ExecutionContext ctx,
                String target,
                int length,
                String tableField,
                Registers registers,
                ConditionCode cc) {

            String input = normalize(ctx.getString(target), length);
            String table = ctx.getString(tableField);

            if (table == null || table.isEmpty()) {
                cc.setEqual();
                return;
            }

            for (int i = 0; i < input.length(); i++) {
                int idx = input.charAt(i) & 0xFF;

                if (idx < table.length() && table.charAt(idx) != 0 && table.charAt(idx) != '0') {
                    registers.set(1, i);
                    registers.set(2, table.charAt(idx));
                    cc.setLow();
                    return;
                }
            }

            cc.setEqual();
        }

        public static void oi(ExecutionContext ctx, String targetOperand, int immediate, ConditionCode cc) {
            applyImmediateLogical(ctx, targetOperand, immediate, "OR", cc);
        }

        public static void xi(ExecutionContext ctx, String targetOperand, int immediate, ConditionCode cc) {
            applyImmediateLogical(ctx, targetOperand, immediate, "XOR", cc);
        }

        public static void ni(ExecutionContext ctx, String targetOperand, int immediate, ConditionCode cc) {
            applyImmediateLogical(ctx, targetOperand, immediate, "AND", cc);
        }

        private static void applyImmediateLogical(
                ExecutionContext ctx,
                String targetOperand,
                int immediate,
                String operation,
                ConditionCode cc) {

            String field = targetOperand;
            int offset = 0;

            int plus = targetOperand.indexOf('+');
            if (plus >= 0) {
                field = targetOperand.substring(0, plus);
                try {
                    offset = Integer.parseInt(targetOperand.substring(plus + 1));
                } catch (NumberFormatException ex) {
                    offset = 0;
                }
            }

            String value = ctx.getString(field);
            if (value == null) {
                value = "";
            }
            if (value.length() <= offset) {
                value = Memory.normalize(value, offset + 1);
            }

            char[] chars = value.toCharArray();
            int current = chars[offset] & 0xFF;
            int result;

            if ("AND".equals(operation)) {
                result = current & immediate;
            } else if ("XOR".equals(operation)) {
                result = current ^ immediate;
            } else {
                result = current | immediate;
            }

            chars[offset] = (char) (result & 0xFF);
            ctx.setString(field, new String(chars));

            if ((result & 0xFF) == 0) {
                cc.setEqual();
            } else {
                cc.setLow();
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

        public static void pack(
                ExecutionContext ctx,
                String target,
                String source,
                int targetLength,
                int sourceLength,
                int targetDigits,
                int scale,
                ConditionCode cc) {

            String zoned = Memory.normalize(ctx.getString(source), sourceLength).trim();
            if (zoned.isEmpty()) {
                zoned = "0";
            }

            String cleaned = zoned.replaceAll("[^0-9+.-]", "");
            if (cleaned.isEmpty() || cleaned.equals("+") || cleaned.equals("-")) {
                cleaned = "0";
            }

            BigDecimal value = new BigDecimal(cleaned);
            BigDecimal normalized = fitPacked(value, targetDigits, scale);
            ctx.setDecimal(target, normalized);
            setDecimalCondition(normalized, cc);
        }

        public static void unpk(
                ExecutionContext ctx,
                String target,
                String source,
                int targetLength,
                int sourceLength,
                int sourceDigits,
                int scale) {

            BigDecimal value = ctx.getDecimal(source);
            String plain = value.setScale(scale, RoundingMode.HALF_UP).movePointRight(scale).abs().toPlainString();
            String zoned = Memory.normalize(plain, targetLength);
            ctx.setString(target, zoned);
        }

        public static void srp(
                ExecutionContext ctx,
                String target,
                int shiftRightDigits,
                int roundingDigit,
                int targetDigits,
                int scale,
                ConditionCode cc) {

            BigDecimal divisor = BigDecimal.TEN.pow(Math.max(0, shiftRightDigits));
            BigDecimal value = ctx.getDecimal(target).divide(divisor, scale, RoundingMode.HALF_UP);
            BigDecimal normalized = fitPacked(value, targetDigits, scale);
            ctx.setDecimal(target, normalized);
            setDecimalCondition(normalized, cc);
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

        public static void oi(ExecutionContext ctx, String targetOperand, int immediate, ConditionCode cc) {
            applyImmediateLogical(ctx, targetOperand, immediate, "OR", cc);
        }

        public static void xi(ExecutionContext ctx, String targetOperand, int immediate, ConditionCode cc) {
            applyImmediateLogical(ctx, targetOperand, immediate, "XOR", cc);
        }

        public static void ni(ExecutionContext ctx, String targetOperand, int immediate, ConditionCode cc) {
            applyImmediateLogical(ctx, targetOperand, immediate, "AND", cc);
        }

        private static void applyImmediateLogical(
                ExecutionContext ctx,
                String targetOperand,
                int immediate,
                String operation,
                ConditionCode cc) {

            String field = targetOperand;
            int offset = 0;

            int plus = targetOperand.indexOf('+');
            if (plus >= 0) {
                field = targetOperand.substring(0, plus);
                try {
                    offset = Integer.parseInt(targetOperand.substring(plus + 1));
                } catch (NumberFormatException ex) {
                    offset = 0;
                }
            }

            String value = ctx.getString(field);
            if (value == null) {
                value = "";
            }
            if (value.length() <= offset) {
                value = Memory.normalize(value, offset + 1);
            }

            char[] chars = value.toCharArray();
            int current = chars[offset] & 0xFF;
            int result;

            if ("AND".equals(operation)) {
                result = current & immediate;
            } else if ("XOR".equals(operation)) {
                result = current ^ immediate;
            } else {
                result = current | immediate;
            }

            chars[offset] = (char) (result & 0xFF);
            ctx.setString(field, new String(chars));

            if ((result & 0xFF) == 0) {
                cc.setEqual();
            } else {
                cc.setLow();
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

        public static void lr(Registers registers, int r1, int r2) {
            registers.set(r1, registers.get(r2));
        }

        public static void lh(Registers registers, int register, short halfword) {
            registers.set(register, halfword);
        }

        public static void l(Registers registers, int register, int fullword) {
            registers.set(register, fullword);
        }

        public static void loadFullword(ExecutionContext ctx, Registers registers, int register, String field) {
            registers.set(register, ctx.getInt(field));
        }

        public static void storeFullword(ExecutionContext ctx, Registers registers, int register, String field) {
            ctx.setInt(field, registers.get(register));
        }

        public static void storeStringFromRegister(ExecutionContext ctx, Registers registers, int register, String field) {
            ctx.setString(field, String.valueOf(registers.get(register)));
        }

        public static void aImmediate(Registers registers, int register, int value, ConditionCode cc) {
            int result = registers.get(register) + value;
            registers.set(register, result);
            setBinaryCondition(result, cc);
        }

        public static void cImmediate(Registers registers, int register, int value, ConditionCode cc) {
            int result = Integer.compare(registers.get(register), value);
            if (result == 0) {
                cc.setEqual();
            } else if (result < 0) {
                cc.setLow();
            } else {
                cc.setHigh();
            }
        }

        public static void a(ExecutionContext ctx, Registers registers, int register, String field, ConditionCode cc) {
            int result = registers.get(register) + ctx.getInt(field);
            registers.set(register, result);
            setBinaryCondition(result, cc);
        }

        public static void c(ExecutionContext ctx, Registers registers, int register, String field, ConditionCode cc) {
            int result = Integer.compare(registers.get(register), ctx.getInt(field));
            if (result == 0) {
                cc.setEqual();
            } else if (result < 0) {
                cc.setLow();
            } else {
                cc.setHigh();
            }
        }

        public static void cr(Registers registers, int r1, int r2, ConditionCode cc) {
            int result = Integer.compare(registers.get(r1), registers.get(r2));
            if (result == 0) {
                cc.setEqual();
            } else if (result < 0) {
                cc.setLow();
            } else {
                cc.setHigh();
            }
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

    public static class Address {
        private final String field;
        private final Integer immediate;

        private Address(String field, Integer immediate) {
            this.field = field;
            this.immediate = immediate;
        }

        public static Address ofField(String field) {
            return new Address(field, null);
        }

        public static Address ofImmediate(int value) {
            return new Address(null, value);
        }

        public static Address ofBaseOffset(Registers registers, int baseRegister, int offset) {
            return new Address(null, registers.get(baseRegister) + offset);
        }

        public static Address ofIndexed(Registers registers, int baseRegister, int indexRegister, int offset) {
            return new Address(null, registers.get(baseRegister) + registers.get(indexRegister) + offset);
        }

        public static void la(ExecutionContext ctx, Registers registers, int register, Address address) {
            if (address.immediate != null) {
                registers.set(register, address.immediate);
            } else if (address.field != null) {
                registers.set(register, Math.abs(address.field.hashCode()));
            } else {
                registers.set(register, 0);
            }
        }
    }

    public static class IO {
        /*
         * Local DDNAME adapter for validation.
         *
         * The generated translator emits generic mainframe-style calls:
         *   OPEN / GET / PUT / CLOSE
         *
         * This adapter maps those calls to local fixed-width files.  It also
         * records the last I/O return code in __LAST_IO_RC so translated code
         * can move that value into R15 and use normal LTR/JZ/BNZ branch flow.
         */

        public static void open(ExecutionContext ctx, ConditionCode cc, String... resources) {
            ctx.set("IO_OPEN", String.join(",", resources));
            ctx.setInt("__LAST_IO_RC", 0);
            cc.setEqual();
        }

        public static void close(ExecutionContext ctx, ConditionCode cc, String... resources) {
            ctx.set("IO_CLOSE", String.join(",", resources));
            ctx.setInt("__LAST_IO_RC", 0);
            cc.setEqual();
        }

        public static void get(ExecutionContext ctx, String resource, String recordField, ConditionCode cc) {
            String effectiveRecordField = effectiveInputRecordField(ctx, resource, recordField);
            String force = ctx.getString("IO_FORCE_READ");

            // Behavior-comparator context mode: data is already staged in ctx.
            if (!"true".equalsIgnoreCase(force) && contextAlreadyHasTransaction(ctx)) {
                ctx.setInt("__LAST_IO_RC", 0);
                cc.setEqual();
                return;
            }

            String staged = ctx.getString(resource + "_NEXT");
            if (staged != null && !staged.isEmpty()) {
                storeRecord(ctx, effectiveRecordField, staged);
                ctx.setInt("__LAST_IO_RC", 0);
                cc.setEqual();
                return;
            }

            String path = resolveInputPath(ctx, resource, effectiveRecordField);

            if (path == null || path.isEmpty()) {
                ctx.setInt("__LAST_IO_RC", 8);
                cc.setHigh();
                return;
            }

            try {
                java.nio.file.Path filePath = existingPath(path);

                if (filePath == null || !java.nio.file.Files.exists(filePath)) {
                    ctx.setString("IO_ERROR", "Input file not found: " + path);
                    ctx.setInt("__LAST_IO_RC", 8);
                    cc.setHigh();
                    return;
                }

                java.util.List<String> lines = java.nio.file.Files.readAllLines(
                        filePath,
                        java.nio.charset.StandardCharsets.UTF_8);

                String cursorKey = "IO_CURSOR_" + sanitizeKey(resource) + "_" + sanitizeKey(effectiveRecordField);
                int pos = ctx.getInt(cursorKey);

                if (pos >= lines.size()) {
                    ctx.setInt("__LAST_IO_RC", 4);
                    cc.setHigh();
                    return;
                }

                String record = lines.get(pos);
                ctx.setInt(cursorKey, pos + 1);
                storeRecord(ctx, effectiveRecordField, record);
                ctx.setInt("__LAST_IO_RC", 0);
                cc.setEqual();

            } catch (Exception ex) {
                ctx.setString("IO_ERROR", ex.getMessage() == null ? ex.toString() : ex.getMessage());
                ctx.setInt("__LAST_IO_RC", 8);
                cc.setHigh();
            }
        }

        public static void put(ExecutionContext ctx, String resource, String recordField, ConditionCode cc) {
            String effectiveRecordField = effectiveOutputRecordField(ctx, resource, recordField);
            String record = ctx.getString(effectiveRecordField);

            if (record == null || record.isEmpty()) {
                record = ctx.getString("IN_RECORD");
            }
            if (record == null) {
                record = "";
            }

            ctx.setString(resource + "_LAST_WRITE", record);

            String path = resolveOutputPath(ctx, resource, effectiveRecordField);

            if (path == null || path.isEmpty()) {
                ctx.setInt("__LAST_IO_RC", 0);
                cc.setEqual();
                return;
            }

            try {
                java.nio.file.Path filePath = outputPath(path);
                java.nio.file.Path parent = filePath.getParent();

                if (parent != null) {
                    java.nio.file.Files.createDirectories(parent);
                }

                java.nio.file.Files.write(
                        filePath,
                        java.util.Arrays.asList(record),
                        java.nio.charset.StandardCharsets.UTF_8,
                        java.nio.file.StandardOpenOption.CREATE,
                        java.nio.file.StandardOpenOption.APPEND);

                ctx.setInt("__LAST_IO_RC", 0);
                cc.setEqual();

            } catch (Exception ex) {
                ctx.setString("IO_ERROR", ex.getMessage() == null ? ex.toString() : ex.getMessage());
                ctx.setInt("__LAST_IO_RC", 8);
                cc.setHigh();
            }
        }

        private static String effectiveInputRecordField(ExecutionContext ctx, String resource, String recordField) {
            if (recordField != null && !recordField.isEmpty()) {
                return recordField;
            }

            String explicit = ctx.getString("IO_RECORD_FIELD");
            if (!explicit.isEmpty()) {
                return explicit;
            }

            String text = resource == null ? "" : resource.toUpperCase();

            if (!ctx.getString("VSAMIN_PATH").isEmpty()) {
                return "IN_RECORD";
            }

            if (text.contains("RPL") || text.contains("CURRTX") || !ctx.getString("CURRTX_PATH").isEmpty()) {
                return "CURRTX";
            }

            if (!ctx.getString("IN_RECORD_PATH").isEmpty()) {
                return "IN_RECORD";
            }

            return "IN_RECORD";
        }

        private static String effectiveOutputRecordField(ExecutionContext ctx, String resource, String recordField) {
            if (recordField != null && !recordField.isEmpty()) {
                return recordField;
            }

            String explicit = ctx.getString("IO_OUTPUT_RECORD_FIELD");
            if (!explicit.isEmpty()) {
                return explicit;
            }

            if (!ctx.getString("OUT_RECORD").isEmpty()) {
                return "OUT_RECORD";
            }

            if (!ctx.getString("IN_RECORD").isEmpty()) {
                return "IN_RECORD";
            }

            if (!ctx.getString("CURRTX").isEmpty()) {
                return "CURRTX";
            }

            return "OUT_RECORD";
        }

        private static boolean contextAlreadyHasTransaction(ExecutionContext ctx) {
            return !ctx.getString("TXCUST").isEmpty()
                    || !ctx.getString("TXAMT").isEmpty()
                    || !ctx.getString("TXLIMIT").isEmpty()
                    || !ctx.getString("TXSTAT").isEmpty()
                    || !ctx.getString("TXTYPE").isEmpty();
        }

        private static void storeRecord(ExecutionContext ctx, String recordField, String record) {
            if (recordField != null && !recordField.isEmpty()) {
                ctx.setString(recordField, record);
            }

            if ("CURRTX".equalsIgnoreCase(recordField)) {
                parseCurrentTransactionRecord(ctx, record);
            }

            if ("IN_RECORD".equalsIgnoreCase(recordField) && ctx.getString("OUT_RECORD").isEmpty()) {
                ctx.setString("OUT_RECORD", record);
            }
        }

        private static void parseCurrentTransactionRecord(ExecutionContext ctx, String record) {
            /*
             * Local TXREAD fixed-width validation layout:
             * TXCARD   0-15   16 chars
             * TXCUST   16-25  10 chars
             * TXAMT    26-33   8 chars, cents
             * TXTYPE   34-35   2 chars
             * TXSTAT   36-36   1 char
             * TXLIMIT  37-44   8 chars, cents
             * TXFEE    45-52   8 chars, cents
             */
            String value = Memory.normalize(record, 53);

            ctx.setString("TXCARD", value.substring(0, 16).trim());
            ctx.setString("TXCUST", value.substring(16, 26).trim());
            setMoneyFromCents(ctx, "TXAMT", value.substring(26, 34));
            ctx.setString("TXTYPE", value.substring(34, 36).trim());
            ctx.setString("TXSTAT", value.substring(36, 37).trim());
            setMoneyFromCents(ctx, "TXLIMIT", value.substring(37, 45));
            setMoneyFromCents(ctx, "TXFEE", value.substring(45, 53));
        }

        private static void setMoneyFromCents(ExecutionContext ctx, String field, String centsText) {
            String cleaned = centsText == null ? "" : centsText.replaceAll("[^0-9+-]", "");

            if (cleaned.isEmpty() || "+".equals(cleaned) || "-".equals(cleaned)) {
                cleaned = "0";
            }

            java.math.BigDecimal value = new java.math.BigDecimal(cleaned)
                    .movePointLeft(2)
                    .setScale(2, java.math.RoundingMode.HALF_UP);

            ctx.setDecimal(field, value);
        }

        private static String resolveInputPath(ExecutionContext ctx, String resource, String recordField) {
            String safeResource = resource == null ? "" : resource;
            String safeRecordField = recordField == null ? "" : recordField;

            String resourcePath = ctx.getString(safeResource + "_PATH");
            if (!resourcePath.isEmpty()) {
                return resourcePath;
            }

            String fieldPath = ctx.getString(safeRecordField + "_PATH");
            if (!fieldPath.isEmpty()) {
                return fieldPath;
            }

            String resourceDdname = ctx.getString(safeResource + "_DDNAME");
            if (!resourceDdname.isEmpty()) {
                return "test_cases/ps/" + resourceDdname.toUpperCase() + ".txt";
            }

            String fieldDdname = ctx.getString(safeRecordField + "_DDNAME");
            if (!fieldDdname.isEmpty()) {
                return "test_cases/ps/" + fieldDdname.toUpperCase() + ".txt";
            }

            if ("CURRTX".equalsIgnoreCase(safeRecordField)) {
                return "test_cases/ps/INVSAM.txt";
            }

            if ("IN_RECORD".equalsIgnoreCase(safeRecordField)) {
                return "test_cases/ps/VSAMIN.txt";
            }

            if ("INRPL".equalsIgnoreCase(safeResource) || "INACB".equalsIgnoreCase(safeResource)) {
                return "test_cases/ps/INVSAM.txt";
            }

            if (safeResource.matches("[A-Za-z0-9_#$@]+")) {
                return "test_cases/ps/" + safeResource.toUpperCase() + ".txt";
            }

            return "";
        }


        private static String resolveOutputPath(ExecutionContext ctx, String resource, String recordField) {
            String safeResource = resource == null ? "" : resource;
            String safeRecordField = recordField == null ? "" : recordField;

            String resourcePath = ctx.getString(safeResource + "_PATH");
            if (!resourcePath.isEmpty()) {
                return resourcePath;
            }

            String fieldPath = ctx.getString(safeRecordField + "_PATH");
            if (!fieldPath.isEmpty()) {
                return fieldPath;
            }

            String resourceDdname = ctx.getString(safeResource + "_DDNAME");
            if (!resourceDdname.isEmpty()) {
                return "test_cases/ps/" + resourceDdname.toUpperCase() + ".txt";
            }

            String fieldDdname = ctx.getString(safeRecordField + "_DDNAME");
            if (!fieldDdname.isEmpty()) {
                return "test_cases/ps/" + fieldDdname.toUpperCase() + ".txt";
            }

            if ("LOGBUFF".equalsIgnoreCase(safeRecordField)
                    || "OUTRPL".equalsIgnoreCase(safeResource)
                    || "OUTACB".equalsIgnoreCase(safeResource)) {
                return "test_cases/ps/OUTVSAM.txt";
            }

            if ("OUT_RECORD".equalsIgnoreCase(safeRecordField)
                    || "OUTFILE".equalsIgnoreCase(safeResource)) {
                return "test_cases/ps/VSAMOUT.txt";
            }

            if (safeResource.matches("[A-Za-z0-9_#$@]+")) {
                return "test_cases/ps/" + safeResource.toUpperCase() + ".txt";
            }

            return "";
        }


        private static String sanitizeKey(String value) {
            if (value == null || value.isEmpty()) {
                return "RESOURCE";
            }
            return value.replaceAll("[^A-Za-z0-9_#$@]", "_");
        }

        private static java.nio.file.Path existingPath(String path) {
            java.nio.file.Path direct = java.nio.file.Paths.get(path);

            if (java.nio.file.Files.exists(direct)) {
                return direct;
            }

            java.nio.file.Path parentRelative = java.nio.file.Paths.get("..", path);

            if (java.nio.file.Files.exists(parentRelative)) {
                return parentRelative;
            }

            return direct;
        }

        private static java.nio.file.Path outputPath(String path) {
            java.nio.file.Path direct = java.nio.file.Paths.get(path);
            java.nio.file.Path parent = direct.getParent();

            if (parent != null && java.nio.file.Files.exists(parent)) {
                return direct;
            }

            return java.nio.file.Paths.get("..", path);
        }
    }

    public static class Program {
        public static void save(Registers registers) {
            // Generated runtime placeholder for SAVE macro.
        }
    }

    public static class Branch {

        public static final int MAX_LOOP_ITERATIONS = 100000;

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

        public static boolean isNotHigh(ConditionCode cc) {
            return cc.get() != ConditionCode.HIGH;
       }

        public static boolean isNotLow(ConditionCode cc) {
            return cc.get() != ConditionCode.LOW;
        }

        public static boolean isOverflow(ConditionCode cc) {
            return cc.get() == ConditionCode.OVERFLOW;
        }

        public static boolean isNotOverflow(ConditionCode cc) {
            return cc.get() != ConditionCode.OVERFLOW;
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

        source_lines = self.module_source_lines.get(module.upper(), [])
        called_modules = self._discover_called_modules(source_lines)

        if called_modules:
            translated_code = self._orchestrator_module_code(module, called_modules)
        else:
            translated_code = self._translated_module_code(module)

        default_return = (
            f'        return ModuleResult.rc({default_rc}, "{module} executed as generated candidate");'
        )

        if self._has_unconditional_terminal_return(translated_code):
            default_return = ""

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

{default_return}

    }}
}}
"""

    def _discover_called_modules(self, lines):
        """
        Discover called modules from HLASM source without hardcoding business names.

        This handles VCON/call-reference patterns such as:
            DC A(=V(CUSTVAL))
            L  15,=V(CUSTVAL)
            LOAD EP=CUSTVAL
            CALL CUSTVAL

        Returns modules in first-seen source order.
        """
        known_modules = {name.upper() for name in self._discover_modules()}
        called = []

        def add_candidate(name):
            candidate = str(name).strip().upper()
            candidate = re.sub(r"[^A-Z0-9_#$@].*$", "", candidate)

            if not candidate:
                return

            if candidate not in known_modules:
                return

            if candidate not in called:
                called.append(candidate)

        for line in lines:
            upper = line.upper()

            for match in re.finditer(r"(?:=)?V\(([A-Z0-9_#$@]+)\)", upper):
                add_candidate(match.group(1))

            match = re.search(r"\bLOAD\b.*\bEP=([A-Z0-9_#$@]+)", upper)
            if match:
                add_candidate(match.group(1))

            match = re.search(r"\bCALL\s+\(?([A-Z0-9_#$@]+)\)?", upper)
            if match:
                add_candidate(match.group(1))

        return called

    def _discover_reject_path_calls(self, lines):
        """
        Discover modules called inside REJECT_PATH or similar reject labels.

        This keeps the orchestration mostly generic. If the HLASM contains:
            BNZ REJECT_PATH
            ...
            REJECT_PATH DS 0H
               L 15,=V(AUTHDEC)
               BALR 14,15

        this returns the module called from that reject path.
        """
        reject_labels = set()

        for line in lines:
            upper = line.upper().strip()
            match = re.search(r"\bB(?:NZ|NE)\s+([A-Z0-9_#$@]+)", upper)
            if match:
                reject_labels.add(match.group(1))

        if not reject_labels:
            return []

        called = []
        inside_reject_block = False
        known_modules = {name.upper() for name in self._discover_modules()}

        for line in lines:
            stripped = line.strip()
            upper = stripped.upper()
            parts = stripped.split()

            if parts and parts[0].upper() in reject_labels:
                inside_reject_block = True
                continue

            if inside_reject_block and len(parts) >= 2:
                first = parts[0].upper()
                second = parts[1].upper()

                if first not in reject_labels and second in {"DS", "CSECT", "EQU"}:
                    inside_reject_block = False

            if not inside_reject_block:
                continue

            for match in re.finditer(r"(?:=)?V\(([A-Z0-9_#$@]+)\)", upper):
                candidate = match.group(1).strip().upper()
                if candidate in known_modules and candidate not in called:
                    called.append(candidate)

            match = re.search(r"\bLOAD\b.*\bEP=([A-Z0-9_#$@]+)", upper)
            if match:
                candidate = match.group(1).strip().upper()
                if candidate in known_modules and candidate not in called:
                    called.append(candidate)

            match = re.search(r"\bCALL\s+\(?([A-Z0-9_#$@]+)\)?", upper)
            if match:
                candidate = match.group(1).strip().upper()
                if candidate in known_modules and candidate not in called:
                    called.append(candidate)

        return called

    def _module_has_reject_branch_after_call(self, lines, called_module):
        """
        Detect whether a called module is followed by an LTR/BNZ-style reject check.

        Example:
            L 15,=V(MODULE)
            BALR 14,15
            LTR 15,15
            BNZ REJECT_PATH
        """
        module = called_module.upper()

        for idx, line in enumerate(lines):
            upper = line.upper()

            if f"=V({module})" not in upper and f"V({module})" not in upper:
                continue

            lookahead = " ".join(
                candidate.upper().strip()
                for candidate in lines[idx + 1 : idx + 7]
            )

            if "LTR" in lookahead and re.search(r"\bB(?:NZ|NE)\b", lookahead):
                return True

        return False

    def _orchestrator_module_code(self, module, called_modules):
        """
        Generate Java orchestration for driver modules.

        This method avoids hardcoding CUSTVAL/LIMITCHK/AUTHDEC names.
        It uses HLASM source clues:
          - called_modules comes from =V(MODULE)/CALL references.
          - reject path calls are discovered from labels reached by BNZ/BNE.
          - modules followed by LTR/BNZ are treated as validation-gated calls.
        """
        source_lines = self.module_source_lines.get(module.upper(), [])
        reject_modules = self._discover_reject_path_calls(source_lines)
        reject_set = set(reject_modules)

        normal_called_modules = [
            called for called in called_modules
            if called.upper() not in reject_set
        ]

        java_lines = [
            "        // Application orchestration discovered from HLASM module call references.",
            f"        // Driver module: {module}",
            "        ModuleResult result = ModuleResult.rc(0, \"Application orchestration started\");",
            "        int overallRc = 0;",
            "",
        ]

        for called_module in normal_called_modules:
            class_name = self._to_class_name(called_module)
            is_reject_checked = self._module_has_reject_branch_after_call(
                source_lines,
                called_module,
            )

            java_lines.append(f"        // Execute translated module: {called_module}")
            java_lines.append(f"        result = new {class_name}().execute(ctx);")

            if is_reject_checked:
                java_lines.append("        if (!result.isOk()) {")
                java_lines.append("            overallRc = result.getReturnCode();")

                if reject_modules:
                    for reject_module in reject_modules:
                        reject_class = self._to_class_name(reject_module)
                        java_lines.append(
                            f"            // Reject-path module discovered from HLASM: {reject_module}"
                        )
                        java_lines.append(f"            new {reject_class}().execute(ctx);")
                else:
                    java_lines.append(
                        "            // No reject-path module discovered in HLASM source."
                    )

                java_lines.append(
                    f'            return ModuleResult.rc(overallRc, "{module} rejected by translated validation path");'
                )
                java_lines.append("        }")
            else:
                java_lines.append("        if (overallRc == 0 && result.getReturnCode() != 0) {")
                java_lines.append("            overallRc = result.getReturnCode();")
                java_lines.append("        }")

            java_lines.append("")

        # Success path final decision.
        # Example: after FEECALC, AUTHDEC should still run to populate AUTHSTAT=APPRV.
        for reject_module in reject_modules:
            reject_class = self._to_class_name(reject_module)
            java_lines.append(
                f"        // Final decision module discovered from HLASM: {reject_module}"
            )
            java_lines.append(f"        new {reject_class}().execute(ctx);")
            java_lines.append("")

        java_lines.append(
            f'        return ModuleResult.rc(overallRc, "{module} orchestration completed");'
        )

        return "\n".join(java_lines)

    def _has_unconditional_terminal_return(self, translated_code):
        meaningful_lines = [
            line.strip()
            for line in translated_code.splitlines()
            if line.strip() and not line.strip().startswith("//")
        ]

        if not meaningful_lines:
            return False

        return meaningful_lines[-1].startswith("return ModuleResult.rc")

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

        translated_lines = translator.translate_block_flow(lines)

        java_lines = []
        java_lines.append("        // Branch-aware translated instruction candidates from HLASM source.")

        for translated in translated_lines:
            java_lines.append(f"        {translated}")

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
