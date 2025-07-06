#!/usr/bin/env python3
from pathlib import Path
from shutil import copy

import click
from ir_datasets_longeval import load
import json
from tqdm import tqdm

# We use the tracker to monitor resource consumption etc. of the indexing and retrieval.
# The tracking is optional, i.e., you can remove it or switch to an alternative such as repro_eval.
from tirex_tracker import tracking, ExportFormat

def get_llm_response(request, base_url, llm_model):
    from openai import OpenAI as cli
    messages = []
    messages.append({"role": "user", "content": request})

    output = cli().chat.completions.create(model=llm_model, messages=messages)

    return output.choices[0].message.to_dict()

def build_prompt(query, rel, non_rel):
    return f"""You are employed as relevance assessor at NIST in the Information Retrieval Group working at TREC. You are already pensioned and have worked as intelligence officer for over 40 years, now you still help because you are really passionate. You will help to evaluate academic search engines for which you will be given a query that was submitted to an search engine and one relevant and one non-relevant document that are abstracts of scientific papers. Please respond exactly in json format with two fields, "narrative" that contains a standard TREC-style narrative and a "description" that contains a standard TREC-style description. Respond only with one valid json.\n\nThe query is: "{query}"\n\nRelevant Document: {rel}\n\nNon-Relevant Document: {non_rel}"""

def process_dataset(dataset, output_path, llm_model, llm_endpoint):
    docs_store = dataset.docs_store()

    with tracking(export_file_path=output_path/"ir-metadata.yml", export_format=ExportFormat.IR_METADATA):
        query_to_relevant = {}
        query_to_non_relevant = {}
        for qrel in dataset.qrels_iter():
            target_dict = query_to_relevant if qrel.relevance > 0 else query_to_non_relevant
            if qrel.query_id not in target_dict:
                target_dict[qrel.query_id] = set()
            target_dict[qrel.query_id].add(qrel.doc_id)

        with open(output_path/"simulations.jsonl", "w") as f:
            for query in tqdm(list(dataset.queries_iter())):
                rel = docs_store.get(list(query_to_relevant[query.query_id])[0]).default_text()
                irr = docs_store.get(list(query_to_non_relevant[query.query_id])[0]).default_text()
                request = build_prompt(query.default_text(), rel, irr)
                response = get_llm_response(request, llm_endpoint, llm_model)
                f.write(json.dumps({"query_id": query.query_id, "snapshot": dataset.get_snapshot(), "request": request, "response": response}))


@click.command()
@click.option("--dataset", type=str, help="The dataset id or a local directory.")
@click.option("--output", type=Path, required=True, help="The output directory.")
@click.option("--llm-model", type=str, default="o4-mini", required=False, help="The model to use.")
@click.option("--llm-endpoint", type=str, default="https://api.openai.com", required=False, help="The endpoint to use.")
def main(dataset, output, llm_model, llm_endpoint):
    ir_dataset = load(dataset)
    sub_collections = [ir_dataset] if not ir_dataset.get_datasets() else ir_dataset.get_datasets()

    for snapshot in sub_collections:
        process_dataset(snapshot, Path(output) / snapshot.get_snapshot(), llm_model, llm_endpoint)


if __name__ == "__main__":
    main()
