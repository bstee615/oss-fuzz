# %%
import traceback
from pathlib import Path

import tqdm
from git import Repo

from class_parser import get_method_node, get_source_file, is_forward
import xml.etree.ElementTree as ET

import re

import argparse
parser = argparse.ArgumentParser(description='Description of your program')
parser.add_argument('input_dir')
parser.add_argument('output_file')
parser.add_argument('--sample', action='store_true')
parser.add_argument('--nproc', type=int, default=10)
args = parser.parse_args()

# %%
all_projects = Path("data/1_preprocess/java-projects-from-csv.txt").read_text().splitlines(keepends=False)
all_xmls = list(Path(args.input_dir).glob("*.xml"))
if args.sample:
    all_xmls = all_xmls[:2]
print(len(all_xmls), "XMLs")


# %%
def decompose_location(location):
    items = location.split('(')[0]
    class_name, method_name = items.rsplit('.', maxsplit=1)
    dollar_idx = class_name.find("$")
    after_dollar_part = None
    if dollar_idx != -1:
        class_name, after_dollar_part = class_name.split("$", maxsplit=1)
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
    if data["method_name"].startswith("lambda$"):
        return {
            "result": "skipped_lambda",
        }
    class_name = data["class_name"]
    method_name = data["method_name"]

    def serialize(node):
        if node.tag == "variable":
            text = node.text
            if node.attrib["serializer"] == "ARRAY":
                text = text.strip()
            elif node.attrib["serializer"] == "TOSTRING":
                if text.startswith('\"') and text.endswith('\"'):
                    # text = text[1:-1]
                    m = re.search(r"@[\da-z]{8}", text)
                    if m is not None:
                        text = text[:m.start()] + text[m.end():]
            if "age" in node.attrib:
                del node.attrib["age"]
            return {
                "tag": node.tag,
                "text": text,
                **node.attrib,
            }
        else:
            return {
                "tag": node.tag,
                "xml": ET.tostring(node, encoding="unicode"),
            }

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
    
    call_attrib = call.attrib
    steps = []
    entry_variables = None
    for child in call:
        if child.tag == "call":
            pass
        elif child.tag == "tracepoint":
            steps.append(child)
            if child.attrib["type"] == "entry":
                entry_variables = [serialize(v) for v in child]
        else:
            steps.append(child)
    assert entry_variables is not None, f"malformed trace: {call}, {repo}"

    def step_izer(node):
        """Convert <tracepoint> tag into dict."""
        variables = [serialize(v) for v in node]
        lineno = int(node.attrib["location"].split(":")[1])
        return {
            "tag": node.tag,
            "variables": variables,
            "relative_lineno": lineno - method_node.start_point[0],
            "lineno": lineno,
            **node.attrib,
        }
    steps_data = []
    for node in steps:
        if node.tag == "tracepoint":
            steps_data.append(step_izer(node))
        else:
            steps_data.append({
                "tag": node.tag,
                "text": node.text,
                **node.attrib,
            })

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
            "entry_variables": entry_variables,
            "attributes": call_attrib,
            "steps": steps_data,
        }
    }

import json

from multiprocessing import Pool, Manager
import functools
from collections import defaultdict

all_results = defaultdict(int)
# failed_project = 0
# failed_example = 0
# missing_method = 0
# skipped_inner_class = 0

# man = Manager()

with open(args.output_file, "w") as outf:
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
                    # printed_methods = set()
                    # for i, call in enumerate(tqdm.tqdm(calls, f"XML ({i+1}/{len(project_xmls)}) {xml}", total=num_calls, leave=False)):
                    # queue = man.Queue(maxsize=12800)
                    with Manager() as man:
                        with man.Pool(args.nproc) as pool:
                            printed_methods = man.dict()
                            it = pool.imap(functools.partial(process_one, repo=repo, xml=xml, printed_methods=printed_methods), calls)
                            with tqdm.tqdm(it,
                                            desc=f"XML ({i+1}/{len(project_xmls)}) {xml}",
                                            total=num_calls,
                                            leave=False
                                            ) as pbar:
                                for result in pbar:
                                    if result["result"] == "success":
                                        outf.write(json.dumps(result["data"]) + "\n")
                                    all_results[result["result"]]
                                    pbar.set_postfix(all_results)
                except Exception:
                    all_results["failed_xml"] += 1
                    print("ERROR in file:", project, str(xml))
                    print(traceback.format_exc())
        except Exception:
            all_results["failed_project"] += 1
            print("failed example-izing", project)
            print(traceback.format_exc())
# print("FAILED", failed_project, "PROJECTS")
# print("FAILED", failed_example, "EXAMPLES")
# print("MISSED", missing_method, "METHODS")
# print("SKIPPED", skipped_inner_class, "INNER CLASSES")
print("RESULTS:")
print(json.dumps(all_results, indent=2))

# %%
