# %%
import re
import traceback
from pathlib import Path

import tqdm
from git import Repo

from class_parser import get_method_node, get_source_file
import xml.etree.ElementTree as ET

from xml_traverser import get_calls

# %%
all_projects = Path("java-projects-from-csv.txt").read_text().splitlines(keepends=False)
all_xmls = [Path(f) for f in Path("SUCCESS_FILES_SHAGAGONOOK.txt").read_text().splitlines(keepends=False)]


# %%
def decompose_location(location):
    items = location.split('(')[0]
    class_name, method_name = items.rsplit('.', maxsplit=1)
    return {
        "class_name": class_name,
        "method_name": method_name,
    }

decompose_location("ASCIIUtilityFuzzer.fuzzerTestOneInput(com.code_intelligence.jazzer.api.FuzzedDataProvider)")

#%%
def is_valid_call(node):
    return not decompose_location(node.attrib["method"])["class_name"].endswith("Fuzzer")


# %%
import json

failed_getting = 0
with open("examples.jsonl", "w") as outf:
    for project in tqdm.tqdm(all_projects):
        try:
            fpaths = [xml for xml in all_xmls if xml.name.startswith("trace-" + project)]
            for fpath in fpaths:
                repo = Repo("repos/" + project)
                root = ET.parse(fpath).getroot()
                calls = get_calls(root)
                calls = filter(is_valid_call, calls)
                for i, call in enumerate(calls):
                    method = call.attrib["method"]
                    try:
                        data = decompose_location(method)
                        class_name = data["class_name"]
                        method_name = data["method_name"]
                        
                        call_attrib = call.attrib
                        tracepoint = None
                        for child in call:
                            if child.tag == "tracepoint" and child.attrib["type"] == "entry":
                                tracepoint = child
                                break
                        def serialize(node):
                            if node.tag == "variable":
                                return {
                                    "tag": node.tag,
                                    "name": node.attrib["name"],
                                    "serializer": node.attrib["serializer"],
                                    "source": node.attrib["source"],
                                    "thread": node.attrib["thread"],
                                    "type": node.attrib["type"],
                                    "text": node.text,
                                }
                            else:
                                return {
                                    "tag": node.tag,
                                    "xml": ET.tostring(node, encoding="unicode"),
                                }
                        variables = [serialize(v) for v in tracepoint]

                        fpath = get_source_file(repo, class_name)
                        # com.sun.mail.util.ASCIIUtility:116
                        lineno = int(call.attrib["location"].split(":")[1])
                        method_node = get_method_node(fpath, class_name, method_name, lineno)
                        is_forward = is_forward(method_node)
                        assert method_node is not None, method
                        method_code = method_node.text.decode()
                        outf.write(json.dumps({
                            "project": project,
                            "class": class_name,
                            "method": method_name,
                            "is_forward": is_forward,
                            "file_path": str(fpath),
                            "start_point": method_node.start_point,
                            "end_point": method_node.end_point,
                            "code": method_code,
                            "entry_variables": variables,
                            "attributes": call_attrib,
                        }) + "\n")
                    except Exception:
                        print("failed exampling method call", i, method, call.attrib)
                        print(traceback.format_exc())
        except Exception:
            print("failed example-izing", project)
            print(traceback.format_exc())
print("FAILED", failed_getting, "PROJECTS")

# %%
