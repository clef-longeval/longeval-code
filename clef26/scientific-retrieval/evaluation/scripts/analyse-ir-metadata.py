#!/usr/bin/env python3
import tempfile
from pathlib import Path

import pandas as pd
import yaml
from git import Repo
from tira.check_format import lines_if_valid


def repo_is_public(repo_url):
    if not repo_url or "bitbucket" in repo_url:
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
    team = None
    run_id = run_dir.name

    for i in lines_if_valid(run_dir, "ir_metadata"):
        i = i["content"]

        # libs
        if (
            "platform" in i
            and "software" in i["platform"]
            and "libraries" in i["platform"]["software"]
        ):
            for s in i["platform"]["software"]["libraries"]:
                libs.add(s.split(":")[0].split("=")[0].split(" ")[0].split(">")[0])

        # runtime
        if "resources" in i and "runtime" in i["resources"]:
            runtime += [i["resources"]["runtime"]["wallclock"]]

        # repo
        if "implementation" in i:
            if (
                "source" in i["implementation"]
                and "repository" in i["implementation"]["source"]
            ):
                repo = i["implementation"]["source"]["repository"]

        # method
        if "method" in i and "retrieval" in i["method"]:
            if not isinstance(i["method"]["retrieval"], list):
                continue
            lexical = i["method"]["retrieval"][0]["lexical"]
            deep_neural_model = i["method"]["retrieval"][0]["deep_neural_model"]
            sparse_neural_model = i["method"]["retrieval"][0]["sparse_neural_model"]
            dense_neural_model = i["method"]["retrieval"][0]["dense_neural_model"]
            single_stage_retrieval = i["method"]["retrieval"][0][
                "single_stage_retrieval"
            ]

        # actor
        if "actor" in i and "team" in i["actor"]:
            team = i["actor"]["team"]

    return {
        "libs": libs,
        "runtime": runtime,
        "repo": repo,
        "lexical": lexical,
        "deep_neural_model": deep_neural_model,
        "sparse_neural_model": sparse_neural_model,
        "dense_neural_model": dense_neural_model,
        "single_stage_retrieval": single_stage_retrieval,
        "team": team,
        "run_id": run_id,
    }


def submissions(tira, task, dataset):
    run_ids_to_evaluate = set(
        (
            Path("evaluation-results-in-progress")
            / f"longeval-2025-{dataset}-results-run-ids.csv"
        )
        .read_text()
        .split("\n")
    )
    for _, submission in tira.submissions(task, dataset).iterrows():
        if (
            submission["is_evaluation"]
            or submission["software"] not in run_ids_to_evaluate
        ):
            continue
        yield submission


def read_metadata(metadata_path):
    with open(metadata_path, "r") as f:
        return yaml.safe_load(f)


def main():
    results = []
    RUN_DIR = Path("data") / "task-1-submissions" / "outputs-flat"

    for run in RUN_DIR.iterdir():
        if run.is_dir():
            tmp = {}
            tmp.update(analyse_ir_metadata(run))
            results.append(tmp)

    pd.DataFrame(results).to_json(
        "data/ir-metadata-overview.jsonl", lines=True, orient="records"
    )


if __name__ == "__main__":
    main()
