# %%
from pathlib import Path

from tree_sitter import Language, Parser
import os

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

#%%
import traceback

def get_source_file(repo, class_name_fq):
    class_filepath = class_name_fq.replace(".", "/")
    actual_filepaths = list(Path(repo.working_dir).rglob("*/" + class_filepath + ".java"))
    assert len(actual_filepaths) >= 1, (actual_filepaths, repo, class_name_fq)
    if len(actual_filepaths) > 1:
        print("WARNING: multiple paths. PATHS =", actual_filepaths, "REPO =", repo, "CLASSNAME =", class_name_fq)
    return actual_filepaths[0]


# %%

# get each class's source code
import functools


def get_children(node, fn):
    return [c for c in node.children if fn(c)]


def get_child(node, fn):
    return next(iter(get_children(node, fn)))

def get_matching_method(class_body, method_name, lineno):
    methods = get_children(class_body, lambda c: c.type == "method_declaration")
    for method in methods:
        method_ident = get_child(method, lambda c: c.type == "identifier")
        start_line = method.start_point[0]
        end_line = method.end_point[0]
        if method_ident.text.decode() == method_name and (lineno is None or (start_line <= lineno <= end_line)):
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
                    class_body = get_child(class_body, lambda c: c.type == "enum_body_declarations")
                # print("FOUND CLASS", node)
                # if is_inner_class:
                #     return dfs(class_body, fn=return_innerclass_method)
                # else:
                #     return get_matching_method(class_body, method_name, lineno)
                return get_matching_method(class_body, method_name, lineno)

    return functools.partial(fn, class_name=class_name, method_name=method_name, lineno=lineno)


def dfs(node, fn, indent=0):
    result = fn(node, indent=indent)
    if result:
        return result
    else:
        for ch in node.children:
            result = dfs(ch, fn, indent+1)
            if result:
                return result


def print_node(node, indent=0, **kwargs):
    text = node.text.decode()
    if "\n" in text:
        text = text.splitlines(keepends=False)[0] + "..."
    print(" " * (indent * 2), node, text)

def get_method_node(actual_filepath, class_name_fq, method_name, lineno, do_print=False):
    if "." in class_name_fq:
        class_name = class_name_fq.rsplit(".", maxsplit=1)[1]
    else:
        class_name = class_name_fq
    tree = parse_file(actual_filepath)

    if do_print:
        dfs(tree.root_node, fn=print_node)
    method_node = dfs(tree.root_node, fn=return_method(class_name, method_name, lineno))
    if method_node is None:
        # TODO: FIX THIS SLOPPY SOLUTION.
        method_node = dfs(tree.root_node, fn=return_method(class_name, method_name, None))

    return method_node

def is_forward(method_node):
    block = get_child(method_node, lambda n: n.type == "block")
    block_stmts = get_children(block, lambda n: n.is_named)
    return len(block_stmts) == 1 and block_stmts[0].type == "return_statement"



#%%
    
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
        get_source_file(Repo("/home/benjis/code/bug-benchmarks/oss-fuzz/repos/apache-commons-configuration"), 'org.apache.commons.text.lookup.FunctionStringLookup')
    except AssertionError:
        traceback.print_exc()
    get_source_file(Repo("/home/benjis/code/bug-benchmarks/oss-fuzz/repos/apache-commons-text"), 'org.apache.commons.text.lookup.FunctionStringLookup')

    # %%
    # no such method checker-framework /home/benjis/code/bug-benchmarks/oss-fuzz/repos/checker-framework/checker-qual/src/main/java/org/checkerframework/checker/formatter/qual/ConversionCategory.java org.checkerframework.checker.formatter.qual.ConversionCategory fromConversionChar 198
    src_fpath = "/home/benjis/code/bug-benchmarks/oss-fuzz/repos/checker-framework/checker-qual/src/main/java/org/checkerframework/checker/formatter/qual/ConversionCategory.java"
    class_name = "org.checkerframework.checker.formatter.qual.ConversionCategory"
    method_name = "fromConversionChar"
    lineno = 198
    print(get_method_node(src_fpath, class_name, method_name, lineno, do_print=False))

    #%%
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

    #%%
    # no such method src_fpath=PosixPath('/home/benjis/code/bug-benchmarks/oss-fuzz/repos/slf4j-api/slf4j-api/src/main/java/org/slf4j/LoggerFactory.java') project='greenmail' repo=<git.repo.base.Repo '/home/benjis/code/bug-benchmarks/oss-fuzz/repos/slf4j-api/.git'> class_name='org.slf4j.LoggerFactory' method_name='getLogger'
    src_fpath = "/home/benjis/code/bug-benchmarks/oss-fuzz/repos/slf4j-api/slf4j-api/src/main/java/org/slf4j/LoggerFactory.java"
    class_name = "org.slf4j.LoggerFactory"
    method_name = "getLogger"
    lineno = 45
    print(get_method_node(src_fpath, class_name, method_name, lineno, do_print=False))
