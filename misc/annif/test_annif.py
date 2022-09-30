import subprocess
from pathlib import Path
from datetime import datetime
import json

from pathvalidate import sanitize_filename
import matplotlib.pyplot as plt
import pandas as pd

TRAINING_FILE = "../../training_en_80k.tsv"
VALIDATION_FILE = "../../validation_en_10k.tsv"
PROJECTS_TO_TEST = [
    "tfidf-en",
    "omikuji-parabel-en",
]
METRICS_TO_DISPLAY = ["F1_score_doc_avg", "Precision_doc_avg", "Recall_doc_avg", "NDCG", "NDCG@5", "Precision@1", "Precision@5"]

EVAL_PARAMS = [
    "--limit 2 --threshold 0.2",
    "--limit 2 --threshold 0.4",
    "--limit 5 --threshold 0.2",
    "--limit 5 --threshold 0.4",
]

Path("./results").mkdir(parents=True, exist_ok=True)

results = {}

date_str = datetime.now().strftime("%Y%m%d_%H_%M_%S")
for project in PROJECTS_TO_TEST:
    subprocess.run(["annif", "train", "-j", "0", project, TRAINING_FILE])
    for eval_param in EVAL_PARAMS:
        metrics_filename = f"./results/metrics_{project}_{eval_param.replace(' ', '')}_{date_str}.json"

        eval_cmd = f"annif eval --metrics-file {metrics_filename} -j 0 {eval_param} {project} {VALIDATION_FILE}"
        subprocess.run(eval_cmd.split())

        with open(metrics_filename, "r") as json_file:
            results_dict = json.load(json_file)
            label = f"{project} {eval_param}"
            results[label] = {k: results_dict[k] for k in METRICS_TO_DISPLAY}

pd.DataFrame(results).T.plot(ylim=(0,1), kind="bar", rot=-10, title=f"Train: {TRAINING_FILE}, validate/test: {VALIDATION_FILE}")

results_png_filename = f"./results/metrics_{date_str}.png"

plt.savefig(results_png_filename)
print(f"Saved plot to {results_png_filename}")
plt.show()
