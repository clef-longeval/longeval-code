#!/usr/bin/env python3
import json
import os
from pathlib import Path

import click
import pandas as pd
import yaml
from ir_datasets_longeval import load
from ir_measures import *
from repro_eval.Evaluator import RplEvaluator
from repro_eval.util import arp_scores

RUN_PATH_FLAT = Path("data/task-1-submissions/outputs-flat")


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


def read_metadata(metadata_path):
    """Read the ir_metadata file"""
    with open(metadata_path, "r") as f:
        metadata = yaml.safe_load(f)
    return metadata


def do_evaluate(
    run_directory, qrels_set, run_id, output, pivot_directory, reference="snapshot-1"
):
    metadata = read_metadata(run_directory / "ir-metadata.yml")
    team = metadata["actor"]["team"]
    tag = metadata["tag"]

    print("\nTeam: ", team)
    print("Tag: ", tag)

    table = []

    ir_dataset_reference = load(f"longeval-sci-2026/{reference}/{qrels_set}")

    qrels_reference = pd.DataFrame(ir_dataset_reference.qrels)

    for snapshot in ["snapshot-1", "snapshot-2", "snapshot-3"]:
        # make output path
        output_path = Path(output) / qrels_set / run_id / snapshot
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        if snapshot == reference:
            # skip reference snapshot
            continue

        ir_dataset = load(f"longeval-sci-2026/{snapshot}/{qrels_set}")
        qrels = pd.DataFrame(ir_dataset.qrels)

        qrels["qid"] = qrels["query_id"]

        # old
        ORIG_A = run_directory / reference / "run.txt.gz"
        ORIG_B = pivot_directory / reference / "run.txt.gz"

        # new
        RPL_A = run_directory / snapshot / "run.txt.gz"
        RPL_B = pivot_directory / snapshot / "run.txt.gz"

        try:
            rpl_eval = RplEvaluator(
                qrels_orig_path=ir_dataset_reference.qrels_path(),
                run_b_orig_path=str(ORIG_B),
                run_a_orig_path=str(ORIG_A),
                run_b_rep_path=str(RPL_B),
                run_a_rep_path=str(RPL_A),
                qrels_rpl_path=ir_dataset.qrels_path(),
            )
            rpl_eval.trim()
            rpl_eval.evaluate()

            try:
                arp_orig = arp_scores(rpl_eval.run_a_orig_score)
            except:
                print(
                    f">>> Original run scores not available for {run_id} in {snapshot}. Skipping..."
                )
                continue

            arp_rep = arp_scores(rpl_eval.run_a_rep_score)

            table.append(
                {
                    "snapshot": snapshot,
                    "team": team,
                    "run_id": run_id,
                    "arp": arp_scores(rpl_eval.run_a_rep_score),
                    "er": rpl_eval.er(),
                    "dri": rpl_eval.dri(),
                    "ttest": rpl_eval.ttest(),
                    "ap": ap(arp_orig, arp_rep),
                    "rc": rc(arp_orig, arp_rep),
                }
            )
        except Exception as e:
            print(f"Error evaluating {team} - {run_id} - {snapshot}: {e}")

    # write table as json to output
    with open(output / "table.json", "w") as f:
        json.dump(table, f, indent=4)


@click.command()
@click.option(
    "--qrels-set",
    type=click.Choice(["dctr", "raw"]),
    required=True,
    help="name of the qrels set to be used for the evaluation.",
)
@click.option(
    "--runs",
    type=str,
    default=str(RUN_PATH_FLAT),
    help="Path to the flattend run files",
)
@click.option("--output", type=str, required=True, help="The output directory.")
@click.option("--pivot-dir", type=str, required=True, help="Path to the pivot system.")
def main(qrels_set, runs, output, pivot_dir):
    for run_dir in Path(runs).glob("*"):
        run_id = run_dir.stem
        do_evaluate(run_dir, qrels_set, run_id, Path(output), Path(pivot_dir))


if __name__ == "__main__":
    # main()
    main(
        args=[
            "--qrels-set",
            "raw",
            "--output",
            "data/robustness",
            "--pivot-dir",
            "data/task-1-submissions/outputs-flat/put-to-front",
        ],
        standalone_mode=False,
    )
