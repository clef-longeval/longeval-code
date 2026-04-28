#!/usr/bin/env python3
from pathlib import Path

import click
import json


@click.command()
@click.option("--output", type=Path, required=True)
def main(output):
    required = {"snapshot-1": 180, "snapshot-2": 119, "snapshot-3": 182}
    for k, v in required.items():
        result = {"meta": {"team_name": "1", "description": "2", "run_name": "3"}}
        for i in range(v):
            result[str(i)] = ["a", "b", "c", "d", "e"]

        result = json.dumps(result)
        (output / (k + ".json")).write_text(result)


if __name__ == "__main__":
    main()
