#!/usr/bin/env python3
import os
import click
import pandas as pd

def average_results(path, measures=None):
    df = pd.read_csv(path, compression='gzip')
    results = df[["measure", "value"]].groupby("measure").mean()["value"].to_dict()    
    if measures:
        results = {measures: results[measures]}
    return results
    

@click.command()
@click.option("--task", type=click.Choice(["longeval-2025"]), required=True, help="The task id in tira. See https://archive.tira.io/datasets?query=longeval-20")
@click.option("--datasets", type=click.Choice(["web-20250430-test", "sci-20250430-test"]), multiple=False, help="The dataset id in tira. See https://archive.tira.io/datasets?query=longeval-20")
@click.option("--output", type=str, required=True, help="The output directory.")
@click.option("--results", type=str, required=True, help="Path to the results")
@click.option("--measure", type=str, help="The measure to aggregate")
def main(task, datasets, output, results, measure):
    tab = []
    for team in os.listdir(os.path.join(results, datasets)):
        team_path = os.path.join(results, datasets, team)
        for run_id in os.listdir(team_path):
            run_directory = os.path.join(team_path, run_id)
            for version in os.listdir(run_directory):
                run_directory_version = os.path.join(run_directory, version)
                snapshot_results = {}
                for snapshot in os.listdir(run_directory_version):
                    
                    if snapshot == "ir-metadata.yml":
                        continue
                    try:
                        score = average_results(
                            os.path.join(run_directory_version, snapshot, "results_perquery.csv.gz"),
                            measures=measure
                        )
                        # add results to table
                        r = {
                            "team": team,
                            "run_id": run_id,
                            "version": version,
                            "snapshot": snapshot
                            }
                        r.update(**score)
                        
                        tab.append(r)
                    except FileNotFoundError:
                        print(f"Results file not found for {team}/{run_id}/{version}/{snapshot}")
                        continue

    pd.DataFrame(tab).to_csv(os.path.join(output, f"{task}-{datasets}-results.csv"), index=False)
    
if __name__ == "__main__":
    # import sys
    # sys.argv = [
    #     "script_name",  # doesn't matter, just a placeholder
    #     "--results", "/workspaces/longeval-code/clef25/evaluation-in-progress/evaluation-results-in-progress/results", "--task", "longeval-2025", "--datasets", "web-20250430-test", "--output", "hi", "--measure", "nDCG@100"
    # ]
    main()