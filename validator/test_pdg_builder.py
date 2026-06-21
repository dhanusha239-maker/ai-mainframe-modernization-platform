from pdg_builder import PDGBuilder

builder = PDGBuilder("HLASM")
builder.scan_repository()
builder.print_report()
builder.export_json("analysis_report.json")

print("\nSaved JSON report to analysis_report.json")