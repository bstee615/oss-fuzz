#%%
import xml.etree.ElementTree as ET
import json
import sys

def var_to_string(v):
    return v.attrib['name'] + '=' + repr(v.text)

def get_variables(tracepoint):
    return (v for v in tracepoint if v.tag == 'variable')

class ResultLogger:
    def __init__(self):
        self.results = []

    def log_method_call(self, call, before, after):
        print(f"TRACEPOINT:")
        #  {call=} {before=} {after=}
        print(f"CALL: {call.attrib['method']} {call.attrib['location']}")
        print(f"BEFORE: {before.attrib['location']}")
        print('\t' + ', '.join(map(var_to_string, get_variables(before))))
        print(f"AFTER: {after.attrib['location']}")
        print('\t' + '\n\t'.join(map(var_to_string, get_variables(after))))
        self.results.append({
            "call": call,
            "before": before,
            "after": after,
        })

    def parse(self, filename):
        it = ET.iterparse(filename)
        for _, node in it:
            if node.tag == "call" and "fuzzerTestOneInput" in node.attrib["method"]:
                # extract calls to project methods
                print("Fuzzer method")
                last_tracepoint_before_call = None
                last_call = None
                really_last_call = None
                seen_noop_results = set()
                noop_results = []
                for i, child in enumerate(node):
                    # detect calls to project methods
                    if child.tag == "call" and "Fuzzer" not in child.attrib["method"]:
                        # get before/after tracepoints
                        last_call = really_last_call = child
                        seen_noop_results = set()
                        pass
                    elif child.tag == "tracepoint":
                        if last_call is not None:
                            # log method call
                            current_tracepoint = child
                            self.log_method_call(last_call, last_tracepoint_before_call, current_tracepoint)
                            last_call = None
                        result_variables = [c for c in get_variables(child) if "benjis_result_" in c.attrib["name"]]
                        result_variables_new = [c for c in result_variables if c not in seen_noop_results]
                        if len(result_variables_new) > 0:
                            print("RESULT:\n\t", "\n\t".join(map(var_to_string, result_variables_new)))
                            self.results[-1]["after"] = child
                            seen_noop_results.update(result_variables_new)
                        last_tracepoint_before_call = child

    def log_results_to_file(self, output_file):
        with open(output_file, "w") as of:
            results = []
            print("ALL RESULTS:")
            for r in self.results:
                call = r["call"]
                before = r["before"]
                after = r["after"]
                print(f"CALL: {call.attrib['method']} {call.attrib['location']}")
                print(f"BEFORE: {before.attrib['location']}")
                print('\t' + '\n\t'.join(map(var_to_string, get_variables(before))))
                print(f"AFTER: {after.attrib['location']}")
                print('\t' + '\n\t'.join(map(var_to_string, get_variables(after))))
                
                stacktrace = next(c for c in call if c.tag == "stacktrace")
                for frame in stacktrace:
                    # TODO detect all fuzzer methods
                    if "fuzzerTestOneInput" in frame.attrib["method"]:
                        call_frame = frame

                changed = []
                for a in after:
                    if a.attrib["name"].startswith("benjis_result_"):
                        changed.append({"new": a})
                    else:
                        b = next((v for v in before if v.attrib["name"] == a.attrib["name"]), None)
                        if b is None:
                            changed.append({"new": a})
                        else:
                            if a.text != b.text:
                                changed.append({
                                    "before": b,
                                    "after": a,
                                })
                # print(f"CHANGED:")
                for c in changed:
                    # print(list(map(var_to_string, c)))
                    results.append({
                        "location": call_frame.attrib["location"],
                        "changed": [{k: {"text": v.text, **v.attrib} for k, v in c.items()} for c in changed],
                    })
            json.dump(results, of, indent=2)

rl = ResultLogger()
# xml_file = "/run/media/benjis/FSCOPY/17537297-282f-49b5-b466-0f3332b732f8/home/benjis/code/bug-benchmarks/trace-modeling/trace_collection_java/log.xml"
xml_file = sys.argv[1]
output_file = sys.argv[2]
rl.parse(xml_file)
rl.log_results_to_file(output_file)

# %%
