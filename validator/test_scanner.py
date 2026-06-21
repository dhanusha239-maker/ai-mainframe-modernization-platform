from asm_scanner import ASMScanner

scanner = ASMScanner("HLASM")

scanner.scan_repository()

scanner.print_report()