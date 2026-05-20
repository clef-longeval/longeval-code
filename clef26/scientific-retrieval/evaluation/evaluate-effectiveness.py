import os
from pathlib import Path

import click
import pandas as pd
import pyterrier as pt
import yaml
from ir_datasets_longeval import load
from ir_measures import *

RUN_PATH_FLAT = Path("data/task-1-submissions/outputs-flat")


def read_metadata(metadata_path):
    """Read the ir_metadata file"""
    with open(metadata_path, "r") as f:
        metadata = yaml.safe_load(f)
    return metadata


def evaluate(run, topics, qrels, run_id):
    res = pt.Experiment(
        [run],
        topics,
        qrels,
        names=[run_id],
        filter_by_qrels=True,
        eval_metrics=["all_trec", nDCG(judged_only=True) @ 10],
        perquery=True,
    )
    return res


def do_evaluate(run_directory, qrels_set, run_id, output):
    metadata = read_metadata(run_directory / "ir-metadata.yml")
    team = metadata["actor"]["team"]
    tag = metadata["tag"]

    print("\nTeam: ", team)
    print("Tag: ", tag)

    for snapshot in ["snapshot-1", "snapshot-2", "snapshot-3"]:
        # make output path
        output_path = Path(output) / qrels_set / run_id / snapshot
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        run_files = run_directory / snapshot / "run.txt.gz"

        run = pt.io.read_results(run_files)

        ir_dataset = load(f"longeval-sci-2026/{snapshot}/{qrels_set}")

        topics = pd.DataFrame(
            [
                {"qid": i.query_id, "query": i.default_text()}
                for i in ir_dataset.queries_iter()
            ]
        )

        qrels = pd.DataFrame(ir_dataset.qrels)
        qrels["qid"] = qrels["query_id"]

        results = evaluate(run, topics, qrels, run_id)
        results.to_csv(
            output_path / "results_perquery.csv.gz", index=False, compression="gzip"
        )


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
def main(qrels_set, runs, output):
    for run_dir in Path(runs).glob("*"):
        run_id = run_dir.stem
        do_evaluate(run_dir, qrels_set, run_id, output)


if __name__ == "__main__":
    main()
    # main(
    #     args=[
    #         "--qrels-set", "raw",
    #         "--output", "data/effectiveness",
    #     ],
    #     standalone_mode=False
    # )
