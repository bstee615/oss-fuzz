import re
import sys
filepath = sys.argv[1]
with open(filepath) as f:
    text = f.read()
text = re.sub(r'--target_class(=|\s+)[a-zA-Z0-9_]+Fuzzer', r'', text)
with open(filepath, "w") as f:
    f.write(text)