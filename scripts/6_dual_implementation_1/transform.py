#%%
from tree_sitter import Language, Parser
from git import Repo
import os

project_root = Repo(__file__, search_parent_directories=True)
os.chdir(os.path.dirname(project_root.git_dir))

os.makedirs("vendor", exist_ok=True)
os.makedirs("build", exist_ok=True)

if not os.path.exists("vendor/tree-sitter-java"):
    Repo.clone_from("https://github.com/tree-sitter/tree-sitter-java.git", "vendor/tree-sitter-java")

Language.build_library(
  # Store the library in the `build` directory
  'build/tree-sitter-languages.so',

  # Include one or more languages
  [
    'vendor/tree-sitter-java'
  ]
)

JAVA_LANGUAGE = Language('build/tree-sitter-languages.so', 'java')

parser = Parser()
parser.set_language(JAVA_LANGUAGE)

#%%
with open("projects/angus-mail/ASCIIUtilityFuzzer_original.java", "rb") as f:
    code = f.read()
    ast = parser.parse(code)
ast.root_node

#%%
# Get fuzzer class
fuzzer_class = None
q = [ast.root_node]
while len(q) > 0:
    n = q.pop(0)
    if n.type == "class_declaration":
        print("CLASS DECLARATION", n, n.children)
        for child in n.children:
            if child.type == "identifier" and child.text.decode().endswith("Fuzzer"):
                print("FUZZER CLASS", child)
                fuzzer_class = n
    q.extend(n.children)
fuzzer_class
#%%
# Get fuzzer harness method
class_body = next(n for n in fuzzer_class.children if n.type == "class_body")

fuzzer_method = None
for n in class_body.children:
    if n.type == "method_declaration":
        print("METHOD DECLARATION", n, n.children)
        for child in n.children:
            if child.type == "identifier" and child.text.decode() == "fuzzerTestOneInput":
                fuzzer_method = n

fuzzer_method
#%%
# Modify method to add header/tail
block = next(n for n in fuzzer_method.children if n.type == "block")
header = """\ntry { data = new MyRecordedFuzzedDataProvider(data, "", "ASCIIUtilityFuzzer"); try { ((MyRecordedFuzzedDataProvider)data).markBeginFuzzer();"""
tail = """} finally { ((MyRecordedFuzzedDataProvider)data).markEndFuzzer(); ((MyRecordedFuzzedDataProvider)data).close(); } } catch (Exception ex) { }\n"""
inserts = []
inserts.append((block.start_byte+1, header))
inserts.append((block.end_byte-2, tail))
inserts = sorted(inserts, key=lambda i: i[0])

with open("projects/angus-mail/ASCIIUtilityFuzzer_original.java", "rb") as f:
    code = f.read()
offset = 0
for byte, to_insert in inserts:
    byte = byte + offset
    code = code[:byte] + to_insert.encode() + code[byte:]
    offset += len(to_insert)

print(code.decode())

#%%
# TODO Get all calls inside harness, instrument
# TODO Handle no-use calls

# %%
