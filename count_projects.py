#%%
import pandas as pd
df = pd.read_csv("oss-fuzz/projects.csv")
df

#%%
for lang, group in df.groupby("Language"):
    st = " OR ".join(f"proj={proj}" for proj in group["Project"])
    print("LANGUAGE", lang)
    print("-status:WontFix,Duplicate,New -component:Infra (", st, ")")

#%%

df = pd.read_csv("oss-fuzz/projects_summary.csv")
print(df.to_markdown())
