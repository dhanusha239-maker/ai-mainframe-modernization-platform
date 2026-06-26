import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class BehaviorTestRunner {

    public static void main(String[] args) throws Exception {
        List<java.util.Map<String, String>> results = new ArrayList<>();

        results.add(runCase0());
        results.add(runCase1());
        results.add(runCase2());

        writeJson(results);
    }

    private static void writeJson(List<java.util.Map<String, String>> results) throws IOException {
        try (FileWriter writer = new FileWriter("java_behavior_output.json")) {
            writer.write("[\n");

            for (int i = 0; i < results.size(); i++) {
                java.util.Map<String, String> item = results.get(i);

                writer.write("  {\n");

                int j = 0;
                for (java.util.Map.Entry<String, String> entry : item.entrySet()) {
                    writer.write("    \"" + escape(entry.getKey()) + "\": \"" + escape(entry.getValue()) + "\"");

                    if (j < item.size() - 1) {
                        writer.write(",");
                    }

                    writer.write("\n");
                    j++;
                }

                writer.write("  }");

                if (i < results.size() - 1) {
                    writer.write(",");
                }

                writer.write("\n");
            }

            writer.write("]\n");
        }
    }

    private static String escape(String value) {
        if (value == null) {
            return "";
        }

        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }


    private static java.util.Map<String, String> runCase0() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("TXCUST", "CUST000001");
        ctx.setString("ERRCODE", "0000");


        AssemblerModule module = new Custval();
        ModuleResult result = module.execute(ctx);
        int rc = result.getReturnCode();


        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "CUSTVAL_VALID_001");
        output.put("module", "CUSTVAL");
        output.put("RC", String.valueOf(rc));

        output.put("ERRCODE", ctx.getString("ERRCODE"));
        output.put("AUTHSTAT", ctx.getString("AUTHSTAT"));
        output.put("TXFEE", ctx.getString("TXFEE"));
        output.put("TXAMT", ctx.getString("TXAMT"));
        output.put("TXLIMIT", ctx.getString("TXLIMIT"));
        output.put("TXCUST", ctx.getString("TXCUST"));
        output.put("TXSTAT", ctx.getString("TXSTAT"));
        output.put("TXTYPE", ctx.getString("TXTYPE"));

        return output;
    }


    private static java.util.Map<String, String> runCase1() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("TXCUST", "BAD000001");


        AssemblerModule module = new Custval();
        ModuleResult result = module.execute(ctx);
        int rc = result.getReturnCode();


        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "CUSTVAL_INVALID_001");
        output.put("module", "CUSTVAL");
        output.put("RC", String.valueOf(rc));

        output.put("ERRCODE", ctx.getString("ERRCODE"));
        output.put("AUTHSTAT", ctx.getString("AUTHSTAT"));
        output.put("TXFEE", ctx.getString("TXFEE"));
        output.put("TXAMT", ctx.getString("TXAMT"));
        output.put("TXLIMIT", ctx.getString("TXLIMIT"));
        output.put("TXCUST", ctx.getString("TXCUST"));
        output.put("TXSTAT", ctx.getString("TXSTAT"));
        output.put("TXTYPE", ctx.getString("TXTYPE"));

        return output;
    }


    private static java.util.Map<String, String> runCase2() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setDecimal("TXAMT", new java.math.BigDecimal("750.00"));
        ctx.setDecimal("TXLIMIT", new java.math.BigDecimal("500.00"));


        AssemblerModule module = new Limitchk();
        ModuleResult result = module.execute(ctx);
        int rc = result.getReturnCode();


        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "LIMITCHK_REJECT_001");
        output.put("module", "LIMITCHK");
        output.put("RC", String.valueOf(rc));

        output.put("ERRCODE", ctx.getString("ERRCODE"));
        output.put("AUTHSTAT", ctx.getString("AUTHSTAT"));
        output.put("TXFEE", ctx.getString("TXFEE"));
        output.put("TXAMT", ctx.getString("TXAMT"));
        output.put("TXLIMIT", ctx.getString("TXLIMIT"));
        output.put("TXCUST", ctx.getString("TXCUST"));
        output.put("TXSTAT", ctx.getString("TXSTAT"));
        output.put("TXTYPE", ctx.getString("TXTYPE"));

        return output;
    }

}
