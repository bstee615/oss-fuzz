"""NOT USED ANYMORE: PREFER INTRUMENTATION OVER TRACING"""

#%%
import xml.etree.ElementTree as ET
import json
import sys

def parse(filename):
    variables = []
    it = ET.iterparse(filename)
    for _, node in it:
        if node.tag == "call" and "fuzzerTestOneInput" in node.attrib["method"]:
            exit_tracepoint = next(child for child in node if child.tag == "tracepoint" and child.attrib["type"] == "exit")
            for v in exit_tracepoint:
                variables.append(v)
            return variables
                    
def write_to_file(data, output_file):
    output_data = [{
        "name": v.attrib["name"],
        "type": v.attrib["type"],
        "valueText": v.text,
    } for v in data]
    with open(output_file, "w") as of:
        json.dump(output_data, of)

# xml_file = "/run/media/benjis/FSCOPY/17537297-282f-49b5-b466-0f3332b732f8/home/benjis/code/bug-benchmarks/trace-modeling/trace_collection_java/log.xml"
xml_file = sys.argv[1]
output_file = sys.argv[2]
data = parse(xml_file)
write_to_file(data, output_file)
