"""
Display examples in human readable format.
"""
import jsonlines

with jsonlines.open("head1.json") as reader:
    # reader = list(reader)[:1]
    for i, example in enumerate(reader):
        lines_covered = list(e["relative_lineno"] for e in example["lines_covered"])
        print("EXAMPLE:", i, example["project"], example["class"], example["method"])
        print("\n".join(["\t" + v["name"] + "=" + str(v["text"]) for v in example["entry_variables"] if v["tag"] == "variable"]))
        print("COVERED:", lines_covered)
        print("\n".join(str(i).rjust(3, " ") + " " + l + (" // TRACED" if i in lines_covered else "") for i, l in enumerate(example["code"].splitlines(), start=1)))