"""
Display examples in human readable format.
"""
import jsonlines

with jsonlines.open("head100.jsonl") as reader:
    reader = list(reader)[:1]
    for example in reader:
        lines_covered = list(sorted(set(e["relative_lineno"] for e in example["lines_covered"])))
        print("COVERED:", lines_covered)
        print("\n".join(str(i).rjust(3, " ") + " " + l for i, l in enumerate(example["code"].splitlines())))