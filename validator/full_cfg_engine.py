from collections import defaultdict

class StructuredCFG:

    def __init__(self):
        self.calls = defaultdict(list)
        self.cfg = defaultdict(lambda: {"next": [], "branch": []})
        self.labels = set()
        self.current_module = None

    def add_module(self, name):
        self.current_module = name

    def add_call(self, target):
        self.calls[self.current_module].append(target)

    def add_flow(self, target):
        self.cfg[self.current_module]["next"].append(target)

    def add_branch(self, target):
        self.cfg[self.current_module]["branch"].append(target)

    def print_graph(self):

        print("\nCALL GRAPH")
        print("-" * 40)
        for k, v in self.calls.items():
            print(f"{k} → {set(v)}")

        print("\nCONTROL FLOW GRAPH")
        print("-" * 40)
        for k, v in self.cfg.items():
            print(f"{k}")
            print(f"   NEXT   → {v['next']}")
            print(f"   BRANCH → {v['branch']}")