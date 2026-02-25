#!/usr/bin/env python3
import click
from pathlib import Path
from ir_datasets_longeval import load
from tira.check_format import lines_if_valid
from tira.io_utils import to_prototext


def all_query_ids(dataset):
    ret = set()
    ir_dataset = load(dataset)
    sub_collections = [ir_dataset] if not ir_dataset.get_datasets() else ir_dataset.get_datasets()

    for snapshot in sub_collections:
        for q in snapshot.queries_iter():
            ret.add(q.query_id)

    return ret


@click.command()
@click.option("--dataset", type=str, required=True, help="The dataset id or a local directory.")
@click.option("--generated-topics", type=Path, required=True, help="The generated topics to verify.")
@click.option("--output", type=Path, required=False, help="The output directory.")
def main(dataset, generated_topics, output):
    all_queries = all_query_ids(dataset)

    ret = {"description-valid": 0, "narrative-valid": 0}

    for topic in lines_if_valid(generated_topics, "*.jsonl"):
        if "qid" not in topic or topic["qid"] not in all_queries:
            continue

        ret["description-valid"] += 1 if "description" in topic and len(topic["description"]) >= 3 else 0
        ret["narrative-valid"] += 1 if "narrative" in topic and len(topic["narrative"]) >= 3 else 0

    ret["description-missing"] = len(all_queries) - ret["description-valid"]
    ret["narrative-missing"] = len(all_queries) - ret["narrative-valid"]

    print(ret)
    if output:
        output.mkdir(exist_ok=True, parents=True)
        with open(output / "evaluation.prototext", "w") as f:
            f.write(to_prototext([ret]))


if __name__ == '__main__':
    main()
