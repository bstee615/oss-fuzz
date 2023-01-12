#%%
import jsonlines
import tqdm
from pathlib import Path
with jsonlines.open("postprocessed_dedup_sort_filter.jsonl") as reader:
    for example in tqdm.tqdm(reader):
        if example["class"].endswith("Fuzzer"):
            continue
        else:
            filename = Path("jar_code")/example["project"]/(example["class"].replace(".", "/") + ".java")
            if not filename.exists():
                print("missing", filename)