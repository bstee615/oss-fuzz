#%%
from pathlib import Path
import json
import tqdm
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

def get_data(d):
    project = d.name
    manifests = d.rglob("*.jar.class_manifest.json")
    data = {}
    for m in manifests:
        with open(m) as f:
            file_data = json.load(f)
            for k, v in file_data.items():
                # print(k, len(v))
                if k in data:
                #     print(f"Duplicate key: {k}")
                    pass
                else:
                    data[k] = v
    all_primitives = []
    try:
        for methods in data.values():
            all_primitives.extend(m["all_primitive"] for m in methods)
    except TypeError:
        pass
    percent_all_primitives = None
    if len(all_primitives) > 0:
        percent_all_primitives = round(np.average(all_primitives)*100, 2)
    for class_name, methods in data.items():
        for m in methods:
            yield {
                "project": project,
                "class": class_name,
                "method": m["method"],
                "all_primitive": m["all_primitive"]
                "all_fuzzable": m["all_fuzzable"]
            }

def analyze_project(d):
    data = get_data(d)
    return pd.DataFrame(data)

def test_debug():
    print(analyze_project(Path("build/out/slf4j-api")))

if __name__ == "__main__":
    all_data = []
    for d in tqdm.tqdm(sorted(Path("build/out").glob("*"))):
        all_data.append(analyze_project(d))
    df = pd.concat(all_data)
    print("Total number of classes:", df.groupby("class").ngroups)
    print("Total number of methods:", len(df))
    print("Mean methods per project:", df.groupby("project")["method"].count().mean())
    print("Median methods per project:", df.groupby("project")["method"].count().median())
    print("Overall average percentage all-primitive functions:", str(round(df["all_primitive"].dropna().mean()*100, 2)) + '%')
    print("Overall average percentage all-primitive functions:", str(round(df["all_fuzzable"].dropna().mean()*100, 2)) + '%')
    agg_info = df.groupby("project")["class"].agg(["nunique", "count"]).rename(columns={"nunique": "unique classes", "count": "unique methods"})
    print(agg_info.to_markdown())

    fig, ax = plt.subplots(2, 1)
    classes_threshold = 2500
    methods_threshold = 5000
    sns.histplot(agg_info[agg_info["unique classes"] < classes_threshold]["unique classes"], bins=25, ax=ax[0])
    sns.histplot(agg_info[agg_info["unique methods"] < methods_threshold]["unique methods"], bins=25, ax=ax[1])
    ax[0].set_title(f'{(agg_info["unique classes"] > classes_threshold).sum()} projects have at least {classes_threshold} classes')
    ax[1].set_title(f'{(agg_info["unique methods"] > methods_threshold).sum()} projects have at least {methods_threshold} methods')
    plt.tight_layout()
    plt.show()
