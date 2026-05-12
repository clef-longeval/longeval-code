#!/usr/bin/env python3
from pathlib import Path
import json
from shutil import copy
from glob import glob
from ir_datasets_longeval import load


TARGET_DIR = Path("longeval-rag")
SRC_DIR = Path("longeval-rag-responses")
IRDS_ID = "longeval-sci-2026/clef-2026/rag"


def load_all_document_ids(run_file):
    ret = set()

    with open(run_file) as f:
        for l in f:
            l = json.loads(l)
            for i in l["references"]:
                ret.add(i)

    return ret


def persist_docs(document_ids):
    ds = load(IRDS_ID).docs_store()
    ret = {}
    print(f"Persist {len(document_ids)} documents.")

    for i in document_ids:
        doc = ds.get(str(i))
        links = [l for l in doc.links if l["type"] == "display"]

        ret[i] = {
            "id": i,
            "text": doc.default_text(),
            "title": doc.title,
            "url": links[0]["url"]
        }

    return ret


def persist_topics(output_file, irds_id):
    output_file.parent.mkdir(exist_ok=True, parents=True)
    irds = load(IRDS_ID)
    with open(output_file, "w") as f:
        for query in irds.queries_iter():
            f.write(json.dumps({"request_id": query.query_id, "title": query.default_text()}) + "\n")


def main():
    config = [json.loads(i) for i in Path('longeval-rag-responses/metadata.jsonl').read_text().split("\n") if i]
    persist_topics(TARGET_DIR / "topics" / "longeval-2026-task4-topics.jsonl", IRDS_ID)
    docs = []
    for i in config:
        src = glob(f"{SRC_DIR}/{i['flat-outputs']}/*.jsonl")
        assert len(src) == 1
        src = Path(src[0])
        target = TARGET_DIR / "runs" / "longeval-2026" / (src.parent.name.replace(" ", "-") + ".jsonl")
        target.parent.mkdir(exist_ok=True, parents=True)
        copy(src, target)
        docs += list(load_all_document_ids(target))
    docs = persist_docs(set(docs))
    for response in glob(str(TARGET_DIR / "runs" / "longeval-2026" / "*")):
        raw_response = Path(response).read_text().split("\n")
        raw_response = [json.loads(i) for i in raw_response if i]
        with open(response, "w") as f:
            for l in raw_response:
                docs_in_response = {i: docs[i] for i in l["references"]}
                l["documents"] = docs_in_response
                f.write(json.dumps(l) + "\n")


if __name__ == '__main__':
    main()
