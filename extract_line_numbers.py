#%%
import jsonlines
with jsonlines.open("rand30.jsonl") as reader:
    for example in reader:
        # get labels for which lines were covered in the method under test
        relative_lines_covered = [s["relative_lineno"] for s in example["steps"] if "relative_lineno" in s]
        lines_covered = [s["lineno"] for s in example["steps"] if "relative_lineno" in s]

        # print examples annotated with line numbers and covered labels
        lines = example["code"].splitlines()
        for i, line in enumerate(lines, 1):
            print(str(i).rjust(len(str(len(lines))), " ") + ". ", end="")
            print(line, end="")
            for j, rel_line in enumerate(relative_lines_covered):
                if i == rel_line:
                    abs_line = lines_covered[j]
                    print(" (COVERED)", "relative line:", rel_line, "absolute line:", abs_line, end="")
            print()
