import re
from collections import defaultdict

class HLASMGraphBuilder:

    def __init__(self):
        self.call_graph = defaultdict(list)
        self.current_module = None
        self.modules = set()

    # Detect module name (CSECT)
    def detect_module(self, line):
        match = re.match(r"^(\w+)\s+CSECT", line)
        if match:
            return match.group(1)
        return None

    # Detect calls (BALR / BASR / LOAD EP / =V)
    def detect_call(self, line):
        patterns = [
            r"L\s+\d+,\=V\((\w+)\)",   # LOAD EP style
            r"BALR\s+\d+,\d+",        # BALR indirect
            r"BASR\s+\d+,\d+",        # BASR indirect
        ]

        for p in patterns:
            if re.search(p, line):
                return True
        return False

    # Extract target module from LOAD EP style
    def extract_module(self, line):
        match = re.search(r"\=V\((\w+)\)", line)
        if match:
            return match.group(1)
        return None

    # Build graph from HLASM lines
    def parse(self, lines):

        for line in lines:

            # detect module
            module = self.detect_module(line)
            if module:
                self.current_module = module
                self.modules.add(module)
                continue

            # detect call
            if self.detect_call(line):

                target = self.extract_module(line)

                if target:
                    self.call_graph[self.current_module].append(target)

        return self.call_graph

    # Pretty print graph
    def print_graph(self):

        print("\nCALL GRAPH")
        print("-" * 40)

        for k, v in self.call_graph.items():
            print(f"{k} → {', '.join(v)}")

    # Detect missing modules
    def detect_missing(self):

        all_targets = set()
        for v in self.call_graph.values():
            all_targets.update(v)

        missing = all_targets - self.modules

        return missing