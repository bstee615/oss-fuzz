#%%
import jsonlines
import re
import tqdm
from collections import OrderedDict

with open("examples_deduplicated.jsonl") as inf:
    num_lines = sum(1 for _ in inf)

with jsonlines.open("examples_deduplicated.jsonl") as inf, jsonlines.open("examples_sorted.jsonl", "w") as outf:
    def write_examples(examples):
        """sort and output all project examples"""
        for out_example in sorted(examples, key=lambda data: (data["class"], data["method"], data["start_point"][0])):
            outf.write(out_example)

    project_examples = []
    current_project = None
    for example in tqdm.tqdm(inf, total=num_lines):
        # /home/benjis/code/bug-benchmarks/oss-fuzz/repos/angus-mail/core/src/main/java/com/sun/mail/util/ASCIIUtility.java
        example["project"] = project = re.search(r"oss-fuzz/repos/([^/]+)/", example["file_path"]).group(1)
        # [
        #     "class",
        #     "method",
        #     "file_path",
        #     "start_point",
        #     "end_point",
        #     "code",
        #     "entry_variables",
        #     "attributes",
        #     "is_forward",
        #     "project"
        # ]
        key_order = [
            "project",
            "class",
            "method",
            "is_forward",
            "start_point",
            "end_point",
            "code",
            "entry_variables",
            "file_path",
            "attributes",
        ]
        example = {k: example[k] for k in key_order}
        if current_project is None:
            current_project = project
        if current_project != project:
            write_examples(project_examples)
            project_examples = []
        project_examples.append(example)
    if len(project_examples) > 0:
        write_examples(project_examples)
