#%%
# for each tracepoint,
# if tracepoint is entry: include all variables and update values in variable map.
# if tracepoint is step or exit: for each variable, if different from last value in variable map, include it and update values.
def filter_variables(example):
    variable_map = {}
    for step in example["lines_covered"]:
        changed_variables = []
        if step["type"] == "entry":
            for v in step["variables"]:
                changed_variables.append(v)
                variable_map[v["name"]] = v["text"]
        else:
            for v in step["variables"]:
                if v["name"] not in variable_map or v["text"] != variable_map[v["name"]]:
                    changed_variables.append(v)
                    variable_map[v["name"]] = v["text"]
        step["variables"] = changed_variables
        # step["changed_variables"] = changed_variables


#%%
# for each tracepoint, for each variable,
# if variable type is static, exclude it.
# if the tracepoint is empty, delete it.
def remove_static_variables(example):
    new_steps = []
    for step in example["lines_covered"]:
        def filter_out_static(l):
            new_l = []
            for v in step["variables"]:
                if not v["source"].startswith("<static>"):
                    new_l.append(v)
            return new_l
        step["variables"] = filter_out_static(step["variables"])
        # step["changed_variables"] = filter_out_static(step["changed_variables"])
        if len(step["variables"]) > 0:
            new_steps.append(step)
    example["steps"] = new_steps


#%%
import jsonlines
import tqdm

input_file = "postprocessed_dedup_sort_head.jsonl"
output_file = "postprocessed_dedup_sort_head_filter.jsonl"
output_file_nostatic = "postprocessed_dedup_sort_head_filter_removestatic.jsonl"
with jsonlines.open(input_file) as inf, jsonlines.open(output_file, "w") as outf, jsonlines.open(output_file_nostatic, "w") as outf2:
    for example in tqdm.tqdm(inf):
        filter_variables(example)
        outf.write(example)
        remove_static_variables(example)
        outf2.write(example)