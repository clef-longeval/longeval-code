#!/usr/bin/env python3
import click
from pathlib import Path
import os
import json

def write_output(filename, d):
    ret = []
    for k, v in d.items():
        ret += ['measure{{\n  key: "{}"\n  value: "{}"\n}}\n'.format(k, str(v))]
    with open(filename, "w") as f:
        f.write("\n".join(ret))


@click.command()
@click.option("--run", type=Path, required=True)
@click.option("--output", type=Path, required=True)
def main(run, output):
    ret = {}
    for f in os.listdir(run):
        if not f.endswith(".json"):
            continue

        parsed = json.loads((Path(run) / f).read_text())
        print(Path(run) / f)
        topics = len([i for i in parsed.keys() if i != "meta"])
        ret[Path(f).name.replace(".json", "")] = topics
    write_output(Path(output) / "evaluation.prototext", ret)

if __name__ == "__main__":
    main()
