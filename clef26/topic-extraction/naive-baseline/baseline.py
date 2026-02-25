#!/usr/bin/env python3
from pathlib import Path

import click
from ir_datasets_longeval import load
import json
from tqdm import tqdm

# We use the tracker to monitor resource consumption etc. of the indexing and retrieval.
# The tracking is optional, i.e., you can remove it or switch to an alternative such as repro_eval.
from tirex_tracker import tracking, ExportFormat


def to_topic(query):
    return json.dumps({
        "qid": query.query_id,
        "query": query.default_text(),
        "description": f"I am looking for information on {query.default_text()}.",
        "narrative": f"Only papers that are highly relevant to {query.default_text()} in the most plausible way are relevant. Everything else is not relevant.",
    })


def process_queries(queries, output):
    ret = []
    for query in tqdm(queries.values()):
        ret.append(to_topic(query))

    with open(output/"topics.jsonl", "w") as f:
        f.write("\n".join(ret))


def load_all_queries(dataset):
    ret = {}
    ir_dataset = load(dataset)
    sub_collections = [ir_dataset] if not ir_dataset.get_datasets() else ir_dataset.get_datasets()

    for snapshot in sub_collections:
        for q in snapshot.queries_iter():
            ret[q.query_id] = q

    return ret


@click.command()
@click.option("--dataset", type=str, help="The dataset id or a local directory.")
@click.option("--output", type=Path, required=True, help="The output directory.")
def main(dataset, output):
    all_queries = load_all_queries(dataset)
    with tracking(export_file_path=output/"ir-metadata.yml", export_format=ExportFormat.IR_METADATA):
        process_queries(all_queries, output)


if __name__ == "__main__":
    main()
