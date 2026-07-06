## test_scanner.py
        │
        ▼
Tests asm_scanner.py only
##### 
test_cfg_builder.py
        │
        ▼
Uses asm_scanner.py
        │
        ▼
Tests cfg_builder.py

#####
test_pdg_builder.py
        │
        ▼
Uses asm_scanner.py
        │
        ▼
Uses cfg_builder.py
        │
        ▼
Tests pdg_builder.py
#####

and finally:

impact_analyzer.py
        │
        ▼
asm_scanner.py
        │
        ▼
cfg_builder.py
        │
        ▼
pdg_builder.py
        │
        ▼
analysis_report.json