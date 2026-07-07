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
        results.add(runCase3());
        results.add(runCase4());
        results.add(runCase5());
        results.add(runCase6());
        results.add(runCase7());
        results.add(runCase8());
        results.add(runCase9());
        results.add(runCase10());
        results.add(runCase11());
        results.add(runCase12());
        results.add(runCase13());
        results.add(runCase14());
        results.add(runCase15());
        results.add(runCase16());

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
        ctx.setString("ERRCODE", "0000");


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

        ctx.setString("TXSTAT", "A");
        ctx.setString("ERRCODE", "0000");


                AssemblerModule module = new Cardstat();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "CARDSTAT_ACTIVE_001");
        output.put("module", "CARDSTAT");
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


    private static java.util.Map<String, String> runCase3() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("TXSTAT", "B");
        ctx.setString("ERRCODE", "0000");


                AssemblerModule module = new Cardstat();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "CARDSTAT_BLOCKED_001");
        output.put("module", "CARDSTAT");
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


    private static java.util.Map<String, String> runCase4() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setDecimal("TXAMT", new java.math.BigDecimal("250.00"));
        ctx.setDecimal("TXLIMIT", new java.math.BigDecimal("500.00"));
        ctx.setString("ERRCODE", "0000");


                AssemblerModule module = new Limitchk();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "LIMITCHK_APPROVE_001");
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


    private static java.util.Map<String, String> runCase5() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setDecimal("TXAMT", new java.math.BigDecimal("750.00"));
        ctx.setDecimal("TXLIMIT", new java.math.BigDecimal("500.00"));
        ctx.setString("ERRCODE", "0000");


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


    private static java.util.Map<String, String> runCase6() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setDecimal("TXAMT", new java.math.BigDecimal("100.00"));
        ctx.setString("TXTYPE", "PO");
        ctx.setString("ERRCODE", "0000");


                AssemblerModule module = new Frdchk();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "FRDCHK_NORMAL_001");
        output.put("module", "FRDCHK");
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


    private static java.util.Map<String, String> runCase7() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setDecimal("TXAMT", new java.math.BigDecimal("600.00"));
        ctx.setString("TXTYPE", "RE");
        ctx.setString("ERRCODE", "0000");


                AssemblerModule module = new Frdchk();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "FRDCHK_REMOTE_HIGH_001");
        output.put("module", "FRDCHK");
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


    private static java.util.Map<String, String> runCase8() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setDecimal("TXAMT", new java.math.BigDecimal("100.00"));
        ctx.setDecimal("TXFEE", new java.math.BigDecimal("0.00"));
        ctx.setString("ERRCODE", "0000");


                AssemblerModule module = new Feecalc();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "FEECALC_BASIC_001");
        output.put("module", "FEECALC");
        output.put("RC", String.valueOf(rc));

        output.put("TXFEE", ctx.getString("TXFEE"));
        output.put("ERRCODE", ctx.getString("ERRCODE"));
        output.put("AUTHSTAT", ctx.getString("AUTHSTAT"));
        output.put("TXAMT", ctx.getString("TXAMT"));
        output.put("TXLIMIT", ctx.getString("TXLIMIT"));
        output.put("TXCUST", ctx.getString("TXCUST"));
        output.put("TXSTAT", ctx.getString("TXSTAT"));
        output.put("TXTYPE", ctx.getString("TXTYPE"));

        return output;
    }


    private static java.util.Map<String, String> runCase9() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("ERRCODE", "0000");
        ctx.setString("AUTHSTAT", "");


                AssemblerModule module = new Authdec();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "AUTHDEC_APPROVE_001");
        output.put("module", "AUTHDEC");
        output.put("RC", String.valueOf(rc));

        output.put("AUTHSTAT", ctx.getString("AUTHSTAT"));
        output.put("ERRCODE", ctx.getString("ERRCODE"));
        output.put("TXFEE", ctx.getString("TXFEE"));
        output.put("TXAMT", ctx.getString("TXAMT"));
        output.put("TXLIMIT", ctx.getString("TXLIMIT"));
        output.put("TXCUST", ctx.getString("TXCUST"));
        output.put("TXSTAT", ctx.getString("TXSTAT"));
        output.put("TXTYPE", ctx.getString("TXTYPE"));

        return output;
    }


    private static java.util.Map<String, String> runCase10() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("ERRCODE", "E003");
        ctx.setString("AUTHSTAT", "");


                AssemblerModule module = new Authdec();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "AUTHDEC_REJECT_001");
        output.put("module", "AUTHDEC");
        output.put("RC", String.valueOf(rc));

        output.put("AUTHSTAT", ctx.getString("AUTHSTAT"));
        output.put("ERRCODE", ctx.getString("ERRCODE"));
        output.put("TXFEE", ctx.getString("TXFEE"));
        output.put("TXAMT", ctx.getString("TXAMT"));
        output.put("TXLIMIT", ctx.getString("TXLIMIT"));
        output.put("TXCUST", ctx.getString("TXCUST"));
        output.put("TXSTAT", ctx.getString("TXSTAT"));
        output.put("TXTYPE", ctx.getString("TXTYPE"));

        return output;
    }


    private static java.util.Map<String, String> runCase11() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("TXCUST", "CUST000001");
        ctx.setString("TXSTAT", "A");
        ctx.setDecimal("TXAMT", new java.math.BigDecimal("100.00"));
        ctx.setDecimal("TXLIMIT", new java.math.BigDecimal("500.00"));
        ctx.setString("TXTYPE", "PO");
        ctx.setString("ERRCODE", "0000");
        ctx.setString("AUTHSTAT", "");
        ctx.setDecimal("TXFEE", new java.math.BigDecimal("0.00"));


                AssemblerModule application = new Maindrv();
                ModuleResult result = application.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "APP_APPROVAL_FLOW_001");
        output.put("module", "MAINDRV");
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


    private static java.util.Map<String, String> runCase12() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("IO_FORCE_READ", "true");
        ctx.setString("INRPL_PATH", "test_cases/ps/INVSAM.txt");
        ctx.setString("INVSAM_PATH", "test_cases/ps/INVSAM.txt");
        ctx.setString("CURRTX_PATH", "test_cases/ps/INVSAM.txt");
        ctx.setString("ERRCODE", "0000");


                AssemblerModule module = new Txread();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "TXREAD_LOCAL_PS_001");
        output.put("module", "TXREAD");
        output.put("RC", String.valueOf(rc));

        output.put("TXCUST", ctx.getString("TXCUST"));
        output.put("TXSTAT", ctx.getString("TXSTAT"));
        output.put("TXAMT", ctx.getString("TXAMT"));
        output.put("TXLIMIT", ctx.getString("TXLIMIT"));
        output.put("TXTYPE", ctx.getString("TXTYPE"));
        output.put("TXFEE", ctx.getString("TXFEE"));
        output.put("ERRCODE", ctx.getString("ERRCODE"));
        output.put("AUTHSTAT", ctx.getString("AUTHSTAT"));

        return output;
    }


    private static java.util.Map<String, String> runCase13() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("IO_FORCE_READ", "true");
        ctx.setString("IO_RECORD_FIELD", "IN_RECORD");
        ctx.setString("IO_OUTPUT_RECORD_FIELD", "OUT_RECORD");
        ctx.setString("INVSAM_PATH", "test_cases/ps/VSAMIN.txt");
        ctx.setString("VSAMIN_PATH", "test_cases/ps/VSAMIN.txt");
        ctx.setString("OUTFILE_PATH", "test_cases/ps/VSAMOUT.txt");
        ctx.setString("OUTDD_PATH", "test_cases/ps/VSAMOUT.txt");


                AssemblerModule module = new Vsampack();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "VSAMPACK_LOCAL_PS_SMOKE_001");
        output.put("module", "VSAMPACK");
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


    private static java.util.Map<String, String> runCase14() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("COUNT", "5");
        ctx.setString("TOTAL", "0");


                AssemblerModule module = new Bctcount();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "BCTCOUNT_COUNT_5_001");
        output.put("module", "BCTCOUNT");
        output.put("RC", String.valueOf(rc));

        output.put("TOTAL", ctx.getString("TOTAL"));
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


    private static java.util.Map<String, String> runCase15() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("COUNT", "3");
        ctx.setString("TOTAL", "0");


                AssemblerModule module = new Bctcount();
                ModuleResult result = module.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "BCTCOUNT_COUNT_3_001");
        output.put("module", "BCTCOUNT");
        output.put("RC", String.valueOf(rc));

        output.put("TOTAL", ctx.getString("TOTAL"));
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


    private static java.util.Map<String, String> runCase16() {
        ExecutionContext ctx = new ExecutionContext();

        ctx.setString("IO_FORCE_READ", "true");
        ctx.setString("INRPL_PATH", "test_cases/ps/INVSAM.txt");
        ctx.setString("INVSAM_PATH", "test_cases/ps/INVSAM.txt");
        ctx.setString("CURRTX_PATH", "test_cases/ps/INVSAM.txt");
        ctx.setString("OUTRPL_PATH", "test_cases/ps/OUTVSAM.txt");
        ctx.setString("OUTACB_PATH", "test_cases/ps/OUTVSAM.txt");
        ctx.setString("LOGBUFF_PATH", "test_cases/ps/OUTVSAM.txt");
        ctx.setString("ERRCODE", "0000");


                AssemblerModule application = new Maindrv();
                ModuleResult result = application.execute(ctx);
                int rc = result.getReturnCode();
        

        java.util.Map<String, String> output = new java.util.LinkedHashMap<>();
        output.put("case_id", "MAINDRV_DDNAME_FILE_FLOW_001");
        output.put("module", "MAINDRV");
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
