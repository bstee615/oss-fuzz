#%%
import jsonlines
import tqdm

projects = set()
with jsonlines.open("dump_logs/postprocessed/examples_dedup_sort_trim.jsonl") as reader:
    for example in tqdm.tqdm(reader):
        example["project"]
        projects.add(example["project"])
print(len(projects), list(sorted(projects))[:5])
