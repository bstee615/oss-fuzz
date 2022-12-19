#%%
import tqdm as tqdm
import xml.etree.ElementTree as ET
import re
from pathlib import Path

import os
import git
repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)

# dstdir = Path("postprocessed_xmls_debug")
# xml_file = Path("/run/media/benjis/basilisk/Files/biggie/oss-fuzz/fuzz_10m_trace_3h/trace_run_3_success_3h/traces-10m/logs-xmls")/"trace-apache-commons-bcel-BcelFuzzer.xml"

#%%
fuzzer_start = re.compile(r'''<call[^>]*method="[^("]+.fuzzerTestOneInput\([^)]+\)"[^>]*''')

from xml.dom import minidom
from xml.parsers.expat import ExpatError

def recover_functions_simple(fpath, dstdir):
    repair_path = dstdir/(str(fpath.name) + ".repair.xml")
    if repair_path.exists():
        return repair_path
    
#     with open(fpath) as f:
#         num_lines = sum(1 for line in tqdm.tqdm(f, desc=f"count lines ({fpath.name})"))
    last_fuzzer_start = None
    with open(fpath) as f:
        i = 0
        it = iter(f)
        failed_functions = 0
        all_functions = 0
        with tqdm.tqdm(it, total=None, desc=f"chop final fuzzer target call ({fpath.name})") as pbar:
            it = pbar
            fuzz_functions = []
            current_fuzz_function = None
            for i, line in enumerate(it):
                m = fuzzer_start.search(line)
                if m is not None:
#                     print("MATCH", m, m.start(), m.span())
                    j = m.start()
                    last_fuzzer_start = (i, j)
#     print("LFS", last_fuzzer_start)
    if last_fuzzer_start is None:
        print("ERROR: last_fuzzer_start is None", fpath)
        return None
    
    with open(fpath) as f, open(repair_path, "w") as outf:
        it = iter(f)
        with tqdm.tqdm(it, total=last_fuzzer_start[0], desc=f"write file ({fpath.name})") as pbar:
            it = pbar
            for i, line in enumerate(it):
#                 print(i)
                if i == last_fuzzer_start[0]:
#                     print("LINE:")
#                     print(line)
                    line_chopped = line[:last_fuzzer_start[1]]
#                     print("CHOPPED:")
#                     print(line_chopped)
                    outf.write(line_chopped)
                    break
                else:
                    outf.write(line)
            outf.write("</trace>")
        
    return repair_path

xml_file = Path("/run/media/benjis/basilisk/Files/biggie/oss-fuzz/fuzz_10m_trace_3h/trace_run_3_success_3h/traces-10m/logs-xmls/trace-spring-security-NimbusJwtEncoderFuzzer.xml")
recover_functions_simple(xml_file, Path("postprocessed_xmls_debug"))

#%%
fuzzer_start = re.compile(r'''<call[^>]*method="[^("]+.fuzzerTestOneInput\([^)]+\)"[^>]*''')
fuzzer_almost_end = re.compile(r'''<tracepoint[^>]+>''')
method_re = re.compile(r'''method="[^("]+.fuzzerTestOneInput\([^)]+\)"''')
exit_re = re.compile(r'''type="exit"''')
fuzzer_real_end = re.compile(r'''</call>''')


from xml.dom import minidom
from xml.parsers.expat import ExpatError

def prettify(rough_string):
    """Return a pretty-printed XML string for the Element.
    """
    reparsed = minidom.parseString(rough_string)
    
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

    return repair_path

recover_functions(xml_file)

#%%
orig_file = "/run/media/benjis/basilisk/Files/biggie/oss-fuzz/fuzz_10m_trace_3h/trace_run_3_success_3h/traces-10m/logs-xmls/trace-apache-commons-bcel-BcelFuzzer.xml"
with open(orig_file) as f:
    it = ET.iterparse(f)
    for _ in it:
        pass
