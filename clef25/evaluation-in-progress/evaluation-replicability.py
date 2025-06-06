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
import json
from repro_eval.Evaluator import RpdEvaluator, RplEvaluator
from repro_eval.util import arp, arp_scores, print_base_adv, print_simple_line, trim
import re

def submission_should_be_skipped(submission):
    """We can skip runs that are evaluation runs, as we do the real evaluation with qrels outside of tira.
    Furthermore, we skip submissions that we only did for testing (included in SUBMISSIONS_TO_SKIP)

    Args:
        submission (dict): the metadata of a submission
    """
    SUBMISSIONS_TO_SKIP = set([
        "TEST-MAIK", "test-system-maik-1234567", "test-system-maik-1234", "test-system-maik"
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
        filter_by_qrels=True,
        eval_metrics=["all_trec", nDCG(judged_only=True)@10],
        perquery=True,
    )
    return res

def get_pivot_path(dataset):
    if dataset == "web-20250430-test":
        bm25_path = "/root/.tira/extracted_runs/longeval-2025/web-20250430-test/clef25-cir-cluster/2025-05-21-16-49-36/output/{}/run.txt.gz"
    elif dataset == "sci-20250430-test":
        bm25_path = "/root/.tira/extracted_runs/longeval-2025/sci-20250430-test/clef25-tf-idk/2025-05-16-21-01-07/output/{}/run.txt"
    else:
        raise ValueError(f"Unknown dataset: {dataset}")
    
    return bm25_path
    

def prepare_runs(task, dataset, run_directory, run_id, output, reference):
    team = run_directory.split("/")[-3]
    version = run_directory.split("/")[-2]
    print("\nTeam: ", team)
    print("Tag: ", run_id)
    print("Run directory: ", run_directory)  
    
    trimmed_path = Path(output) / dataset / team / run_id / version
    snapshots = sorted(os.listdir(run_directory))
    for snapshot in snapshots:
        if not bool(re.match(r'^\d{4}-(0[1-9]|1[0-2])$', snapshot)):
            print(f">>> Snapshot {snapshot} not in evaluation scope. Skipping...")
            continue
                
        # make output path 
        if not os.path.exists(trimmed_path / snapshot):
            os.makedirs(trimmed_path / snapshot)
        
        if os.path.exists(trimmed_path / snapshot / "run.csv.gz"):
            continue
        
        run_files = os.listdir(run_directory + f"/{snapshot}")
        # get the ending of the run file to load it correctly
        if "run.txt" in run_files:
            run = pt.io.read_results(run_directory + f"/{snapshot}/run.txt")
        elif "run.txt.gz" in run_files:
            run = pt.io.read_results(run_directory + f"/{snapshot}/run.txt.gz")
        else:
            print(f">>> Run file not found for {run_id} in {snapshot}. Skipping...")
            continue
        
        pivot_path = get_pivot_path(dataset)
        baseline_run = pt.io.read_results(pivot_path.format(snapshot))   
        base_topics = set(baseline_run["qid"].unique())
        
        # print num removed topics
        print(f"Removed {len(set(run['qid'].unique()) - base_topics)} topics from {snapshot} relevance feedback run.")
        
        # Remove topics not in base run
        run = run[run["qid"].isin(base_topics)]
        
        # Strip doc prefix from docno if needed

        # write runs to output
        pt.io.write_results(run, trimmed_path / snapshot / "run.csv")

def ap(arp_orig, arp_rep):
    """Calculate the average precision for the two snapshots."""            
    res = {}
    for measure, score in arp_orig.items():
        mean = (score + arp_rep[measure]) / 2        
        res[measure] = mean
    return res

def rc(arp_orig, arp_rep):
    """Calculate the relative change for the two snapshots."""
    res = {}
    for measure, score in arp_orig.items():
        if arp_rep[measure] == 0:
            res[measure] = 0
        else:
            res[measure] = (score - arp_rep[measure]) / score
    return res
        
def do_evaluation(task, dataset, run_directory, run_id, output, reference):
    team = run_directory.split("/")[-3]
    version = run_directory.split("/")[-2]
    dataset_screen_name = dataset.split("-")[0]
    
    table = []
    snapshots = sorted(os.listdir(run_directory))
    trimmed_path = Path(output) / dataset / team / run_id / version
    for snapshot in snapshots:
        if not bool(re.match(r'^\d{4}-(0[1-9]|1[0-2])$', snapshot)):
            continue 
        if snapshot == reference:
            continue
        
        pivot_path = get_pivot_path(dataset)
        
        base_dir = f"/workspaces/longeval-code/clef25/evaluation-in-progress/evaluation-results-in-progress/"
        # old
        QREL = os.path.join(base_dir, f"/workspaces/longeval-code/clef25/evaluation-in-progress/evaluation-results-in-progress/qrels/longeval-{dataset_screen_name}/{reference}/qrels_processed.txt")
        ORIG_A = trimmed_path / reference / "run.csv"
        ORIG_B = pivot_path.format(reference)

        # new
        QREL_RPL = os.path.join(base_dir, f"/workspaces/longeval-code/clef25/evaluation-in-progress/evaluation-results-in-progress/qrels/longeval-{dataset_screen_name}/{snapshot}/qrels_processed.txt")
        RPL_A = trimmed_path / snapshot / "run.csv"
        RPL_B = pivot_path.format(snapshot)
        
        rpl_eval = RplEvaluator(qrel_orig_path=QREL,
                            run_b_orig_path=ORIG_B,
                            run_a_orig_path=ORIG_A,
                            run_b_rep_path=RPL_B,
                            run_a_rep_path=RPL_A,
                            qrel_rpl_path=QREL_RPL)
        rpl_eval.trim()
        rpl_eval.evaluate()
        
        try:
            arp_orig = arp_scores(rpl_eval.run_a_orig_score)
        except:
            print(f">>> Original run scores not available for {run_id} in {snapshot}. Skipping...")
            continue
            
        arp_rep = arp_scores(rpl_eval.run_a_rep_score)
                
        table.append({
            "snapshot": snapshot,
            "team": team,
            "run_id": run_id,
            "version": version,
            "arp": arp_scores(rpl_eval.run_a_rep_score),
            "er": rpl_eval.er(),
            "dri": rpl_eval.dri(),
            "ttest": rpl_eval.ttest(),
            "ap": ap(arp_orig, arp_rep),
            "rc": rc(arp_orig, arp_rep)
        })
    
    
    # write table as json to output
    output_path = trimmed_path / "results.json"
    with open(output_path, "w") as f:
        json.dump(table, f, indent=4)    


@click.command()
@click.option("--task", type=click.Choice(["longeval-2025"]), required=True, help="The task id in tira. See https://archive.tira.io/datasets?query=longeval-20")
@click.option("--datasets", type=click.Choice(["web-20250430-test", "sci-20250430-test"]), multiple=True, help="The dataset id in tira. See https://archive.tira.io/datasets?query=longeval-20")
@click.option("--output", type=str, required=True, help="The output directory.")
@click.option("--reference", type=str, required=True, help="The output directory.")
def main(task, datasets, output, reference):
    tira = Client()
    to_review = defaultdict(lambda: set())

    for dataset in datasets:
        for _, submission in tira.submissions(task, dataset).iterrows():
            if submission_should_be_skipped(submission):
                continue
            run_directory = tira.download_zip_to_cache_directory(task=task, dataset=dataset, team=submission["team"], run_id=submission["run_id"])
            prepare_runs(task, dataset, run_directory, run_id=submission["software"], output=output, reference=reference)
        
        for _, submission in tira.submissions(task, dataset).iterrows():
            if submission_should_be_skipped(submission):
                continue
            run_directory = tira.download_zip_to_cache_directory(task=task, dataset=dataset, team=submission["team"], run_id=submission["run_id"])
            do_evaluation(task, dataset, run_directory, run_id=submission["software"], output=output, reference=reference)


if __name__ == '__main__':
    # import sys
    # sys.argv = [
    #     "script_name",  # doesn't matter, just a placeholder
    #     "--task", "longeval-2025", 
    #     "--datasets", "sci-20250430-test", 
    #     "--output", "/workspaces/longeval-code/clef25/evaluation-in-progress/evaluation-results-in-progress/replicability", 
    #     "--reference", "2024-11"
    # ]
    main()
