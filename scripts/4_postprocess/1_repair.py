# %% [markdown]
# 1. PARSE XML FILES
# 2. TURN INTO TREE
# 3. IF FAILS, PARSE AS MANY OF THE ENTRIES AS POSSIBLE

# %%
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import shutil
import os

import git

repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)

# srcpaths=(
#     "traces-1m-worker_3_overnight_portclash",
#     "traces-1m-worker_4_overnight_fixportclash",
# )
srcpaths=(
    "./media/benjis/basilisk/Files/biggie/oss-fuzz/fuzz_10m_trace_3h/trace_run_3_success_3h/traces-10m/logs-xmls/",
)

xmls = []
for d in srcpaths:
    l = list(Path(d).glob("*.xml"))
    xmls += l
print(len(xmls), "XML files found,", len(set([f.name for f in xmls])), "unique. duplicates =", [f for f in xmls if [g.name for g in xmls].count(f.name) > 1])

# %%
dstdir=Path("postprocessed_xmls")
dstdir.mkdir(exist_ok=True)

# if dstdir.exists():
#     shutil.rmtree(dstdir)
# dstdir.mkdir()

# %%
successes = (dstdir/"1_repair_success_1.txt").read_text().splitlines(keepends=False)
len(successes)

# %%
failed_1 = [p for p in xmls if str(p) not in successes]
assert len(failed_1) == 150
failed_1 = failed_1[105:]
len(failed_1)

# %%
#!pip install tqdm jupyter ipywidgets

# %%
import tqdm as tqdm

successes_1 = []
failed_1 = []
for fpath in tqdm.tqdm(xmls):
    if ".repair." in fpath.name:
        continue
    try:
        root = ET.parse(fpath).getroot()
        # print(fpath, "parsed successfully")
        successes_1.append(fpath)
        shutil.copyfile(fpath, dstdir/fpath.name)
    except ET.ParseError as ex:
        # print("exception", type(ex).__name__, ex, "parsing", fpath)
        failed_1.append(fpath)

print("ROUND 1:", len(failed_1), "files failed parsing")
(dstdir/"1_repair_success_1.txt").write_text("\n".join(map(str, successes_1)))

# %%
import tqdm as tqdm

fuzzer_start = re.compile(r'''<call[^>]*method="[^."]+.fuzzerTestOneInput\([^)]+\)"[^>]*''')
fuzzer_almost_end = re.compile(r'''<tracepoint[^>]+>''')
method_re = re.compile(r'''method="[^."]+.fuzzerTestOneInput\([^)]+\)"''')
exit_re = re.compile(r'''type="exit"''')
fuzzer_real_end = re.compile(r'''</call>''')


from xml.dom import minidom
from xml.parsers.expat import ExpatError

def prettify(rough_string):
    """Return a pretty-printed XML string for the Element.
    """
    # rough_string = ET.tostring(elem)
    reparsed = minidom.parseString(rough_string)
    
    # text = reparsed.toprettyxml(indent=" " * 2)
    # return "".join(text.splitlines(keepends=True)[1:])
    
    # return reparsed.childNodes[0].toprettyxml(indent=" " * 2)
    
    return reparsed.toprettyxml(indent="  ")

def recover_functions(fpath):
    with open(fpath) as f:
        xmlstring = f.read()
    xmllines = xmlstring.splitlines(keepends=True)
    it = iter(xmllines)
    repair_path = dstdir/(str(fpath.name) + ".repair.xml")
    failed_functions = 0
    all_functions = 0
    with open(repair_path, "w") as outf:
        with tqdm.tqdm(it, total=len(xmllines), desc="deconstruct into fuzzer target calls") as pbar:
            it = iter(pbar)
            fuzz_functions = []
            current_fuzz_function = None
            try:
                outf.write(next(it))
                while True:
                    line = next(it)
                    if fuzzer_start.search(line):
                        # print("start at", line)
                        # start fuzzed function
                        current_fuzz_function = []
                    if current_fuzz_function is not None:
                        current_fuzz_function.append(line)
                    m = fuzzer_almost_end.search(line)
                    if m:
                        tag = m.group(0)
                        if method_re.search(tag) and exit_re.search(tag):
                            # print("end at", line)
                            while True:
                                line = next(it)
                                # print("search end", line)
                                current_fuzz_function.append(line)
                                if fuzzer_real_end.search(line):
                                    # cap off fuzzed function
                                    # print("end", line)
                                    all_functions += 1
                                    try:
                                        func_xml = "".join(current_fuzz_function)
                                        # ET.fromstring(func_xml)
                                        # print(func_xml)
                                        func_xml = "".join(prettify(func_xml).splitlines(keepends=True)[1:])
                                        outf.write(func_xml + "\n")
                                    except (ExpatError, ET.ParseError):
                                        failed_functions += 1
                                    pbar.set_postfix({"all": all_functions, "failed": failed_functions})
                                    break
            except StopIteration:
                pass
        outf.write("</trace>")
    
#     print("found", len(fuzz_functions), "functions")

#     success_functions = []
#     failed_functions = 0
#     pbar = tqdm.tqdm(fuzz_functions, desc="parse individual fuzzer targets")
#     for fuzzed_function in pbar:
#         try:
#             root = ET.ElementTree(ET.fromstring(fuzzed_function)).getroot()
#             # ET.indent(root, space="\t", level=0)
#             success_functions.append(ET.tostring(root, encoding='unicode', method='xml'))
#         except ET.ParseError as ex:
#             # print("function exception", type(ex), ex, "parsing", fpath)
#             # print(fuzzed_function)
#             failed_functions += 1
#         pbar.set_postfix({"failed": failed_functions})
    # print("failed", failed_functions, "out of", all_functions, "functions")

#     success_text = "\n".join((xmllines[0], "".join(success_functions), "</trace>"))
#     success_text = prettify(success_text)
#     repair_path.write_text("".join(success_text))
    return repair_path

# repair_path = recover_functions("traces-1m-worker_3_overnight_portclash/trace-apache-commons-cli-ParserFuzzer.xml")
# root = ET.parse(repair_path).getroot()
# repair_path

# %%
successes_2 = []
failed_2 = []
for fpath in tqdm.tqdm(failed_1, position=1, desc="round 2"):
    repair_path = recover_functions(fpath)
    try:
        root = ET.parse(repair_path).getroot()
        successes_2.append(repair_path)
        shutil.copyfile(repair_path, dstdir/repair_path.name)
    except ET.ParseError as ex:
        print("exception", type(ex), ex, "parsing", fpath)
        failed_2.append(repair_path)

print("ROUND 2:", len(failed_2), "files failed parsing")
(dstdir/"1_repair_success_2_part2.txt").write_text("\n".join(map(str, successes_2)))

# root = ET.parse('traces-1m/trace-angus-mail-BASE64EncoderStreamFuzzer.xml').getroot()
# root

# %%
all_files = successes_1 + successes_2

# %%
with open(dstdir/"1_repair_success_all.txt", "w") as f:
    f.write("\n".join(map(str, all_files)))


