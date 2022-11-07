"""
PARSE XML FILES
TURN INTO TREE
CHECK TREE STATISTICS
"""


#%%
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
import re

xmls = list(Path("traces-1m-worker").glob("*.xml"))
print(len(xmls), "XML files found")

successes = []
failed = 0
for fpath in xmls:
    xmlstring = fpath.read_text()
    try:
        root = ET.ElementTree(ET.fromstring(xmlstring)).getroot()
        print(fpath, "parsed successfully")
        successes.append(fpath)
    except ET.ParseError as ex:
        print("exception", type(ex), ex, "parsing", fpath)
        continue

        fuzzer_start = re.compile(r'''<call[^>]*method="[^."]+.fuzzerTestOneInput\([^)]+\)"[^>]*''')
        fuzzer_almost_end = re.compile(r'''<tracepoint[^>]+>''')
        method_re = re.compile(r'''method="[^."]+.fuzzerTestOneInput\([^)]+\)"''')
        exit_re = re.compile(r'''type="exit"''')
        fuzzer_real_end = re.compile(r'''</call>''')
        xmllines = xmlstring.splitlines(keepends=True)
        it = iter(xmllines)
        fuzz_functions = []
        current_fuzz_function = None
        try:
            while True:
                line = next(it)
                if fuzzer_start.search(line):
                    # print("start at", line)
                    # start fuzzed function
                    current_fuzz_function = []
                if current_fuzz_function is not None:
                    current_fuzz_function.append(line)
                m = fuzzer_almost_end.search(line)
                if m:
                    tag = m.group(0)
                    if method_re.search(tag) and exit_re.search(tag):
                        # print("end at", line)
                        while True:
                            line = next(it)
                            # print("search end", line)
                            current_fuzz_function.append(line)
                            if fuzzer_real_end.search(line):
                                # cap off fuzzed function
                                # print("end", line)
                                fuzz_functions.append("".join(current_fuzz_function))
                                current_fuzz_function = []
                                break
        except StopIteration:
            pass
        
        print("found", fuzz_functions, "functions")

        success_functions = []
        failed_functions = 0
        for fuzzed_function in fuzz_functions:
            try:
                root = ET.ElementTree(ET.fromstring(fuzzed_function)).getroot()
                success_functions.append(fuzzed_function)
            except ET.ParseError as ex:
                # print("function exception", type(ex), ex, "parsing", fpath)
                # print(fuzzed_function)
                failed_functions += 1
                if failed_functions >= 5:
                    break
        print("failed", failed_functions, "out of", len(fuzz_functions), "functions")

        success_text = xmllines[0] + "".join(success_functions) + "</trace>"
        repair_path = Path(str(fpath) + ".repair")
        repair_path.write_text("".join(success_text))
        failed += 1
print(failed, "files failed parsing")

# root = ET.parse('traces-1m/trace-angus-mail-BASE64EncoderStreamFuzzer.xml').getroot()
# root

#%%
import networkx as nx

class DFS:
    def __init__(self, node) -> None:
        self.counter = 0
        self.graph = nx.DiGraph()
        self.dfs(node)

    def dfs(self, node, parent=None):
        my_counter = self.counter
        attr = {}
        attr["tag"] = node.tag
        if "method" in node.attrib:
            attr["method"] = node.attrib["method"]
        self.graph.add_node(my_counter, **attr)
        self.counter += 1
        if parent is not None:
            self.graph.add_edge(parent, my_counter)
        for child in node:
            self.dfs(child, my_counter)

def to_nx_graph(root):
    return DFS(root).graph

root = ET.parse("traces-1m/trace-apache-commons-beanutils-BeanutilsFuzzer.xml").getroot()

G = to_nx_graph(root)

print(G)

#%%
successes = [xmls[0]]
for fpath in successes:
    root = ET.ElementTree(ET.fromstring(xmlstring)).getroot()
    G = to_nx_graph(root)
    calls = []
    for n, tag in G.nodes(data="tag"):
        if tag == "call":
            calls.append(n)
    print(len(calls), "calls", len(set(G.nodes[c]["method"] for c in calls)))

# %%
