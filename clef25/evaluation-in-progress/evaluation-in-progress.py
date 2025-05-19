#!/usr/bin/env python3
import click
from tira.rest_api_client import Client
from pathlib import Path
from collections import defaultdict


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

def do_evaluation(task, dataset, run_directory):
    print(f"do some evaluation on {run_directory}")
    if not (Path(run_directory) / "ir-metadata.yml").exists():
        raise ValueError("This is some 'pseudo evaluation'...")

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
            do_evaluation(task, dataset, run_directory)

    print_submissions_to_review(task, to_review)


if __name__ == '__main__':
    main()
