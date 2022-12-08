# %%
import traceback
from pathlib import Path

import tqdm
from git import Repo

from class_parser import get_method_node, get_source_file, is_forward
import xml.etree.ElementTree as ET

from xml_traverser import get_calls

# %%
all_projects = Path("data/1_preprocess/java-projects-from-csv_cut1.txt").read_text().splitlines(keepends=False)
# all_xmls = [Path(f) for f in Path("SUCCESS_FILES_SHAGAGONOOK.txt").read_text().splitlines(keepends=False)]
all_xmls = list(Path("postprocessed").glob("*.xml"))
print(len(all_xmls), "XMLs")


# %%
def decompose_location(location):
    items = location.split('(')[0]
    class_name, method_name = items.rsplit('.', maxsplit=1)
    dollar_idx = class_name.find("$")
    after_dollar_part = None
    if dollar_idx != -1:
        class_name, after_dollar_part = class_name.split("$")
    return {
        "class_name": class_name,
        "method_name": method_name,
        "inner_class_name": after_dollar_part,
    }

decompose_location("ASCIIUtilityFuzzer.fuzzerTestOneInput(com.code_intelligence.jazzer.api.FuzzedDataProvider)")
decompose_location("org.apache.commons.configuration2.tree.InMemoryNodeModel$1.visitBeforeChildren(java.lang.Object, org.apache.commons.configuration2.tree.NodeHandler)")

#%%
# project = "apache-commons-configuration"
# method = "org.apache.commons.configuration2.tree.InMemoryNodeModel$1.visitBeforeChildren(java.lang.Object, org.apache.commons.configuration2.tree.NodeHandler)"
# data = decompose_location(method)
# class_name = data["class_name"]
# method_name = data["method_name"]
# repo = Repo("repos/" + project)
# src_fpath = get_source_file(repo, class_name)
# get_method_node(src_fpath, class_name, method_name, 160)

#%%
project = "apache-commons-lang"
method = "org.apache.commons.lang3.Validate.isTrue(boolean, java.lang.String, java.lang.Object[])"
data = decompose_location(method)
class_name = data["class_name"]
method_name = data["method_name"]
repo = Repo("repos/" + project)
get_source_file(repo, class_name)

#%%
def is_valid_call(node):
    return not decompose_location(node.attrib["method"])["class_name"].endswith("Fuzzer")


# %%
def get_calls_iter(iter):
    for _, node in iter:
        if node.tag == "call":
            yield node
            node.clear()

def process_one(call, xml, repo, printed_methods):
    if not is_valid_call(call):
        return {
            "result": "invalid_call",
        }
    method = call.attrib["method"]
    data = decompose_location(method)
    if data["inner_class_name"] is not None:
        return {
            "result": "skipped_inner_class",
        }
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

    src_fpath = get_source_file(repo, class_name)
    # com.sun.mail.util.ASCIIUtility:116
    lineno = int(call.attrib["location"].split(":")[1])
    method_node = get_method_node(src_fpath, class_name, method_name, lineno)
    if method_node is None:
        if method not in printed_methods:
            print("no such method", project, src_fpath, class_name, method_name, lineno)
            printed_methods.add(method)
        return {
            "result": "missing_method",
        }
    assert method_node is not None, method_node
    ifw = is_forward(method_node)
    method_code = method_node.text.decode()
    return {
        "result": "success",
        "data": {
            "project": project,
            "class": class_name,
            "method": method_name,
            "is_forward": ifw,
            "xml_file_path": str(xml.absolute()),
            "file_path": str(src_fpath.absolute()),
            "start_point": method_node.start_point,
            "end_point": method_node.end_point,
            "code": method_code,
            "entry_variables": variables,
            "attributes": call_attrib,
        }
    }

import json

from multiprocessing import Pool, Manager
import functools

failed_project = 0
failed_example = 0
missing_method = 0
skipped_inner_class = 0

# man = Manager()

with open("postprocessed/examples_cut1.jsonl", "w") as outf:
    for project in tqdm.tqdm(all_projects, desc="all projects"):
        try:
            project_xmls = [xml for xml in all_xmls if xml.name.startswith("trace-" + project)]
            # print(project, fpaths)
            for i, xml in enumerate(project_xmls):
                repo = Repo("repos/" + project)
                num_calls = 0
                with open(xml) as inf:
                    for line in tqdm.tqdm(inf, desc="count <call> tags", leave=False):
                        if "<call" in line:
                            num_calls += 1
                iter = ET.iterparse(xml, events=("end",))
                calls = get_calls_iter(iter)
                # should_leave = i == len(project_xmls)-1
                try:
                    printed_methods = set()
                    # for i, call in enumerate(tqdm.tqdm(calls, f"XML ({i+1}/{len(project_xmls)}) {xml}", total=num_calls, leave=False)):
                    # queue = man.Queue(maxsize=12800)
                    with Pool(10) as pool:
                        for result in tqdm.tqdm(
                                                pool.imap(functools.partial(process_one, repo=repo, xml=xml, printed_methods=printed_methods), calls),
                                                desc=f"XML ({i+1}/{len(project_xmls)}) {xml}",
                                                total=num_calls,
                                                leave=False
                                                ):
                            try:
                                if result["result"] == "success":
                                    outf.write(json.dumps(result["data"]) + "\n")
                                elif result["result"] == "missing_method":
                                    missing_method += 1
                                elif result["result"] == "skipped_inner_class":
                                    skipped_inner_class += 1
                            except Exception:
                                failed_example += 1
                                if method not in printed_methods:
                                    print("failed exampling method call", project, repo, i, method)
                                    print(traceback.format_exc())
                                    printed_methods.add(method)
                except Exception:
                    print("ERROR in file:", project, str(xml))
                    print(traceback.format_exc())
        except Exception:
            failed_project += 1
            print("failed example-izing", project)
            print(traceback.format_exc())
print("FAILED", failed_project, "PROJECTS")
print("FAILED", failed_example, "EXAMPLES")
print("MISSED", missing_method, "METHODS")
print("SKIPPED", skipped_inner_class, "INNER CLASSES")

# %%
