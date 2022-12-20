import re
import xml.etree.ElementTree as ET
from pathlib import Path

from class_parser import *
from git import Repo

import logging

log = logging.getLogger(__name__)


def serialize_call(node):
    """
    Represent a <call> tag as a string.
    """
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
    variables = [serialize_call(v) for v in node]
    lineno = int(node.attrib["location"].split(":")[1])
    return {
        "tag": node.tag,
        **node.attrib,
        "variables": variables,
        "relative_lineno": lineno - method_node.start_point[0],
        "lineno": lineno,
    }


def get_src_fpath(project, class_name):
    """
    Get filepath of class_name source code.
    """
    repo = Repo("repos/" + project)
    if class_name.endswith("Fuzzer"):
        src_fpath = next(
            (Path("projects") / project).rglob(class_name.replace(".", "/") + ".java")
        )
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
    return src_fpath


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
                entry_variables = [serialize_call(v) for v in child]
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


auto_lookup = {
    "org.springframework": "spring-framework",
    "org.slf4j": "slf4j-api",
    "jakarta.mail": "jakarta-mail-api",
}


def process_one(call, xml):
    """
    Process one <call> tag into dict representation with extra metadata.
    """
    lineno = int(call.attrib["location"].split(":")[1])
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
            src_fpath = get_src_fpath(project, class_name)
        except AssertionError:
            return {
                "result": "missing_source"
            }
        method_node = get_method_node(src_fpath, class_name, method_name, lineno)
        if method_node is None:
            return {
                "result": "missing_method",
            }
        assert method_node is not None, method_node
        ifw = is_forward(method_node)
        method_code = method_node.text.decode()

        entry_variables, lines_covered = get_dynamic_information(call, method_node)

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
                "attributes": call.attrib,
                "lines_covered": lines_covered,
            },
        }
    except Exception:
        log.exception(f"ERROR HANDLING METHOD {project=} {class_name=} {method_name=}")
        return {
            "result": "error_method",
        }
    
def test_process_one():
    xml = Path("postprocessed_xmls/trace-greenmail-UserManagerFuzzer.xml")
    call = next(n for _, n in ET.iterparse(xml) if n.tag == "call")
    process_one(call, xml)
