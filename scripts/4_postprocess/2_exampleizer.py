# %%
import traceback
from pathlib import Path

import tqdm
from git import Repo

from class_parser import get_method_node, get_source_file, is_forward
import xml.etree.ElementTree as ET

import re

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('input_dir')
    parser.add_argument('output_file')
    parser.add_argument('--sample', action='store_true')
    parser.add_argument('--nproc', type=int, default=10)
    parser.add_argument('--single_thread', action='store_true')
    args = parser.parse_args()

    # %%
    all_projects = Path("data/1_preprocess/java-projects-from-csv.txt").read_text().splitlines(keepends=False)
    all_xmls = list(Path(args.input_dir).glob("*.xml"))
    if args.sample:
        # all_xmls = all_xmls[:2]
        all_xmls = all_xmls[2:4]
        # all_xmls = [
        #     Path("postprocessed_xmls/trace-apache-commons-bcel-BcelFuzzer.xml.repair.xml")
        # ]
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

if __name__ == "__main__":
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
if __name__ == "__main__":
    project = "apache-commons-lang"
    method = "org.apache.commons.lang3.Validate.isTrue(boolean, java.lang.String, java.lang.Object[])"
    data = decompose_location(method)
    class_name = data["class_name"]
    method_name = data["method_name"]
    repo = Repo("repos/" + project)
    get_source_file(repo, class_name)


# %%
auto_lookup = {
    'org.springframework': 'spring-framework',
    'org.slf4j': 'slf4j-api',
    'jakarta.mail': 'jakarta-mail-api',
}

def process_one(call, project, xml, repo, printed_methods):
    # print("FOO", call.attrib, xml, ET.tostring(call))
    method = call.attrib["method"]
    data = decompose_location(method)
    # if data["class_name"].endswith("Fuzzer"):
    #     return {
    #         "result": "fuzzer_class",
    #     }
    if data["method_name"].startswith("$"):
        return {
            "result": "invalid_call",
            "class_name": data["class_name"],
            "method_name": data["method_name"],
        }
    if data["inner_class_name"] is not None:
        return {
            "result": "skipped_inner_class",
        }
    if data["method_name"].startswith("lambda$"):
        return {
            "result": "skipped_lambda",
        }
    class_name = data["class_name"]
    # if class_name in auto_lookup:
    #     repo = Repo(auto_lookup[class_name])
    method_name = data["method_name"]
    try:
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
                    **node.attrib,
                    "text": text,
                }
            else:
                return {
                    "tag": node.tag,
                    **node.attrib,
                    "xml": ET.tostring(node, encoding="unicode"),
                }

        if class_name.endswith("Fuzzer"):
            src_fpath = next((Path("projects") / project).rglob(class_name.replace(".", "/") + ".java"))
        else:
            src_fpath = get_source_file(repo, class_name)
            # TODO: make this better
            # try:
            #     src_fpath = get_source_file(repo, class_name)
            # except AssertionError:
            #     # Try again
            #     if class_name.startswith("org.apache.commons"):
            #         package_subname = class_name.split(".")[3]
            #         if package_subname[-1].isdigit():
            #             # configuration2 lang3
            #             package_subname = package_subname[:-1]
            #         repo_name = "apache-commons-" + package_subname
            #         repo = Repo("repos/" + repo_name)
            #         src_fpath = get_source_file(repo, class_name)
            #     else:
            #         p = next(((k, v) for k, v in auto_lookup.items() if class_name.startswith(k)), None)
            #         if p is not None:
            #             repo_name = p[1]
            #             repo = Repo("repos/" + repo_name)
            #             src_fpath = get_source_file(repo, class_name)
            #         else:
            #             raise
        # example: com.sun.mail.util.ASCIIUtility:116
        lineno = int(call.attrib["location"].split(":")[1])
        method_node = get_method_node(src_fpath, class_name, method_name, lineno)
        if method_node is None:
            if method not in printed_methods:
                print(f"no such method {src_fpath=} {project=} {repo=} {class_name=} {method_name=} {lineno=}")
                printed_methods[(project, class_name, method_name)] = 0
            printed_methods[(project, class_name, method_name)] += 1
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
                **node.attrib,
                "variables": variables,
                "relative_lineno": lineno - method_node.start_point[0],
                "lineno": lineno,
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
        lines_covered = list(sorted(set(s["relative_lineno"] for s in steps_data if "relative_lineno" in s)))

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
                "lines_covered": lines_covered,
            }
        }
    except Exception:
        if method not in printed_methods:
            print(f"failed exampling method call {project=} {class_name=} {method_name=}\n{traceback.format_exc()}")
            printed_methods[(project, class_name, method_name)] = 0
        printed_methods[(project, class_name, method_name)] += 1
        return {
            "result": "error_method",
        }

import json

from multiprocessing import Manager, Pool
import functools
from collections import defaultdict

if __name__ == "__main__":
    all_results = defaultdict(int)

    def get_calls_iter(iter):
        for _, node in iter:
            if node.tag == "call":
                yield node
                node.clear()

    with open(args.output_file, "w") as outf:
        for project in tqdm.tqdm(all_projects, desc="all projects"):
            try:
                project_xmls = [xml for xml in all_xmls if xml.name.startswith("trace-" + project)]
                for i, xml in enumerate(project_xmls):
                    repo = Repo("repos/" + project)
                    num_calls = 0
                    with open(xml) as inf:
                        for line in tqdm.tqdm(inf, desc="count <call> tags", leave=False):
                            if "<call" in line:
                                num_calls += 1
                    iter = ET.iterparse(xml, events=("end",))
                    calls = get_calls_iter(iter)
                    try:
                        with Manager() as man:
                            printed_methods = man.dict()
                            invalid_methods = set()
                            with Pool(args.nproc) as pool:
                                if args.single_thread:
                                    it = map(functools.partial(process_one, project=project, repo=repo, xml=xml, printed_methods=printed_methods), calls)
                                else:
                                    it = pool.imap(functools.partial(process_one, project=project, repo=repo, xml=xml, printed_methods=printed_methods), calls)
                                with tqdm.tqdm(it,
                                                desc=f"XML ({i+1}/{len(project_xmls)}) {xml}",
                                                total=num_calls,
                                                leave=False
                                                ) as pbar:
                                    for result in pbar:
                                        if result["result"] == "success":
                                            outf.write(json.dumps(result["data"]) + "\n")
                                        if result["result"] == "invalid_call":
                                            invalid_methods.add((result["class_name"], result["method_name"]))
                                        all_results[result["result"]] += 1
                                        # pbar.set_postfix(all_results)
                            printed_methods = dict(printed_methods)
                            if len(printed_methods) > 0:
                                print(xml, "Errored methods:", json.dumps({str(k): v for k, v in printed_methods.items()}, indent=2), sep="\n")
                            if len(invalid_methods) > 0:
                                print(xml, "Invalid calls:", json.dumps(sorted(invalid_methods), indent=2), sep="\n")
                            # print(xml, "Results:", json.dumps(all_results, indent=2), sep="\n")
                    except Exception:
                        all_results["failed_xml"] += 1
                        print("ERROR in file:", project, str(xml))
                        print(traceback.format_exc())
            except Exception:
                all_results["failed_project"] += 1
                print("failed example-izing", project)
                print(traceback.format_exc())
    print("RESULTS:")
    print(json.dumps(all_results, indent=2))

# %%
