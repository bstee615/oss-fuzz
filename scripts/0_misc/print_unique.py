"""
Print lines logged by tqdm cleanly
"""

#%%
unique_line = {}
with open("/tmp/ts-out.olVouW") as f:
    for line in f:
        if line.startswith("XML ("):
            line_id = line[:line.index(")")]
            unique_line[line_id] = line
for k, v in unique_line.items():
    print(v, end="")