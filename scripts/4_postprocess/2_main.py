import functools
import json
import traceback
# import xml.etree.ElementTree as ET
import lxml.etree as ET
from collections import OrderedDict
from multiprocessing import Manager, Pool
from pathlib import Path

from xml_traverser import enumerate_calls, count_calls

import itertools

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


def parse_xml(xml, nproc, single_thread):
    """Parse xml and return a generator of the representations of each <call> tag."""
    calls = enumerate_calls(xml)

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
            yield result


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
        # NOTE: different times call for different measures
        # all_xmls = all_xmls[:2]
        # all_xmls = all_xmls[:10]
        # all_xmls = [xml for xml in all_xmls if "trace-apache-commons-ImagingBmpFuzzer.xml" in xml.name]
        # all_xmls = [xml for xml in all_xmls if "trace-apache-commons-lang-EscapeHtmlFuzzer.xml" in xml.name]
        # all_xmls = [xml for xml in all_xmls if "janino" in xml.name]
        # all_xmls = [
        #     Path("postprocessed_xmls/trace-apache-commons-bcel-BcelFuzzer.xml.repair.xml")
        # ]
        pass
    all_xmls = sorted(all_xmls, key=lambda p: p.name)
    log.info("Processing %d XMLs", len(all_xmls))

    name, ext = Path(args.output_file).name.rsplit(".", maxsplit=1)
    error_file = Path(args.output_file).parent / (name + "_error." + ext)

    all_results = OrderedDict()

    with open(args.output_file, "w") as outf, open(error_file, "w") as error_outf:
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
                num_calls = count_calls(xml)
                if args.sample:
                    it = itertools.islice(it, 10)
                    num_calls = min(num_calls, 10)
                with tqdm.tqdm(
                    it,
                    desc=desc,
                    total=num_calls,
                ) as pbar:
                    for result in pbar:
                        if result["result"] == "success":
                            outf.write(json.dumps(result["data"]) + "\n")
                        else:
                            error_outf.write(json.dumps(result) + "\n")
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
            for k, v in xml_results.items():
                all_results[k] = (all_results[k] + v) if k in all_results else v
    print("RESULTS:")
    print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
