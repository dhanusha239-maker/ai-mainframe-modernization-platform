from cfg_builder import CFGBuilder

builder = CFGBuilder("HLASM")
builder.scan_repository()
builder.print_report()