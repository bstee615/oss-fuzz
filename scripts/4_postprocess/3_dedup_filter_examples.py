#%%
import json
import jsonlines
import itertools
import tqdm

from class_parser import get_method_node

def ambiguate(var):
    if isinstance(var, str) or var["tag"] == "event-thread-mismatch":
        # unhandled node type, probably event thread mismatch
        # print("STRING", var)
        return None
    try:
        text = var["text"]
    except KeyError:
        print("unhandled", var)
        return None
    if var["serializer"] == "TOSTRING":
        if "@" in text:
            if text.startswith('\"') and text.endswith('\"'):
                text = text[1:-1]
            text = text[:text.find("@")]
    return {
        "name": var["name"],
        "type": var["type"],
        "source": var["source"],
        "serializer": var["serializer"],
        "text": text,
    }

def make_hash(example):
    variables = []
    for v in example["entry_variables"]:
        if v is None:
            # unhandled node
            return None
        av = ambiguate(v)
        if av is None:
            return None
        variables.append(av)
    return json.dumps({
        "class": example["class"],
        "method": example["method"],
        "start_point": example["start_point"],
        "end_point": example["end_point"],
        "variables": variables
    })

seen_examples = set()

def filter_example(example):
    if example["is_forward"]:
        return "forward"
    h = make_hash(example)
    if h is None:
        return "failed"
    else:
        if h not in seen_examples:
            seen_examples.add(h)
            return "new"
        else:
            return "duplicated"

how_many_seen = {
    "new": 0,
    "duplicated": 0,
    "forward": 0,
    "failed": 0,
}

limit = False
# limit = True

if limit:
    num_lines = None
else:
    num_lines = 0
    with open("examples_cut0.jsonl") as inf:
        num_lines += sum(1 for _ in inf)
    with open("examples_cut1.jsonl") as inf:
        num_lines += sum(1 for _ in inf)
with jsonlines.open("examples_cut0.jsonl") as inf0, jsonlines.open("examples_cut1.jsonl") as inf1, jsonlines.open("examples_deduplicated.jsonl", "w") as outf:
    it = itertools.chain(inf0, inf1)
    # it = inf
    if limit:
        it = itertools.islice(it, 5)
    with tqdm.tqdm(it, total=num_lines) as pbar:
        for example in pbar:
            try:
                outcome = filter_example(example)
                how_many_seen[outcome] += 1
                pbar.set_postfix(how_many_seen)
                if outcome == "new":
                    outf.write(example)
            except Exception:
                print("ERROR", json.dumps(example, indent=2))
                raise
        
