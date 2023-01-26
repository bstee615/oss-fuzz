from pathlib import Path
import tqdm

import sys

scripts = list((Path("build/out") / sys.argv[1]).rglob("build_fuzzer_commands_*.java.sh"))

for fname in tqdm.tqdm(scripts):
    with open(fname) as f:
        text = ""
        for line in f:
            tokens = line.split()
            replaced_cp = False
            # has_d_option = False
            for i, t in enumerate(tokens):
                if t == "-cp":
                    if ":/usr/local/lib/recorder_deploy.jar" not in tokens[i+1]:
                        tokens[i+1] += ":/usr/local/lib/recorder_deploy.jar"
                    replaced_cp = True
                if t == "-d":
                    # has_d_option = True
                    print("REMOVING -d OPTION:", tokens[i], tokens[i+1])
                    tokens[i] = ""
                    tokens[i+1] = ""
            # if not has_d_option:
            tokens = [tokens[0]] + ["-d", "/out"] + tokens[1:]
            if not replaced_cp:
                print("DID NOT REPLACE -cp", fname)
            text += " ".join(tokens)
    # with open(fname.parent / (fname.name + ".new"), "w") as f:
    with open(fname, "w") as f:
        f.write(text)
