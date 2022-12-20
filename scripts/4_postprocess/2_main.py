import functools
import json
import traceback
import xml.etree.ElementTree as ET
from collections import defaultdict
from multiprocessing import Manager, Pool
from pathlib import Path

import tqdm
from exampleizer import *


def count_calls(xml):
    """Return the number of <call> tags in xml."""
    num_calls = 0
    with open(xml) as inf:
        for line in tqdm.tqdm(inf, desc="count <call> tags", leave=False):
            if "<call" in line:
                num_calls += 1
    return num_calls


def enumerate_calls(xml):
    """Return a generator yielding all <call> nodes in xml."""
    it = ET.iterparse(xml, events=("end",))
    for _, node in it:
        if node.tag == "call":
            yield node
            node.clear()


def parse_xml(xml, nproc, single_thread, desc):
    """Parse xml and return a generator of the representations of each <call> tag."""
    num_calls = count_calls(xml)
    calls = enumerate_calls(xml)

    invalid_methods = set()
    with Manager() as man:
        with Pool(nproc) as pool:
            if single_thread:
                it = map(
                    functools.partial(
                        process_one,
                        xml=xml,
                    ),
                    calls,
                )
            else:
                it = pool.imap(
                    functools.partial(
                        process_one,
                        xml=xml,
                    ),
                    calls,
                )
            with tqdm.tqdm(
                it,
                desc=desc,
                total=num_calls,
            ) as pbar:
                for result in pbar:
                    if result["result"] == "invalid_call":
                        invalid_methods.add(
                            (result["class_name"], result["method_name"])
                        )
                    yield result
        if len(invalid_methods) > 0:
            print(
                xml,
                "Invalid calls:",
                json.dumps(sorted(invalid_methods), indent=2),
                sep="\n",
            )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Description of your program")
    parser.add_argument("input_dir")
    parser.add_argument("output_file")
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--nproc", type=int, default=10)
    parser.add_argument("--single_thread", action="store_true")
    args = parser.parse_args()

    all_xmls = list(Path(args.input_dir).glob("*.xml"))
    if args.sample:
        # all_xmls = all_xmls[:2]
        all_xmls = all_xmls[2:4]
        # all_xmls = [
        #     Path("postprocessed_xmls/trace-apache-commons-bcel-BcelFuzzer.xml.repair.xml")
        # ]
    all_xmls = sorted(all_xmls, key=lambda p: p.name)
    print(len(all_xmls), "XMLs")

    all_results = defaultdict(int)

    with open(args.output_file, "w") as outf:
        for i, xml in enumerate(all_xmls):
            try:
                it = parse_xml(
                    xml,
                    args.nproc,
                    args.single_thread,
                    f"XML ({i+1}/{len(all_xmls)}) {xml}",
                )
                for result in it:
                    if result["result"] == "success":
                        outf.write(json.dumps(result["data"]) + "\n")
                    all_results[result["result"]] += 1
            except Exception:
                all_results["failed_xml"] += 1
                print("ERROR in file:", str(xml))
                print(traceback.format_exc())
    print("RESULTS:")
    print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
