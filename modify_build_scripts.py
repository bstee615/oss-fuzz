#%%
from pathlib import Path
import re
import difflib

base_dir = Path("projects")
base_dst_dir = Path("projects_instrumented")

def transform_project(project):
    project_dir = base_dir / project
    dst_dir = base_dst_dir / project_dir.relative_to(base_dir)
    
    # Dockerfile
    # "FROM gcr.io/oss-fuzz-base/base-builder-jvm" -> "FROM gcr.io/oss-fuzz-base/base-builder-jvm:recorder-1.0.0"
    with open(project_dir / "Dockerfile", "r") as f:
        text = f.read()
    new_text = text.replace("FROM gcr.io/oss-fuzz-base/base-builder-jvm", "FROM gcr.io/oss-fuzz-base/base-builder-jvm:recorder-1.0.0")
    print("*** Dockerfile ***")
    print("\n".join(difflib.unified_diff(text.splitlines(), new_text.splitlines())))
    dst_file = dst_dir / "Dockerfile"
    dst_file.write_text(new_text)
    print(f"*** WRITE TO {dst_file}***")

    # build.sh
    with open(project_dir / "build.sh", "r") as f:
        text = f.read()
    # "javac" to "javac -g"
    # When "--cp=" occurs, prepend "$RECORDER_API_PATH:"
    new_text = re.sub(r"(^|\s)--cp=", r"\1--cp=$RECORDER_API_PATH:", re.sub(r"(^|\s)javac(\s)", r"\1javac -g\2", text))
    print("*** build.sh ***")
    print("\n".join(difflib.unified_diff(text.splitlines(), new_text.splitlines())))
    dst_file = dst_dir / "build.sh"
    dst_file.write_text(new_text)
    print(f"*** WRITE TO {dst_file}***")

transform_project("angus-mail")
#%%
projects_file="data/1_preprocess/java-projects-from-csv.txt"
with open(projects_file) as f:
    for line in f:
        transform_project(line.strip())