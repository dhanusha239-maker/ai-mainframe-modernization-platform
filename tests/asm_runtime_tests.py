import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
JAVA_DIR = PROJECT_ROOT / "generated_java"


TEST_RUNNER = r"""
import java.math.BigDecimal;

public class AsmRuntimeTestRunner {

    private static int passed = 0;
    private static int failed = 0;

    public static void main(String[] args) {
        testMvcLiteral();
        testMvcTruncate();
        testMvcPad();
        testClcEqual();
        testClcLow();
        testCli();
        testZap();
        testAp();
        testSp();
        testMp();
        testDp();
        testBct();

        System.out.println();
        System.out.println("ASM RUNTIME TEST SUMMARY");
        System.out.println("----------------------------------------");
        System.out.println("Passed: " + passed);
        System.out.println("Failed: " + failed);

        if (failed > 0) {
            System.exit(1);
        }
    }

    private static void assertEquals(String name, Object expected, Object actual) {
        if ((expected == null && actual == null)
                || (expected != null && expected.equals(actual))) {
            System.out.println(name + " ........ PASS");
            passed++;
        } else {
            System.out.println(name + " ........ FAIL");
            System.out.println("  expected: " + expected);
            System.out.println("  actual  : " + actual);
            failed++;
        }
    }

    private static void testMvcLiteral() {
        ExecutionContext ctx = new ExecutionContext();
        AsmRuntime.Memory.mvcLiteral(ctx, "ERRCODE", 4, "E001");

        assertEquals("MVC literal", "E001", ctx.getString("ERRCODE"));
    }

    private static void testMvcTruncate() {
        ExecutionContext ctx = new ExecutionContext();
        ctx.setString("SOURCE", "ABCDEFG");

        AsmRuntime.Memory.mvc(ctx, "TARGET", 4, "SOURCE");

        assertEquals("MVC truncate", "ABCD", ctx.getString("TARGET"));
    }

    private static void testMvcPad() {
        ExecutionContext ctx = new ExecutionContext();
        ctx.setString("SOURCE", "AB");

        AsmRuntime.Memory.mvc(ctx, "TARGET", 4, "SOURCE");

        assertEquals("MVC pad", "AB  ", ctx.getString("TARGET"));
    }

    private static void testClcEqual() {
        ExecutionContext ctx = new ExecutionContext();
        AsmRuntime.ConditionCode cc = new AsmRuntime.ConditionCode();

        ctx.setString("A", "TEST");

        AsmRuntime.Memory.clcLiteral(ctx, "A", 4, "TEST", cc);

        assertEquals("CLC equal", AsmRuntime.ConditionCode.EQUAL, cc.get());
    }

    private static void testClcLow() {
        ExecutionContext ctx = new ExecutionContext();
        AsmRuntime.ConditionCode cc = new AsmRuntime.ConditionCode();

        ctx.setString("A", "ABCD");

        AsmRuntime.Memory.clcLiteral(ctx, "A", 4, "ZZZZ", cc);

        assertEquals("CLC low", AsmRuntime.ConditionCode.LOW, cc.get());
    }

    private static void testCli() {
        ExecutionContext ctx = new ExecutionContext();
        AsmRuntime.ConditionCode cc = new AsmRuntime.ConditionCode();

        ctx.setString("TXSTAT", "A");

        AsmRuntime.Memory.cli(ctx, "TXSTAT", 'A', cc);

        assertEquals("CLI equal", AsmRuntime.ConditionCode.EQUAL, cc.get());
    }

    private static void testZap() {
        ExecutionContext ctx = new ExecutionContext();
        AsmRuntime.ConditionCode cc = new AsmRuntime.ConditionCode();

        ctx.setDecimal("SOURCE", new BigDecimal("123.45"));

        AsmRuntime.Packed.zap(ctx, "TARGET", "SOURCE", 7, 2, cc);

        assertEquals("ZAP", new BigDecimal("123.45"), ctx.getDecimal("TARGET"));
    }

    private static void testAp() {
        ExecutionContext ctx = new ExecutionContext();
        AsmRuntime.ConditionCode cc = new AsmRuntime.ConditionCode();

        ctx.setDecimal("A", new BigDecimal("100.00"));
        ctx.setDecimal("B", new BigDecimal("25.50"));

        AsmRuntime.Packed.ap(ctx, "A", "B", 7, 2, cc);

        assertEquals("AP", new BigDecimal("125.50"), ctx.getDecimal("A"));
    }

    private static void testSp() {
        ExecutionContext ctx = new ExecutionContext();
        AsmRuntime.ConditionCode cc = new AsmRuntime.ConditionCode();

        ctx.setDecimal("A", new BigDecimal("100.00"));
        ctx.setDecimal("B", new BigDecimal("25.50"));

        AsmRuntime.Packed.sp(ctx, "A", "B", 7, 2, cc);

        assertEquals("SP", new BigDecimal("74.50"), ctx.getDecimal("A"));
    }

    private static void testMp() {
        ExecutionContext ctx = new ExecutionContext();
        AsmRuntime.ConditionCode cc = new AsmRuntime.ConditionCode();

        ctx.setDecimal("A", new BigDecimal("10.00"));
        ctx.setDecimal("B", new BigDecimal("2.50"));

        AsmRuntime.Packed.mp(ctx, "A", "B", 7, 2, cc);

        assertEquals("MP", new BigDecimal("25.00"), ctx.getDecimal("A"));
    }

    private static void testDp() {
        ExecutionContext ctx = new ExecutionContext();
        AsmRuntime.ConditionCode cc = new AsmRuntime.ConditionCode();

        ctx.setDecimal("A", new BigDecimal("10.00"));
        ctx.setDecimal("B", new BigDecimal("4.00"));

        AsmRuntime.Packed.dp(ctx, "A", "B", 7, 2, cc);

        assertEquals("DP", new BigDecimal("2.50"), ctx.getDecimal("A"));
    }

    private static void testBct() {
        AsmRuntime.Registers registers = new AsmRuntime.Registers();

        registers.set(5, 2);

        boolean branch1 = AsmRuntime.Branch.bct(registers, 5);
        boolean branch2 = AsmRuntime.Branch.bct(registers, 5);

        assertEquals("BCT first branch", true, branch1);
        assertEquals("BCT second branch", false, branch2);
    }
}
"""


def main():
    if not JAVA_DIR.exists():
        raise FileNotFoundError(f"generated_java folder not found: {JAVA_DIR}")

    runner_path = JAVA_DIR / "AsmRuntimeTestRunner.java"
    runner_path.write_text(TEST_RUNNER.strip() + "\n", encoding="utf-8")

    print("Compiling Java runtime tests...")
    compile_result = subprocess.run(
        ["javac", "*.java"],
        cwd=JAVA_DIR,
        shell=True,
        capture_output=True,
        text=True,
    )

    if compile_result.returncode != 0:
        print(compile_result.stdout)
        print(compile_result.stderr)
        raise SystemExit(1)

    print("Running Java runtime tests...")
    run_result = subprocess.run(
        ["java", "AsmRuntimeTestRunner"],
        cwd=JAVA_DIR,
        shell=True,
        capture_output=True,
        text=True,
    )

    print(run_result.stdout)

    if run_result.returncode != 0:
        print(run_result.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()