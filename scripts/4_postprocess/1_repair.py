#!/usr/bin/env python
# coding: utf-8

# 1. PARSE XML FILES
# 2. TURN INTO TREE
# 3. IF FAILS, PARSE AS MANY OF THE ENTRIES AS POSSIBLE

# In[2]:


import traceback
import xml.etree.ElementTree as ET
from lxml import etree as ET2
from pathlib import Path
import re
import shutil
import os

import git

repo = git.Repo('.', search_parent_directories=True)
os.chdir(repo.working_tree_dir)

srcpaths=(
    "first_run_xmls/logs-xmls",
)

xmls = []
for d in srcpaths:
    l = list(Path(d).glob("*.xml"))
    l = [p for p in l if ".repair." not in p.name]
    xmls += l
print(len(xmls), "XML files found,", len(set([f.name for f in xmls])), "unique. duplicates =", [f for f in xmls if [g.name for g in xmls].count(f.name) > 1])


# In[6]:


dstdir=Path("postprocessed-xmls-lxml")


# In[7]:


if dstdir.exists():
    shutil.rmtree(dstdir)
dstdir.mkdir(exist_ok=True)


# In[15]:
def get_calls(fpath):
    for _, elem in ET2.iterparse(fpath):
        if elem.tag == "call":
            yield elem
            elem.clear()

import tqdm as tqdm
import copy
from multiprocessing import Pool
import functools

def convert_file(fpath, dstdir):
    with open(dstdir/fpath.name, "wb") as of:
        with open(fpath) as inf:
            original_calls = (l.count("<call") for l in inf)
        calls_written = 0
        of.write("<repaired-trace>\n".encode())
        try:
            it = get_calls(fpath)
            for n in it:
                n = copy.deepcopy(n)
                n.attrib["xml"] = str(fpath)
                for c in n:
                    if c.tag == "call":
                        n.remove(c)
                of.write(ET2.tostring(n, pretty_print=True))
                of.write("\n".encode())
                calls_written += 1
                del n
            return (fpath, "success", calls_written, original_calls)
        except ET.ParseError:
            return (fpath, "failure", calls_written, original_calls)
        except ET2.XMLSyntaxError:
            return (fpath, "failure", calls_written, original_calls)
        finally:
            of.write("</repaired-trace>\n".encode())

successes_1 = []
failed_1 = []
with Pool(8) as pool, open(dstdir/"1_repair.txt", "w") as rf:
    rf.write(f"fpath,result,calls_written,original_calls\n")
    with tqdm.tqdm(pool.imap_unordered(functools.partial(convert_file, dstdir=dstdir), xmls), total=len(xmls), desc="Parsing XMLs") as pbar:
        for fpath, res, calls_written, original_calls in pbar:
            if res == "success":
                successes_1.append(fpath)
            if res == "failure":
                failed_1.append(fpath)
            pbar.set_postfix({
                "success": len(successes_1),
                "failed": len(failed_1),
            })
            rf.write(",".join(str(fpath), res, calls_written, original_calls) + "\n")
            rf.flush()

print("ROUND 1:", len(failed_1), "files failed parsing")
