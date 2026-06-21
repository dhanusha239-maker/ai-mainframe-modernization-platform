import os
import re
from collections import defaultdict


class ASMScanner:
    """
    Repository-wide ASM scanner.

    Responsibilities:
    -----------------
    1. Discover modules (CSECT)
    2. Discover call relationships
    3. Report missing modules

    Future:
    -------
    Add new call patterns in CALL_PATTERNS list.
    """

    def __init__(self, asm_folder="HLASM"):

        self.asm_folder = asm_folder

        # Module -> file path
        self.modules = {}

        # Module -> called modules
        self.call_graph = defaultdict(set)

        self.missing_modules = set()

        #
        # Add future patterns here.
        #
        self.CALL_PATTERNS = [

            # =V(MODULE)
            (
                "VCON",
                re.compile(
                    r"=V\(([A-Z0-9#$@]+)\)",
                    re.IGNORECASE,
                ),
            ),

            # LOAD EP=MODULE
            (
                "LOAD_EP",
                re.compile(
                    r"LOAD\s+EP=([A-Z0-9#$@]+)",
                    re.IGNORECASE,
                ),
            ),

            # LINK EP=MODULE
            (
                "LINK_EP",
                re.compile(
                    r"LINK\s+EP=([A-Z0-9#$@]+)",
                    re.IGNORECASE,
                ),
            ),

            # ATTACH EP=MODULE
            (
                "ATTACH_EP",
                re.compile(
                    r"ATTACH\s+EP=([A-Z0-9#$@]+)",
                    re.IGNORECASE,
                ),
            ),

            # CALL MODULE
            (
                "CALL",
                re.compile(
                    r"\bCALL\s+([A-Z0-9#$@]+)",
                    re.IGNORECASE,
                ),
            ),

            #
            # Direct BAL
            #
            (
                "BAL",
                re.compile(
                    r"\bBAL\s+\d+\s*,\s*([A-Z0-9#$@]+)",
                    re.IGNORECASE,
                ),
            ),

            #
            # Direct BAS
            #
            (
                "BAS",
                re.compile(
                    r"\bBAS\s+\d+\s*,\s*([A-Z0-9#$@]+)",
                    re.IGNORECASE,
                ),
            ),
        ]

    def scan_repository(self):

        for filename in os.listdir(self.asm_folder):

            if not (
                filename.endswith(".asm")
                or filename.endswith(".asm.txt")
            ):
                continue

            full_path = os.path.join(
                self.asm_folder,
                filename,
            )

            self.parse_file(full_path)

        self.find_missing_modules()

    def parse_file(self, filepath):

        current_module = None

        with open(
            filepath,
            "r",
            encoding="utf-8",
        ) as f:

            for raw_line in f:

                line = raw_line.strip()

                #
                # Detect CSECT
                #
                csect_match = re.match(
                    r"^([A-Z0-9#$@]+)\s+CSECT",
                    line,
                    re.IGNORECASE,
                )

                if csect_match:

                    current_module = (
                        csect_match.group(1)
                        .upper()
                    )

                    self.modules[
                        current_module
                    ] = filepath

                    continue

                if current_module is None:
                    continue

                #
                # Detect all call types
                #
                self.extract_calls(
                    current_module,
                    line,
                )

    def extract_calls(
        self,
        source_module,
        line,
    ):

        for pattern_name, regex in self.CALL_PATTERNS:

            matches = regex.findall(line)

            if not matches:
                continue

            for target in matches:

                self.call_graph[
                    source_module
                ].add(
                    target.upper()
                )

    def find_missing_modules(self):

        discovered = set(
            self.modules.keys()
        )

        for source, targets in (
            self.call_graph.items()
        ):

            for target in targets:

                if target not in discovered:

                    self.missing_modules.add(
                        target
                    )

    def print_report(self):

        print("\nMODULES")
        print("-" * 50)

        for module in sorted(
            self.modules
        ):
            print(module)

        print("\nCALL GRAPH")
        print("-" * 50)

        for source in sorted(
            self.call_graph
        ):

            targets = sorted(
                self.call_graph[source]
            )

            print(
                f"{source} -> "
                + ", ".join(targets)
            )

        print("\nMISSING MODULES")
        print("-" * 50)

        if not self.missing_modules:
            print("None")
        else:
            for module in sorted(
                self.missing_modules
            ):
                print(module)