def compare_outputs(hlasm_output, java_output):

    if hlasm_output == java_output:
        return "PASS"
    else:
        return "FAIL"