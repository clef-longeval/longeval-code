#!/usr/bin/env python3
import json
from glob import glob
from tqdm import tqdm

docs = set()
with open('queries.jsonl', 'r') as f:
    for l in f:
        l = json.loads(l)
        for doc in l["doc_ids"]:
            docs.add(doc)

json_docs = []

for l in tqdm(glob('/home/maik/.ir_datasets/longeval-sci-2026/longeval_sci_09_11_2026_documents/data/processed/doc_collection_09032026_abstract_2/snapshot-3/longeval_sci_test-09-11_2026_abstract/documents/*.jsonl')):
    with open(l, 'r') as f:
        for i in f:
            i_parsed = json.loads(i)
            if i_parsed["id"] in docs:
                json_docs.append(i)

print(len(docs))
print(len(json_docs))

with open("documents/documents_000001.jsonl", "w") as f:
    for i in json_docs:
        f.write(i)

with open("report-requests.jsonl", "w") as outp, open('queries.jsonl', 'r') as inp:
    for l in inp:
        l = json.loads(l)
        outp.write(json.dumps({"topic_id": l["query_id"], "request_id": l["query_id"], "title": "some title..."}) + "\n")
