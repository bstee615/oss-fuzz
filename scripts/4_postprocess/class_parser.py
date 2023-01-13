#%%
import logging
import os
import traceback
from pathlib import Path
from pprint import pp

from git import Repo
from tree_sitter import Language, Parser

log = logging.getLogger(__name__)

TREE_SITTER_LIB_PREFIX = "./lib"

languages = ["java"]
language_dirs = []

for lang in languages:
    clone_dir = os.path.join(TREE_SITTER_LIB_PREFIX, f"tree-sitter-{lang}")
    language_dirs.append(clone_dir)

lib_file = os.path.join(TREE_SITTER_LIB_PREFIX, "build/languages.so")
Language.build_library(
    # Store the library in the `build` directory
    lib_file,
    # Include one or more languages
    [
        os.path.join(TREE_SITTER_LIB_PREFIX, f"tree-sitter-{lang}"),
    ],
)

LANGUAGE = Language(lib_file, languages[0])
parser = Parser()
parser.set_language(LANGUAGE)


def parse_file(filename):
    with open(filename, "rb") as f:
        tree = parser.parse(f.read())
    return tree

def print_tree(root, return_string=False):
    if return_string:
        output = io.StringIO()
    else:
        output = None
    print(file=output)
    q = [(root, 0)]
    while len(q) > 0:
        n, level = q.pop(-1)
        print("  " * level, end="", file=output)
        node_str = print_node(n, return_string=True)
        print(node_str.rstrip(), file=output)
        q.extend([(m, level+1) for m in reversed(n.children)])
    if return_string:
        return output.getvalue()

def test_parse():
    tree = parser.parse("""public void main() {
    System.out.println("Hello, world!");
}""".encode())
    print_tree(tree.root_node)

#%%


def decompose_location(location):
    """
    Split a location org.benjis.Foo$Bar.baz() into its components "org.benjis.Foo", "bar", "Bar" (inner class)
    """
    method_id, rest = location.split("(")
    class_name, method_name = method_id.rsplit(".", maxsplit=1)
    dollar_idx = class_name.find("$")
    after_dollar_part = None
    if dollar_idx != -1:
        class_name, after_dollar_part = class_name.split("$", maxsplit=1)
    rest = rest[:-1]
    if len(rest) == 0:
        parameter_types = []
    else:
    parameter_types = rest.split(", ")
    return {
        "class_name": class_name,
        "method_name": method_name,
        "inner_class_name": after_dollar_part,
        "parameter_types": parameter_types,
    }


def test_decompose_location():
    fuzzerTestOneInput = decompose_location(
        "ASCIIUtilityFuzzer.fuzzerTestOneInput(com.code_intelligence.jazzer.api.FuzzedDataProvider)"
    )
    assert fuzzerTestOneInput["class_name"] == "ASCIIUtilityFuzzer"
    assert fuzzerTestOneInput["method_name"] == "fuzzerTestOneInput"
    assert fuzzerTestOneInput["inner_class_name"] == None
    assert fuzzerTestOneInput["parameter_types"] == [
        'com.code_intelligence.jazzer.api.FuzzedDataProvider',
    ]
    pp(fuzzerTestOneInput)
    visitBeforeChildren = decompose_location(
        "org.apache.commons.configuration2.tree.InMemoryNodeModel$1.visitBeforeChildren(java.lang.Object, org.apache.commons.configuration2.tree.NodeHandler)"
    )
    assert visitBeforeChildren["class_name"] == "org.apache.commons.configuration2.tree.InMemoryNodeModel"
    assert visitBeforeChildren["method_name"] == "visitBeforeChildren"
    assert visitBeforeChildren["inner_class_name"] == "1"
    assert visitBeforeChildren["inner_class_name"] == "1"
    assert visitBeforeChildren["parameter_types"] == [
        'java.lang.Object',
        'org.apache.commons.configuration2.tree.NodeHandler',
    ]
    pp(visitBeforeChildren)


def get_source_file(repo, class_name_fq):
    class_filepath = class_name_fq.replace(".", "/") + ".java"
    result = list(Path(repo).rglob(class_filepath))
    return result


def test_get_source_file():
    project = "apache-commons-lang"
    method = "org.apache.commons.lang3.Validate.isTrue(boolean, java.lang.String, java.lang.Object[])"
    data = decompose_location(method)
    class_name = data["class_name"]
    method_name = data["method_name"]
    repo = Repo("repos/" + project)
    get_source_file(repo, class_name)


# get each class's source code
import functools


def get_children(node, fn):
    if isinstance(fn, str):
        return [c for c in node.children if c.type == fn]
    else:
    return [c for c in node.children if fn(c)]


def get_child(node, fn, none_default=False):
    if none_default:
        return next(iter(get_children(node, fn)), None)
    else:
        return next(iter(get_children(node, fn)))


def get_parameter_types(method):
    formal_parameters = get_child(method, lambda n: n.type == "formal_parameters")
    params = list(get_children(formal_parameters, lambda n: n.is_named))
    param_types = []
    for p in params:
        typ = get_children(p, lambda n: n.is_named)[0]
        typ_text = typ.text.decode()
        typ_text = "".join(typ_text.split())
        param_types.append(typ_text)
    return param_types

def matches_parameter_types(method, trace_parameter_types):
    source_parameter_types = get_parameter_types(method)
    return all(s in t for s, t in zip(source_parameter_types, trace_parameter_types))

def test_parameter_types():
    tree = parser.parse("""public class Foo { // 0
    public void bar() { // 1
         // 2
    } // 3
    public void bar(int baz) { // 4
         // 5
    } // 6
    public <t> void bar(int gam, t gee) { // 7
         // 8
    } // 9
    public void bar(int[] boo, foo [] zoo) { // 10
         // 11
    } // 12
}""".encode())
    root = tree.root_node
    class_decl = get_child(root, lambda n: n.type == "class_declaration")
    class_body = get_child(class_decl, lambda n: n.type == "class_body")
    # class_block = get_child(class_decl, lambda n: n.type == "block")
    methods = get_children(class_body, lambda n: n.type == "method_declaration")
    for method_node in methods:
        print_node(method_node)
        print(get_parameter_types(method_node))
    print(get_matching_method(class_body, "bar", None, ["int", "t"]))

def get_matching_method(class_body, method_name, lineno, entry_lineno, parameter_types):
    methods = get_children(class_body, lambda c: c.type == "method_declaration")
    for method in methods:
        method_ident = get_child(method, lambda c: c.type == "identifier")
        if method_ident.text.decode() == method_name:
            start_line = method.start_point[0]+1
            end_line = method.end_point[0]+1
            first_stmt = get_first_stmt_lineno(method)
            if (
            lineno is None or (start_line <= lineno <= end_line)
            ):
                if (
            parameter_types is None or matches_parameter_types(method, parameter_types)
        ):
            return method


def return_method(class_name, method_name, lineno, entry_lineno, parameter_types):
    def fn(node, class_name, method_name, lineno, entry_lineno, parameter_types, **kwargs):
        decl_nodes = {
            "class_declaration": "class_body",
            "enum_declaration": "enum_body",
        }
        if node.type in decl_nodes.keys():
            ident = get_child(node, lambda c: c.type == "identifier")
            if ident.text.decode() == class_name:
                body_type = decl_nodes[node.type]
                class_body = get_child(node, lambda c: c.type == body_type)
                if node.type == "enum_declaration":
                    class_body = get_child(
                        class_body, lambda c: c.type == "enum_body_declarations"
                    )
                # print("FOUND CLASS", node)
                # if is_inner_class:
                #     return dfs(class_body, fn=return_innerclass_method)
                # else:
                #     return get_matching_method(class_body, method_name, lineno)
                return get_matching_method(class_body, method_name, lineno, parameter_types)

    return functools.partial(
        fn, class_name=class_name, method_name=method_name, lineno=lineno, entry_lineno=entry_lineno, parameter_types=parameter_types
    )


def dfs(node, fn, indent=0):
    result = fn(node, indent=indent)
    if result:
        return result
    else:
        for ch in node.children:
            result = dfs(ch, fn, indent + 1)
            if result:
                return result


def print_node(node, indent=0, return_string=False, **kwargs):
    if return_string:
        output = io.StringIO()
    else:
        output = None
    text = node.text.decode()
    if "\n" in text:
        text = text.splitlines(keepends=False)[0] + "..."
    print(" " * (indent * 2), node, text, file=output)
    if return_string:
        return output.getvalue()


def get_method_node(
    actual_filepath, class_name_fq, method_name, lineno, entry_lineno, parameter_types, do_print=False
):
    if "." in class_name_fq:
        class_name = class_name_fq.rsplit(".", maxsplit=1)[1]
    else:
        class_name = class_name_fq
    tree = parse_file(actual_filepath)

    if do_print:
        dfs(tree.root_node, fn=print_node)
    method_node = dfs(tree.root_node, fn=return_method(class_name, method_name, lineno, entry_lineno, parameter_types))

    if method_node is None:
        log.debug(f"NO SUCH METHOD {actual_filepath=} {class_name=} {method_name=} {lineno=} {entry_lineno=} {parameter_types=}")

    return method_node


def get_method_type(method_node):
    block = get_child(method_node, lambda n: n.type == "block", none_default=True)
    if block is None:
        return "no_body"
    block_stmts = get_children(block, lambda n: n.is_named)
    if len(block_stmts) == 1 and block_stmts[0].type == "return_statement":
        return "forward"
    return "normal"


def test_get_method_node():
    project = "apache-commons-configuration"
    method = "org.apache.commons.configuration2.tree.InMemoryNodeModel$1.visitBeforeChildren(java.lang.Object, org.apache.commons.configuration2.tree.NodeHandler)"
    data = decompose_location(method)
    class_name = data["class_name"]
    method_name = data["method_name"]
    repo = Repo("repos/" + project)
    src_fpath = get_source_file(repo, class_name)
    get_method_node(src_fpath, class_name, method_name, 160)


def is_not_permeable(n):
    if not n.is_named:
        return False
    elif n.type in ("block", "line_comment", "block_comment"):
        return False
    elif n.type == "local_variable_declaration":
        var_decl = get_children(n, lambda n: n.type == "variable_declarator")
        for decl in var_decl:
            assignment_operator = get_child(decl, lambda n: n.type == "=", none_default=True)
            if assignment_operator is not None:
                return True
        return False
    else:
        return True


def get_first_stmt(method_node):
    block = get_child(method_node, lambda n: n.type == "block")
    first_stmt = get_child(block, is_not_permeable)
    while first_stmt.type in ("try_statement",):
        try_block = get_child(first_stmt, lambda n: n.type == "block")
        first_stmt = get_child(try_block, is_not_permeable)
    return first_stmt


def test_get_first_stmt_vardecl():
    project = "apache-commons"
    class_name = "ArchiveUtils"
    method_name = "matchAsciiBuffer"
    repo = Repo("repos/" + project)
    src_fpath = get_source_file(repo, class_name)[0]
    method_node = get_method_node(src_fpath, class_name, method_name, 76)
    assert get_first_stmt(method_node).start_point[0]+1 == 76


def test_get_first_stmt_linecomment():
    project = "apache-commons"
    class_name = "org.apache.commons.compress.archivers.tar.TarUtils"
    method_name = "exceptionMessage"
    repo = Repo("repos/" + project)
    src_fpath = get_source_file(repo, class_name)[0]
    method_node = get_method_node(src_fpath, class_name, method_name, 258)
    assert get_first_stmt(method_node).start_point[0]+1 == 258


def test_get_first_stmt():
    method_node = get_method_node("projects/apache-commons/CompressZipFuzzer.java", "CompressZipFuzzer", "fuzzerTestOneInput", 30)
    assert get_first_stmt(method_node).start_point[0]+1 == 30


if __name__ == "__main__":
    from git import Repo

    repo = Repo("repos/angus-mail")
    fpath = get_source_file(repo, "com.sun.mail.util.ASCIIUtility")
    method1 = get_method_node(fpath, "com.sun.mail.util.ASCIIUtility", "parseInt", 45)
    method2 = get_method_node(fpath, "com.sun.mail.util.ASCIIUtility", "parseInt", 116)
    fwd1 = is_forward(method1)
    print(method1, fwd1)
    fwd2 = is_forward(method2)
    print(method2, fwd2)

    from git import Repo

    try:
        get_source_file(
            Repo(
                "/home/benjis/code/bug-benchmarks/oss-fuzz/repos/apache-commons-configuration"
            ),
            "org.apache.commons.text.lookup.FunctionStringLookup",
        )
    except AssertionError:
        traceback.print_exc()
    get_source_file(
        Repo("/home/benjis/code/bug-benchmarks/oss-fuzz/repos/apache-commons-text"),
        "org.apache.commons.text.lookup.FunctionStringLookup",
    )

    # no such method checker-framework /home/benjis/code/bug-benchmarks/oss-fuzz/repos/checker-framework/checker-qual/src/main/java/org/checkerframework/checker/formatter/qual/ConversionCategory.java org.checkerframework.checker.formatter.qual.ConversionCategory fromConversionChar 198
    src_fpath = "/home/benjis/code/bug-benchmarks/oss-fuzz/repos/checker-framework/checker-qual/src/main/java/org/checkerframework/checker/formatter/qual/ConversionCategory.java"
    class_name = "org.checkerframework.checker.formatter.qual.ConversionCategory"
    method_name = "fromConversionChar"
    lineno = 198
    print(get_method_node(src_fpath, class_name, method_name, lineno, do_print=False))

    # no such method apache-commons-io /home/benjis/code/bug-benchmarks/oss-fuzz/repos/apache-commons-io/src/main/java/org/apache/commons/io/function/IOConsumer.java org.apache.commons.io.function.IOConsumer forEach 106
    # no such method apache-commons-io /home/benjis/code/bug-benchmarks/oss-fuzz/repos/apache-commons-io/src/main/java/org/apache/commons/io/StandardLineSeparator.java org.apache.commons.io.StandardLineSeparator getString 72
    # no such method apache-commons-io /home/benjis/code/bug-benchmarks/oss-fuzz/repos/apache-commons-io/src/main/java/org/apache/commons/io/StandardLineSeparator.java org.apache.commons.io.StandardLineSeparator $values 28
    src_fpath = "/home/benjis/code/bug-benchmarks/oss-fuzz/repos/apache-commons-io/src/main/java/org/apache/commons/io/function/IOConsumer.java"
    class_name = "org.apache.commons.io.function.IOConsumer"
    method_name = "forEach"
    lineno = 106
    print(get_method_node(src_fpath, class_name, method_name, lineno, do_print=False))
    src_fpath = "/home/benjis/code/bug-benchmarks/oss-fuzz/repos/apache-commons-io/src/main/java/org/apache/commons/io/StandardLineSeparator.java"
    class_name = "org.apache.commons.io.StandardLineSeparator"
    method_name = "getString"
    lineno = 72
    print(get_method_node(src_fpath, class_name, method_name, lineno, do_print=False))
    src_fpath = "/home/benjis/code/bug-benchmarks/oss-fuzz/repos/apache-commons-io/src/main/java/org/apache/commons/io/StandardLineSeparator.java"
    class_name = "org.apache.commons.io.StandardLineSeparator"
    method_name = "$values"
    lineno = 28
    print(get_method_node(src_fpath, class_name, method_name, lineno, do_print=False))

    # no such method src_fpath=PosixPath('/home/benjis/code/bug-benchmarks/oss-fuzz/repos/slf4j-api/slf4j-api/src/main/java/org/slf4j/LoggerFactory.java') project='greenmail' repo=<git.repo.base.Repo '/home/benjis/code/bug-benchmarks/oss-fuzz/repos/slf4j-api/.git'> class_name='org.slf4j.LoggerFactory' method_name='getLogger'
    src_fpath = "/home/benjis/code/bug-benchmarks/oss-fuzz/repos/slf4j-api/slf4j-api/src/main/java/org/slf4j/LoggerFactory.java"
    class_name = "org.slf4j.LoggerFactory"
    method_name = "getLogger"
    lineno = 45
    print(get_method_node(src_fpath, class_name, method_name, lineno, do_print=False))

