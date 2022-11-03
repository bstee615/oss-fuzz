import sys
append_list = None
old = []
new = []
for arg in sys.argv[1:]:
    if arg == "OLD":
        append_list = old
    elif arg == "NEW":
        append_list = new
    else:
        append_list.append(arg)
print(" ".join(x for x in new if x not in old))
