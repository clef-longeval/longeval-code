#!/usr/bin/env python3
import click
from tira.rest_api_client import Client
from pathlib import Path
from tira.check_format import lines_if_valid
from collections import defaultdict
import os
import pandas as pd
from tqdm import tqdm
from git import Repo
import tempfile

def repo_is_public(repo_url):
    if not repo_url or 'bitbucket' in repo_url:
        return False

    with tempfile.TemporaryDirectory() as t:
        for s in ["", ".git"]:
            try:
                Repo.clone_from(repo_url + s, t)
                return True
            except:
                pass
    return False

def analyse_ir_metadata(run_dir):
    libs = set()
    has_repo = False
    repo = None

    lexical = None
    deep_neural_model = None
    sparse_neural_model = None
    dense_neural_model = None
    single_stage_retrieval = None
    runtime = []

    for i in lines_if_valid(run_dir, "ir_metadata"):
        i = i["content"]

        if "platform" in i and "software" in i["platform"] and "libraries" in i["platform"]["software"]:
            for s in i["platform"]["software"]["libraries"]:
                libs.add(s.split(":")[0].split("=")[0].split(" ")[0].split(">")[0])
        if "resources" in i and "runtime" in i["resources"]:
            runtime += [i["resources"]["runtime"]["wallclock"]]

        if "implementation" in i:
            if "source" in i["implementation"] and "repository" in i["implementation"]["source"]:
                repo =  i["implementation"]["source"]["repository"]

        if "method" in i and "retrieval" in i["method"]:
            if not isinstance(i["method"]["retrieval"], list):
                continue
            lexical = i["method"]["retrieval"][0]["lexical"]
            deep_neural_model = i["method"]["retrieval"][0]["deep_neural_model"]
            sparse_neural_model = i["method"]["retrieval"][0]["sparse_neural_model"]
            dense_neural_model = i["method"]["retrieval"][0]["dense_neural_model"]
            single_stage_retrieval = i["method"]["retrieval"][0]["single_stage_retrieval"]

    return {"libs": libs, "runtime": runtime, "repo": repo, "lexical": lexical, "deep_neural_model": deep_neural_model, "sparse_neural_model": sparse_neural_model, "dense_neural_model": dense_neural_model, "single_stage_retrieval": single_stage_retrieval}

def submissions(tira, task, dataset):
    run_ids_to_evaluate = set((Path("evaluation-results-in-progress") / f"longeval-2025-{dataset}-results-run-ids.csv").read_text().split("\n"))
    for _, submission in tira.submissions(task, dataset).iterrows():
        if submission["is_evaluation"] or submission["software"] not in run_ids_to_evaluate:
            continue
        yield submission
@click.command()
@click.option("--task", type=click.Choice(["longeval-2025"]), required=True, help="The task id in tira. See https://archive.tira.io/datasets?query=longeval-20")
@click.option("--datasets", type=click.Choice(["web-20250430-test", "sci-20250430-test"]), multiple=True, help="The dataset id in tira. See https://archive.tira.io/datasets?query=longeval-20")
def main(task, datasets):
    tira = Client()
    results = []
    repo_to_public = {}
    for dataset in datasets:
        for submission in tqdm(list(submissions(tira, task, dataset)), dataset):
            run_directory = tira.download_zip_to_cache_directory(task=task, dataset=dataset, team=submission["team"], run_id=submission["run_id"])
            tmp = {"team": submission["vm"], "submission": submission["software"]}
            tmp.update(analyse_ir_metadata(run_directory))
            if tmp["repo"] and tmp["repo"] not in repo_to_public:
                repo_to_public[tmp["repo"]] = repo_is_public(tmp["repo"])

            tmp["repo_is_public"] = repo_to_public.get(tmp["repo"], False)
            results.append(tmp)
    pd.DataFrame(results).to_json("ir-metadata-overview.jsonl.gz", lines=True, orient="records")

if __name__ == '__main__':
    main()
