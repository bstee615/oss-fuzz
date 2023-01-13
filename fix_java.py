"""
NOT USED: fix the line numbers in decompiled java code to match the original line number.
BORKEN
"""
#%%
import re
def fix_file(fpath):
    text = ""
    with open(fpath) as f:
        line_pointer = 1
        for line in f:
            m = re.match(r"/\*\s+([0-9]+)\s+\*/", line)
            real_lineno = int(m.group(1))
            if real_lineno == 0:
                pass
            else:
                while line_pointer < real_lineno:
                    text += "\n"
                    line_pointer += 1
            # text += line[m.end()+1:]
            text += line
            line_pointer += 1
    with open(fpath, "w") as f:
        f.write(text)

#%%
fix_file("jar_code/angus-mail/com/sun/mail/util/BASE64DecoderStream.java")