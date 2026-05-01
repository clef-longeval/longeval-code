#!/usr/bin/env python3
from pathlib import Path

import click
from glob import glob
import json
import csv

TEAM_NAME = "my-team"
DESCRIPTION = "my-description"
RUN_NAME = "my-run"


def load_sessions(file_name):
    ret = {}
    with open(file_name) as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=["index", "user", "session", "query", "timestamp",  "serp", "search-id", "clicks"])
        for row in reader:
           if row["session"] not in ret:
               ret[row["session"]] = []
           ret[row["session"]].append(row["query"])
    return ret


def make_predictions(sessions):
    for session in sessions.keys():
        queries = sessions[session]
        if len(queries) >= 6:
            queries = queries[:4]
        while len(queries) < 5:
            # always predict the last query again
            queries.append(queries[-1])
        sessions[session] = queries
    return sessions


@click.command()
@click.option("--input-dir", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def main(input_dir, output):
    for i in glob(f"{input_dir}/*.csv"):
        sessions = load_sessions(i)
        sessions = make_predictions(sessions)
        sessions["meta"] = {"team_name": TEAM_NAME, "description": DESCRIPTION, "run_name": RUN_NAME}
        result = json.dumps(sessions)
        (output/i.split('/')[-1].replace('.csv', '.json')).write_text(result)


if __name__ == "__main__":
    main()
