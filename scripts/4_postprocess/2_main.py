import functools
import json
import traceback
# import xml.etree.ElementTree as ET
import lxml.etree as ET
from collections import OrderedDict
from multiprocessing import Manager, Pool
from pathlib import Path

import tqdm
from exampleizer import *

import logging
root = logging.getLogger()
root.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
root.addHandler(handler)

handler = logging.FileHandler("debug.log")
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
root.addHandler(handler)


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


def parse_xml(xml, nproc, single_thread):
    """Parse xml and return a generator of the representations of each <call> tag."""
    calls = enumerate_calls(xml)

    invalid_methods = set()
    if single_thread:
        nproc = 1
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
        for result in it:
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
        all_xmls = all_xmls[:5]
        # all_xmls = [
        #     Path("postprocessed_xmls/trace-apache-commons-bcel-BcelFuzzer.xml.repair.xml")
        # ]
    all_xmls = sorted(all_xmls, key=lambda p: p.name)
    log.info("Processing %d XMLs", len(all_xmls))

    all_results = OrderedDict()

    with open(args.output_file, "w") as outf:
        for i, xml in enumerate(all_xmls):
            log.debug(f"PROCESS XML %s", str(xml))
            xml_results = OrderedDict()
            try:
                it = parse_xml(
                    xml,
                    args.nproc,
                    args.single_thread,
                )
                desc = f"XML ({i+1}/{len(all_xmls)}) {xml}"
                with tqdm.tqdm(
                    it,
                    desc=desc,
                    total=count_calls(xml),
                ) as pbar:
                    for result in pbar:
                        if result["result"] == "success":
                            outf.write(json.dumps(result["data"]) + "\n")
                        result_code = result["result"]
                        if result_code not in xml_results:
                            xml_results[result_code] = 0
                        xml_results[result_code] += 1
                        pbar.set_postfix(xml_results)
            except Exception:
                if "failed_xml" not in xml_results:
                    xml_results["failed_xml"] = 0
                xml_results["failed_xml"] += 1
                print("ERROR in file:", str(xml))
                print(traceback.format_exc())
            all_results.update(xml_results)
    print("RESULTS:")
    print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
