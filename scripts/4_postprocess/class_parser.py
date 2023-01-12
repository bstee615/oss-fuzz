#%%
import logging
import os
import traceback
from pathlib import Path
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




def decompose_location(location):
    """
    Split a location org.benjis.Foo$Bar.baz() into its components "org.benjis.Foo", "bar", "Bar" (inner class)
    """
    method_id = location.split("(")[0]
    class_name, method_name = method_id.rsplit(".", maxsplit=1)
    dollar_idx = class_name.find("$")
    after_dollar_part = None
    if dollar_idx != -1:
        class_name, after_dollar_part = class_name.split("$", maxsplit=1)
    return {
        "class_name": class_name,
        "method_name": method_name,
        "inner_class_name": after_dollar_part,
    }


def test_decompose_location():
    decompose_location(
        "ASCIIUtilityFuzzer.fuzzerTestOneInput(com.code_intelligence.jazzer.api.FuzzedDataProvider)"
    )
    decompose_location(
        "org.apache.commons.configuration2.tree.InMemoryNodeModel$1.visitBeforeChildren(java.lang.Object, org.apache.commons.configuration2.tree.NodeHandler)"
    )


def get_source_file(repo, class_name_fq):
    class_filepath = class_name_fq.replace(".", "/")
    actual_filepaths = list(
        Path(repo).rglob("*/" + class_filepath + ".java")
    )
    assert len(actual_filepaths) >= 1, (actual_filepaths, repo, class_name_fq)
    actual_filepaths = sorted(actual_filepaths, key=lambda p: str(p.absolute()))
    # if len(actual_filepaths) > 1:
        # if class_name_fq.startswith("com.google.common"):
        #     actual_filepaths = [f for f in actual_filepaths if f.is_relative_to(Path(repo.working_dir)/"guava")]
        # actual_filepaths = sorted(actual_filepaths, key=lambda p: str(p.absolute()))
        # for i in range(1, len(actual_filepaths)):
            # if not filecmp.cmp(actual_filepaths[i-1], actual_filepaths[i]):
                # log.warn(f"multiple paths. {actual_filepaths=} {repo=} {class_name_fq=}")
                # break
        # log.debug(f"multiple paths. {actual_filepaths=} {repo=} {class_name_fq=}")
    return actual_filepaths


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
    return [c for c in node.children if fn(c)]


def get_child(node, fn, none_default=False):
    if none_default:
        return next(iter(get_children(node, fn)), None)
    else:
        return next(iter(get_children(node, fn)))


def get_matching_method(class_body, method_name, lineno):
    methods = get_children(class_body, lambda c: c.type == "method_declaration")
    for method in methods:
        method_ident = get_child(method, lambda c: c.type == "identifier")
        start_line = method.start_point[0]
        end_line = method.end_point[0]
        if method_ident.text.decode() == method_name and (
            lineno is None or (start_line <= lineno <= end_line)
        ):
            return method


# def return_innerclass_method(method_name, lineno):
#     def fn(node, method_name, lineno):
#         if node.type == "class_declaration":
#     return functools.partial(fn, method_name=method_name, lineno=lineno)


def return_method(class_name, method_name, lineno):
    def fn(node, class_name, method_name, lineno, **kwargs):
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
                return get_matching_method(class_body, method_name, lineno)

    return functools.partial(
        fn, class_name=class_name, method_name=method_name, lineno=lineno
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


def print_node(node, indent=0, **kwargs):
    text = node.text.decode()
    if "\n" in text:
        text = text.splitlines(keepends=False)[0] + "..."
    print(" " * (indent * 2), node, text)


def get_method_node(
    actual_filepath, class_name_fq, method_name, lineno, do_print=False
):
    if "." in class_name_fq:
        class_name = class_name_fq.rsplit(".", maxsplit=1)[1]
    else:
        class_name = class_name_fq
    tree = parse_file(actual_filepath)

    if do_print:
        dfs(tree.root_node, fn=print_node)
    method_node = dfs(tree.root_node, fn=return_method(class_name, method_name, lineno))
    # if method_node is None:
    #     # TODO: FIX THIS SLOPPY SOLUTION.
    #     method_node = dfs(tree.root_node, fn=return_method(class_name, method_name, None))

    if method_node is None:
        log.debug(f"NO SUCH METHOD {actual_filepath=} {class_name=} {method_name=} {lineno=}")

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

