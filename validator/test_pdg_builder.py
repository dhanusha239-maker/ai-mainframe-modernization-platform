from pdg_builder import PDGBuilder

builder = PDGBuilder("HLASM")
builder.scan_repository()
builder.print_report()