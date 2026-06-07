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
    expected_runs = 24
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


def create_qrels(output_directory, dataset, prompt):
    if not all_required_environment_variables_are_set():
        return

    preds_file = output_directory / 'raw-llm-predictions' / (os.environ["OPENAI_MODEL"].replace("/", "-") + '-' + prompt + '.jsonl.gz')
    preds_parsed = {}
    for l in read_failsave(preds_file):
        if l["query_id"] not in preds_parsed:
            preds_parsed[l["query_id"]] = {}
        preds_parsed[l["query_id"]][l["doc_id"]] = parse_llm_response(l["prediction"]["content"])[0]

    for i in load_sub_collections(dataset).keys():
        target = os.environ["OPENAI_MODEL"].replace("/", "-") + '-' + prompt
        with gzip.open(output_directory / "pooling" / f"{i}.jsonl.gz", "rt") as f, open(output_directory / "qrels" / (target + "-" + i + ".qrels.txt"), "w") as outp:
            for l in f:
                l = json.loads(l)
                if l["query_id"] not in preds_parsed:
                    continue
                rel = preds_parsed[l["query_id"]][l["doc_id"]]
                outp.write(f"{l['query_id']} 0 {l['doc_id']} {rel}\n")

def create_qrels_on_all_prompts(output_directory, dataset):
    for prompt in PROMPTS_TO_RUN:
        create_qrels(output_directory, dataset, prompt)

@click.group()
def main():
    pass


@main.command()
@click.argument('dataset')
@click.argument('output-directory', type=Path)
def baseline_predictions(dataset: str, output_directory: Path):
    load_all_run_files(dataset, output_directory / "retrieval-runs")
    pool_runs(output_directory, dataset)
    run_llm_predictions(output_directory, dataset)
    create_qrels_on_all_prompts(output_directory, dataset)


def load_topic_impl(approach):
    topics_file = Path("../../../../longeval-26-evaluation/task-2-submissions/outputs-flat/") / approach
    if not topics_file.is_file():
        topics_file = glob(f"{topics_file}/*.jsonl")
        assert len(topics_file) == 1
        topics_file = Path(topics_file[0])
    ret = {}
    for l in topics_file.read_text().split("\n"):
        if not l:
            continue
        l = json.loads(l)
        q = l["query"].lower().strip()
        assert q not in ret, q
        ret[q] = l

    return ret
    
def run_llm_predictions_extracted_topics(output_directory, dataset, input_topics, topic_allow_list):
    if not all_required_environment_variables_are_set():
        return

    topics = load_topic_impl(input_topics)
    from prompts import umbrella_zeroshot_basic

    def prompt_impl(q, d):
        if q.lower().strip() not in topics:
            print(json.dumps(list(topics.keys()), indent=2))
        topic = topics[q.lower().strip()]
        ret = umbrella_zeroshot_basic(query=q, document=d, narrative=topic["narrative"], description=topic["description"])
        return ret

    prompt = "umbrella_zeroshot_basic-" + input_topics

    for i in load_sub_collections(dataset).keys():
        target_file = output_directory / 'raw-llm-predictions' / (os.environ["OPENAI_MODEL"].replace("/", "-") + '-' + prompt + '.jsonl.gz')
        input_file = output_directory / "pooling" / f"{i}.jsonl.gz"
        run_llm_preds(input_file, prompt, target_file, topic_allow_list, prompt_impl)


@main.command()
@click.argument('dataset')
@click.argument('prompt')
@click.argument('output-directory', type=Path)
def predictions_on_topic(dataset: str, prompt: str, output_directory: Path):
    topic_allow_list = set([
        "10c7ef19d812f4c1bacecc0ee54d30a8", "1bc4dce8577f8939ace5bf16d86b1829", "220b79bfcc0380e3999edb61a0c103f6",
        "253235b2573e803d3d7cb91bbe626407", "2c19f7bf825bc626b8ec40399ae413f8", "2cb72c6bf8046051f3e04155984cc99d",
        "32b77e26bf1e161271a79b443af3b421", "4167db3ceb4e698b81750084e926f71c", "4880fdf7ff336b249af928cf93f43f0a",
        "4ed1037709aa13b70fca0575c1c88c48", "56311e2226162fc29277c68b6e6e586b", "5fcf8eb1af05248be1503e13e8940abf",
        "6513b320bfbcd0ed11d192b17f985131", "67f8b0b8c80910677c062be26466333e", "6d1f50ca1928f230f5e90b7573fedc85",
        "70a7a4c11f729b8ced811befa82aa2b7", "781ce9d684cf75f39303e94af5013c41", "8563a9d294a5cbb4e837f30028ce6a6d",
        "8cc85d9d1d5424fb44a6e3c22ecc8a12", "93552e2eb156f5c55161c41a17f2a01a", "a17857d1a641623051cc8b231abd516b",
        "a64aae27da8e92c91015c275eb443a14", "a8a463fe5c77781ae586810949bc43b4", "c0837308bd8bdd88372e59d7fbcdd79a",
        "c3d39be1a3633d49008261165f6058b6", "cf0a23a14082d55d74fad12e78a868e6", "d2af595f032a1958c62ceea6b1545833",
        "d49230534d6a85b88426fb74707a9cbb", "d6e9712bf4d78dc25582d46273456358", "d7121387aa077f9d346a6b5a0378e5c6"
    ])
    run_llm_predictions_extracted_topics(output_directory, dataset, prompt, topic_allow_list)
    create_qrels(output_directory, dataset, "umbrella_zeroshot_basic-" +prompt)


if __name__ == '__main__':
    main()

