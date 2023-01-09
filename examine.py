#%%
import jsonlines
import sys

with jsonlines.open(sys.argv[1]) as datas:
    for d in datas:
        print("***CODE***")
        print("\n".join(str(i).rjust(3, " ") + " " + l for i, l in enumerate(d["code"].splitlines(), start=1)))
        print("***TRACE***")
        for lc in d["lines_covered"]:
            print(lc["relative_lineno"], lc["type"], len(lc["variables"]), "items")
            for v in lc["variables"]:
                def truncate(s, length):
                    if s is None:
                        return s
                    if len(s) <= length-3:
                        return s
                    else:
                        return s[:length-3] + "..."
                print("\t", v["name"], "[", v["type"], "]", v["source"], truncate(v["text"], 40))
