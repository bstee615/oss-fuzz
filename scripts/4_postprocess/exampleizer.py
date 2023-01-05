import pprint
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import itertools

from class_parser import *
from git import Repo

import logging

log = logging.getLogger(__name__)


def serialize_variable(node):
    """
    Represent a <variable> or sibling tag as a string.
    """
    # TODO: handle <SKIPPED>, <event-thread-mismatch>, <exception>
    if node.tag == "variable":
        text = node.text
        if node.attrib["serializer"] == "ARRAY":
            text = text.strip()
        elif node.attrib["serializer"] == "TOSTRING":
            if text.startswith('"') and text.endswith('"'):
                m = re.search(r"@[\da-z]{8}", text)
                if m is not None:
                    text = text[: m.start()] + text[m.end() :]
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


def serialize_tracepoint(method_node, node):
    """
    Convert <tracepoint> tag into dict.
    """
    variables = [serialize_variable(v) for v in node]
    result = {
        "tag": node.tag,
        **node.attrib,
        "variables": variables,
    }
    try:
        lineno = int(node.attrib["location"].split(":")[1])
        result.update({
            "relative_lineno": lineno - method_node.start_point[0],
            "lineno": lineno,
        })
    except IndexError:
        pass
    return result

auto_lookup = {
    # "org.springframework": "spring-framework",
    "org.slf4j": "slf4j-api",
    # "jakarta.mail": "jakarta-mail-api",
}

def get_repo(project, class_name):
    """Return the repo containing the project's source code."""
    matched_repo_name = None
    for package_path, repo_name in auto_lookup.items():
        if class_name.startswith(package_path):
            matched_repo_name = repo_name
    if matched_repo_name is not None:
        return Repo("repos/" + matched_repo_name), True
    else:
        return Repo("repos/" + project), False


def get_src_fpath(project, class_name):
    """
    Get filepath of class_name source code.
    """
    repo, fudged = get_repo(project, class_name)
    if class_name.endswith("Fuzzer") or class_name == "ExampleFuzzerNative":
        src_fpaths = [next(
            (Path("projects") / project).rglob(class_name.replace(".", "/") + ".java")
        )]
    else:
        src_fpaths = get_source_file(repo, class_name)
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
    return src_fpaths, fudged


def get_dynamic_information(call, method_node):
    """
    Return a list of lines covered by the method.
    """

    steps = []
    entry_variables = None
    for child in call:
        if child.tag == "call":
            pass
        elif child.tag == "tracepoint":
            steps.append(child)
            if child.attrib["type"] == "entry":
                entry_variables = [serialize_variable(v) for v in child]
        else:
            steps.append(child)
    assert entry_variables is not None, f"malformed trace: {call}"

    steps_data = []
    for node in steps:
        if node.tag == "tracepoint":
            steps_data.append(serialize_tracepoint(method_node, node))
        else:
            steps_data.append(
                {
                    "tag": node.tag,
                    "text": node.text,
                    **node.attrib,
                }
            )
    lines_covered = list(
        sorted(set(s["relative_lineno"] for s in steps_data if "relative_lineno" in s))
    )

    return entry_variables, lines_covered



def process_one(call, xml):
    """
    Process one <call> tag into dict representation with extra metadata.
    """
    try:
        lineno = int(call.attrib["location"].split(":")[1])
    except IndexError:
        lineno = None
    method = call.attrib["method"]
    location = decompose_location(method)
    if location["method_name"].startswith("$"):
        return {
            "result": "invalid_call",
            "class_name": location["class_name"],
            "method_name": location["method_name"],
        }
    if location["inner_class_name"] is not None:
        return {
            "result": "skipped_inner_class",
        }
    if location["method_name"].startswith("lambda$"):
        return {
            "result": "skipped_lambda",
        }
    class_name = location["class_name"]

    xml_stem = xml.stem
    project_fuzzer = xml_stem.split("-", maxsplit=1)[1]
    project, fuzzer_name = project_fuzzer.rsplit("-", maxsplit=1)
    method_name = location["method_name"]
    try:
        try:
            src_fpaths, fudged = get_src_fpath(project, class_name)
        except AssertionError:
            return {
                "result": "missing_source",
            }
        for src_fpath in src_fpaths:
            method_node = get_method_node(src_fpath, class_name, method_name, lineno)
            if method_node is not None:
                break

        if method_node is None:
            return {
                "result": "missing_method",
                "project": project,
                "class_name": class_name,
                "method_name": method_name,
                "lineno": lineno,
                "src_fpath": src_fpath,
                "xml": xml,
            }

        assert method_node is not None, method_node
        method_type = get_method_type(method_node)
        method_code = method_node.text.decode()

        entry_variables, lines_covered = get_dynamic_information(call, method_node)

        return {
            "result": "success",
            "data": {
                "project": project,
                "class": class_name,
                "method": method_name,
                "fudged_repo": fudged,
                "method_type": method_type,
                "is_forward": method_type == "forward",
                "has_body": method_type != "no_body",
                "xml_file_path": str(xml.absolute()),
                "file_path": str(src_fpath.absolute()),
                "start_point": method_node.start_point,
                "end_point": method_node.end_point,
                "code": method_code,
                "entry_variables": entry_variables,
                "attributes": call.attrib,
                "lines_covered": lines_covered,
            },
        }
    except Exception as ex:
        log.exception(f"ERROR HANDLING METHOD {project=} {class_name=} {method_name=}")
        return {
            "result": "error_method",
            "project": project,
            "class_name": class_name,
            "method_name": method_name,
            "ex": ex,
        }
    
def test_process_no_lineno():
    print()
    xml = Path("postprocessed_xmls/trace-java-example-ExampleFuzzerNative.xml")
    it = (n for _, n in ET.iterparse(xml) if n.tag == "call")
    results = defaultdict(int)
    for node in it:
        data = process_one(node, xml)
        results[data["result"]] += 1
        # pprint.pprint(data)
    pprint.pprint(dict(results))
    
def test_process_one():
    print()
    xml = Path("postprocessed_xmls/trace-greenmail-UserManagerFuzzer.xml")
    it = (n for _, n in ET.iterparse(xml) if n.tag == "call")

    myp = pprint.PrettyPrinter(width=600)

    i = 0
    results = defaultdict(int)
    fudged = []
    for node in it:
        try:
            data = process_one(node, xml)
            results[data["result"]] += 1
            if data["result"] != "success":
                print(i, "MISSING!")
                myp.pprint(data)
                # break
            else:
                fudged.append(data["data"]["fudged_repo"])
            # myp.pprint(data)
        except Exception:
            print(i, "FAILED!")
            traceback.print_exc()
            break
        i += 1
    myp.pprint(dict(results))
    print("FUDGED:", sum(fudged), len(fudged))
