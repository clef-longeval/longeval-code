#!/usr/bin/env python3
import click
from tira.rest_api_client import Client
from pathlib import Path
from collections import defaultdict
import os
from ir_measures import *
import pandas as pd
import pyterrier as pt
from ir_datasets_longeval import load


def submission_should_be_skipped(submission):
    """We can skip runs that are evaluation runs, as we do the real evaluation with qrels outside of tira.
    Furthermore, we skip submissions that we only did for testing (included in SUBMISSIONS_TO_SKIP)

    Args:
        submission (dict): the metadata of a submission
    """
    SUBMISSIONS_TO_SKIP = set([
        "TEST-MAIK", "test-system-maik-1234567", "test-system-maik-1234"
    ])

    return submission["is_evaluation"] or submission["software"] in SUBMISSIONS_TO_SKIP

def print_submissions_to_review(task, to_review):
    if not to_review:
        return

    for team in to_review:
        print(f"\n\nRemaining reviews for {team}:")
        print(f"\tGo to: https://www.tira.io/submit/{task}/user/{team}/upload-submission")
        print(f"\tTo Review:")
        for i in to_review[team]:
            print(f"\t\t- {i}")

def evaluate(run, topics, qrels, run_id):
    res = pt.Experiment(
        [run],
        topics,
        qrels,
        names=[run_id],
        eval_metrics=["all_trec", nDCG(judged_only=True)@10],
        perquery=True,
    )
    return res



def do_evaluation(task, dataset, run_directory, run_id, output):
    team = run_directory.split("/")[-3]
    print("\nTeam: ", team)
    print("Tag: ", run_id)

    timestamp = run_directory.split("/")[-2]
    
    for snapshot in sorted(os.listdir(run_directory)):
        if snapshot in ["ir-metadata.yml", ".DS_Store"]:
            continue

        # make output path 
        output_path = Path(output) / dataset / team / run_id / timestamp/ snapshot
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        if os.path.exists(output_path / "results_perquery.csv.gz"):
            continue

        run = pt.io.read_results(run_directory + f"/{snapshot}/run.txt.gz")
        
        dataset_screen_name = dataset.split("-")[0]
        ir_dataset = load(f"longeval-{dataset_screen_name}/{snapshot}")
        topics = pd.DataFrame(
            [
                {"qid": i.query_id, "query": i.default_text()}
                for i in ir_dataset.queries_iter()
            ]
        )
        qrels_path = f'/workspaces/longeval-code/clef25/evaluation-in-progress/evaluation-results-in-progress/qrels/longeval-{dataset_screen_name}/{snapshot}/qrels_processed.txt'
        qrels = pt.io.read_qrels(qrels_path)

        # Apply fix for docno if needed
        if dataset_screen_name == "web" and run["docno"].str.startswith("doc").any():
            qrels["docno"] = "doc" + qrels["docno"].astype(str)
        
        results = evaluate(run, topics, qrels, run_id)
        results.to_csv(output_path / "results_perquery.csv.gz", index=False, compression="gzip")
        
    


@click.command()
@click.option("--task", type=click.Choice(["longeval-2025"]), required=True, help="The task id in tira. See https://archive.tira.io/datasets?query=longeval-20")
@click.option("--datasets", type=click.Choice(["web-20250430-test", "sci-20250430-test"]), multiple=True, help="The dataset id in tira. See https://archive.tira.io/datasets?query=longeval-20")
@click.option("--output", type=str, required=True, help="The output directory.")
def main(task, datasets, output):
    tira = Client()
    to_review = defaultdict(lambda: set())

    for dataset in datasets:
        for _, submission in tira.submissions(task, dataset).iterrows():
            if submission_should_be_skipped(submission):
                continue

            if submission["review_blinded"]:
                to_review[submission["team"]].add(submission["software"])
            
            run_directory = tira.download_zip_to_cache_directory(task=task, dataset=dataset, team=submission["team"], run_id=submission["run_id"])
            do_evaluation(task, dataset, run_directory, run_id=submission["software"], output=output)

    print_submissions_to_review(task, to_review)


if __name__ == '__main__':
    main()
