#%%
# source: https://gist.github.com/nrosner/70bed930684f467dddd5fc68cbf39e82

import sys, os, re, zipfile, subprocess
import json
import tqdm
import glob

# Rudimentary parsing of javap output
regex_type = r'[a-zA-Z0-9.<>,?& $[\]_]+'
regex_type_no_generic = r'[a-zA-Z0-9.?$[\]_]+'
regex_class = r'(?:(public|private|protected) )?((?:(?:static|abstract|final) ?)*)(class) (' + regex_type_no_generic + r')'
regex_method = r'(?:(public|private|protected) )?((?:static|abstract|final|synchronized) ?)*(?:\<[^>]+\>\s*)(?:' + regex_type + r' )([$a-zA-Z0-9_]+)\(([^\)]*)\)(?: throws .*)?;'
regex_method_no_generic = r'(?:(public|private|protected)\s*)?((?:static|abstract|final|synchronized)\s*)*(?:' + regex_type + r' )?([$a-zA-Z0-9_]+)\(([^\)]*)\)(?: throws .*)?;'
regex_field = r'(?:(public|private|protected)\s*)?((?:(?:static|abstract|final|volatile|transient)\s*)*)(' + regex_type + r') ([$a-zA-Z0-9_$]+);'
RE_TYPE = re.compile(regex_type)
RE_CLASS = re.compile(regex_class)
RE_METHOD = re.compile(regex_method)
RE_METHOD_NO_GENERIC = re.compile(regex_method_no_generic)
RE_FIELD = re.compile(regex_field)
# RE_COMPILEDFROM = re.compile(r'''Classfile jar:file://.*!/.*.class
# \s+Last modified .*
# \s+MD5 checksum .*
# \s+Compiled from ".*\.java"
# ''', flags=re.MULTILINE)
RE_HEADER = re.compile(r'''(?:Compiled from ".*\.(?:java|kt|groovy)"\n|}\n)+''', flags=re.MULTILINE)
FQ_TYPE_PREFIX = re.compile(r'((?:[a-zA-Z0-9_$]+\.)+)([a-zA-Z0-9_$]+)')


def classnamesfromjar(jarfilepath):
    '''Return list of fully-qualified classnames.'''
    with zipfile.ZipFile(jarfilepath, 'r') as zf:
        for zi in zf.infolist():
            fn = zi.filename
            if fn.endswith('.class'):
                dotted = fn.replace('/', '.')
                assert dotted.endswith('.class')
                yield dotted[:len(dotted)-len('.class')]

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
    
def decompose(param):
    BRACKETS_RE = re.compile(r'([^\[]+)(\[\])*')
    param = BRACKETS_RE.match(param).group(1)
    if "<" in param:
        param = param[:param.index("<")]
    return param

def test_decompose():
    assert "int" == decompose("int")
    assert "byte" == decompose("byte[]")
    assert "java.lang.String" == decompose("java.lang.String[][]")
    
def check_params(params):
    primitives = (
        "boolean", "Boolean",
        "byte", "Byte",
        "short", "Short",
        "long", "Long",
        "int", "Int",
        "float", "Float",
        "char", "Char",
        "double", "Double",
        "java.lang.String", "java.lang.CharSequence",
        "java.io.ByteArrayInputStream", "java.io.InputStream",
        "java.util.Map", "java.util.Map", "java.lang.Class", "java.lang.reflect.Method",
    )
    return len(params) == 0 or all(decompose(p) in primitives for p in params)
    
def check_params2(params):
    primitives = (
        "boolean", "Boolean",
        "byte", "Byte",
        "short", "Short",
        "long", "Long",
        "int", "Int",
        "float", "Float",
        "char", "Char",
        "double", "Double",
        "java.lang.String", "java.lang.CharSequence",
        "java.util.List", "java.util.ArrayList",
    )
    return len(params) == 0 or all(decompose(p) in primitives for p in params)

def test_check_params():
    assert check_params(["int"])
    assert check_params(["int", "java.lang.String"])
    assert check_params(["byte[][]", "java.lang.String[]"])
    assert not check_params(["byte[][]", "Foo", "java.lang.String[]"])

def test_header_split():
    expected = ['public class Foo {\n', 'public class Bar {\n}']
    assert expected == split_header("""Compiled from "foo.java"
public class Foo {
}
public class Bar {
}""")
    assert expected == split_header("""Compiled from "foo.java"
public class Foo {
}
Compiled from "foo.java"
public class Bar {
}""")
    assert expected == split_header("""public class Foo {
}
Compiled from "foo.java"
public class Bar {
}""")
    assert expected == split_header("""public class Foo {
}
public class Bar {
}""")

def split_header(s):
    return list(filter(None, RE_HEADER.split(s)))

def runjavap(jarfilepath):
    '''Run javap on this jar for all the classes in the jar. Return the output of the javap command.'''
    classnames = list(classnamesfromjar(jarfilepath))
    classnames_chunks = chunks(classnames, 1000)
    result_text = ""
    for chunk in classnames_chunks:
        result_text += runjavap_aux(classpath=jarfilepath, classnames=chunk)
    if result_text.startswith("Error occurred"):
        print("ERROR:", jarfilepath)
        print(result_text)
        return
    split_text = split_header(result_text)
    # print(json.dumps(split_text, indent=4))
    # assert split_text[-1] == '', f"split text should be ended with empty string.\nstring={result_text}\nsplit={json.dumps(split_text, indent=2)}''"
    # split_text = split_text[:-1]
    for i in range(0, len(split_text), 1):
        code = split_text[i]
        lines = []
        lines = code.splitlines()
        class_line = lines[0].strip()
        tokens = class_line.split()
        if "module" in tokens or "interface" in tokens:
            continue
        class_m = RE_CLASS.match(class_line)
        if class_m is None:
            print("NO CLASS MATCH:", class_line)
        else:
            methods = []
            class_name = class_m.group(4)
            for i, body_line in enumerate(lines[1:]):
                # body_line = re.sub(r'<[^>]+>', lambda s: "".join(s.group().split()), body_line, flags=re.DOTALL)
                body_line = body_line.strip()
                method_m = RE_METHOD.match(body_line)
                if method_m is None:
                    method_m = RE_METHOD_NO_GENERIC.match(body_line)
                if method_m is not None:
                    groups = method_m.groups()
                    name = groups[2]
                    params = groups[3:]
                    params = [p.strip() for p in filter(None, params)]
                    all_fuzzable = check_params(params)
                    all_primitive = check_params2(params)
                    # if all_primitive:
                    #     print("ALL PRIMITIVE:", params)
                    # else:
                    #     print("SOME NOT PRIMITIVE:", params)
                    fq_method_name = class_name + "::" + name + "(" + ",".join(params) + ")"
                    methods.append({
                        "method": fq_method_name,
                        "all_fuzzable": all_fuzzable,
                        "all_primitive": all_primitive,
                    })
                else:
                    # print("CLASS:", class_name)
                    class_name_for_ctor = re.sub(r'<.*>', r'', class_name.replace(r".", r"\.").replace(r'$', r'\$'))
                    regex_ctor = r'(?:(public|private|protected) )?((?:static|abstract|final|synchronized) ?)*' + regex_type + r'\s*' + class_name_for_ctor + r'\(([^\)]*)\)(?: throws .*)?;'
                    REGEX_CTOR = re.compile(regex_ctor)
                    if REGEX_CTOR.match(body_line):
                        # print("CTOR for class", class_name + ":", body_line)
                        pass
                    else:
                        regex_ctor_no_generic = r'(?:(public|private|protected) )?((?:static|abstract|final|synchronized) ?)*' + class_name_for_ctor + r'\(([^\)]*)\)(?: throws .*)?;'
                        REGEX_CTOR_NO_GENERIC = re.compile(regex_ctor_no_generic)
                        if REGEX_CTOR_NO_GENERIC.match(body_line):
                            pass
                        elif RE_FIELD.match(body_line):
                            # print("FIELD:", body_line)
                            pass
                        else:
                            if body_line not in ("static {};", "static strictfp {};"):
                                print(f"NO MATCH ({class_name}):", body_line)
                                print("METHOD:", regex_method)
                                print("METHOD NO GENERIC:", regex_method_no_generic)
                                print("CTOR:", regex_ctor)
                                print("CTOR NO GENERIC:", regex_ctor_no_generic)
            # if len(methods) == 0:
            #     print("NO METHODS:", class_name, class_m, class_m.groups())
            yield class_name, methods

def runjavap_aux(classpath, classnames):
    '''Run javap on the given classpath for the given classnames. Return the output of the javap command.'''
    cmdarglist = [
        'javap',
        '-classpath', classpath
    ] + list(classnames)
    print("COMMAND:", " ".join(cmdarglist))
    p = subprocess.Popen(cmdarglist, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    tup_output = p.communicate()
    stdout = tup_output[0]
    stderr = tup_output[1]
    return stdout

if __name__ == '__main__':
    jars = glob.glob("build/out/**/*.jar")
    # jars = glob.glob("build_test/out/**/*.jar")
    # jars = list(glob.glob("build/out/*/*.jar"))[:2]
    # jars = ["build/out/osgi/ant-contrib-0.6.jar"]
    # jars = ["build/out/osgi/batik-all-1.7.jar"]
    print("JARS:", json.dumps(jars))
    for jarpathname in tqdm.tqdm(jars):
        try:
            if jarpathname.endswith("jazzer_agent_deploy.jar"):
                continue
            classes_methods = runjavap(jarpathname)
            result = {}
            for class_name, data in classes_methods:
                # print(jarpathname, "Class:", class_name, "Methods:", len(methods))
                # for m in methods:
                #     print(class_name, m)
                result[class_name] = data
            result_file = jarpathname + ".class_manifest.json"
            # print("PRINT TO FILE:", result_file)
            # print(json.dumps(result, indent=4))
            with open(result_file, "w") as f:
                json.dump(result, f, indent=4)
        except AssertionError:
            print("ERROR processing", jarpathname)
            raise
