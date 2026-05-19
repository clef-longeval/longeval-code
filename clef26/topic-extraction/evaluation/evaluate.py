#!/usr/bin/env python3
import click
from ir_datasets_longeval import load
from pathlib import Path
from tqdm import tqdm
from subprocess import check_output
from glob import glob
from trectools import TrecRun, TrecPoolMaker
import json
import gzip
import os
from llm_predictions import read_failsave, parse_llm_response, run_predictions as run_llm_preds


PROMPTS_TO_RUN = ["umbrella_zeroshot_no_desc_no_narrative"]

def all_required_environment_variables_are_set():
    required_env_to_description = {
        "OPENAI_API_KEY": "The OPENAI_API_KEY environment variable is required. Please run something like 'export OPENAI_API_KEY=...'",
        "OPENAI_BASE_URL": "The OPENAI_BASE_URL environment variable is required. Please run something like 'export OPENAI_BASE_URL=https://openrouter.ai/api/v1'",
        "OPENAI_MODEL": "The OPENAI_MODEL environment variable is required. Please run something like 'export OPENAI_MODEL=mistralai/mistral-small-3.1-24b-instruct:free'",
    }
    errors = []

    for k, v in required_env_to_description.items():
        if k not in os.environ:
            errors += ["\n\n\t- " + v]
    
    if len(errors) > 0:
        print("Error: The LLM Endpoint is not configured." + ("".join(errors)))

    return len(errors) == 0


def load_sub_collections(dataset):
    ir_dataset = load(dataset)
    sub_collections = [ir_dataset] if not ir_dataset.get_datasets() else ir_dataset.get_datasets()
    return {i.get_snapshot(): i for i in sub_collections}


def load_all_run_files(dataset, output_directory):
    if output_directory.is_dir():
        print(f"Runs already exists. Delete directory to re-download runs: {output_directory}")
        return

    ir_datasets_id_to_tira_id = {"longeval-sci-2026/clef-2026/sci": "task-1-run-upload-20260428-training"}
    tira_id = ir_datasets_id_to_tira_id[dataset]
    cmd = ["tira-cli", "download", "--all-submissions", "--dataset", tira_id, "--output", str(output_directory)]
    check_output(cmd)


def run_pooling(subcollection, output_directory):
    # TODO remove hard-coded magic number
    expected_runs = 15
    runs = glob(f"{output_directory}/retrieval-runs/outputs-flat/*/{subcollection}/*run*")
    assert len(runs) == expected_runs
    parsed_runs = [TrecRun(i) for i in tqdm(runs, "Parse runs")]
    return TrecPoolMaker().make_pool(parsed_runs, strategy="topX", topX=10).pool


def pooling_is_already_finished(output_directory, dataset):
    for i in load_sub_collections(dataset).keys():
        if not (output_directory / "pooling" / f"{i}.jsonl.gz").is_file():
            return False
    return True

def pool_runs(output_directory, dataset):
    if pooling_is_already_finished(output_directory, dataset):
        print(f"Pooling already done. Delete directory to re-pool runs: {output_directory/'pooling'}")
        return

    subcollections = load_sub_collections(dataset)
    (output_directory / "pooling").mkdir(exist_ok=True, parents=True)
        
    for i in subcollections.keys():
        print(f"Pool {i}")
        qid_to_query = {q.query_id: q.default_text() for q in subcollections[i].queries_iter()}
        docs_store = subcollections[i].docs_store()
        pool = run_pooling(i, output_directory)
        to_persist = []

        docs_skipped = 0
        for qid in pool.keys():
            for docid in pool[qid]:
                try:
                    doc = docs_store.get(docid)
                except:
                    docs_skipped += 1
                    continue
                to_persist.append({
                    "query_id": qid,
                    "query": qid_to_query[qid],
                    "doc_id": docid,
                    "text": doc.default_text()
                })
        print(f"{docs_skipped} for {i}")
        with gzip.open(output_directory / "pooling" / f"{i}.jsonl.gz", "wt") as f:
            for l in to_persist:
                f.write(json.dumps(l) + "\n")


def run_llm_predictions(output_directory, dataset):
    if not all_required_environment_variables_are_set():
        return

    for i in load_sub_collections(dataset).keys():
        for prompt in PROMPTS_TO_RUN:
            target_file = output_directory / 'raw-llm-predictions' / (os.environ["OPENAI_MODEL"].replace("/", "-") + '-' + prompt + '.jsonl.gz')
            input_file = output_directory / "pooling" / f"{i}.jsonl.gz"
            run_llm_preds(input_file, prompt, target_file)


def create_qrels(output_directory, dataset):
    if not all_required_environment_variables_are_set():
        return

    prompt_to_preds = {}
    for prompt in PROMPTS_TO_RUN:
        preds_file = output_directory / 'raw-llm-predictions' / (os.environ["OPENAI_MODEL"].replace("/", "-") + '-' + prompt + '.jsonl.gz')
        preds_parsed = {}
        for l in read_failsave(preds_file):
            if l["query_id"] not in preds_parsed:
                preds_parsed[l["query_id"]] = {}
            preds_parsed[l["query_id"]][l["doc_id"]] = parse_llm_response(l["prediction"]["content"])[0]
        prompt_to_preds[prompt] = preds_parsed

    for i in load_sub_collections(dataset).keys():
        for prompt in PROMPTS_TO_RUN:
            target = os.environ["OPENAI_MODEL"].replace("/", "-") + '-' + prompt
            with gzip.open(output_directory / "pooling" / f"{i}.jsonl.gz", "rt") as f, open(output_directory / "qrels" / (target + "-" + i + ".qrels.txt"), "w") as outp:
                for l in f:
                    l = json.loads(l)
                    rel = prompt_to_preds[prompt][l["query_id"]][l["doc_id"]]
                    outp.write(f"{l['query_id']} 0 {l['doc_id']} {rel}\n")


@click.command()
@click.argument('dataset')
@click.argument('output-directory', type=Path)
def run_predictions(dataset: str, output_directory: Path):
    load_all_run_files(dataset, output_directory / "retrieval-runs")
    pool_runs(output_directory, dataset)
    run_llm_predictions(output_directory, dataset)
    create_qrels(output_directory, dataset)


if __name__ == '__main__':
    run_predictions()

