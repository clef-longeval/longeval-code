#!/usr/bin/env python3
from pathlib import Path

import click
from ir_datasets_longeval import load
import json


# TODO: Replace with your run id and your team id
RUN_ID = "my-system"
TEAM_ID = "my-team"

def generate_response(query, docs_store):
    metadata = {"run_id": RUN_ID, "type": "automatic", "narrative_id": query.query_id, "team_id": TEAM_ID}
    references = query.doc_ids

    answer = [
        {"text": f"I will next answer {query.default_text()}.", "citations": []},
        {"text": "Therefore, we have to consider the following aspects.", "citations": []},
    ]

    for ref, doc_id in zip(range(len(references)), references):
        answer += [{"text": docs_store.get(doc_id).title, "citations": [ref]}]

    return {"metadata": metadata, "references": references, "answer": answer}


@click.command()
@click.option("--dataset", type=str, default="longeval-sci-2026/clef-2026/rag", help="The dataset id or a local directory.")
@click.option("--output", type=Path, required=True, help="The output directory.")
def main(dataset, output):
    ir_dataset = load(dataset)
    docs_store = ir_dataset.docs_store()

    ret = []

    for q in ir_dataset.queries_iter():
        ret += [generate_response(q, docs_store)]

    with open(output, "w") as f:
        for response in ret:
            f.write(json.dumps(response) + '\n')

    # The ir-metadata description of your approach
    ir_metadata = Path(__file__).parent / "ir-metadata.yml"

    copy(ir_metadata, output / "ir-metadata.yml")


if __name__ == "__main__":
    main()
