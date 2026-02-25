---
configs:
- config_name: inputs
  data_files:
  - split: train
    path: ["documents/*.jsonl", "metadata.json", "queries.txt"]
- config_name: truths
  data_files:
  - split: train
    path: ["queries.txt", "metadata.json", "qrels.txt"]

tira_configs:
  resolve_inputs_to: "."
  resolve_truths_to: "."
  baseline:
    link: https://github.com/reneuir/lsr-benchmark/tree/main/step-03-retrieval-approaches/lexical/pyterrier-naive
    command: /run-pyterrier.py --dataset $inputDataset --retrieval BM25 --output $outputDir
    format:
      name: ["run.txt", "lightning-ir-document-embeddings", "lightning-ir-query-embeddings"]
  input_format:
    name: "lsr-benchmark-inputs"
  truth_format:
    name: "qrels.txt"
  evaluator:
    measures: ["nDCG@10","P@10"]
---

# Topic Extraction at LongEval'26: Spot-Check Dataset

This dataset is intended to spot check submissions for Task-2@LongEval on Topic Extraction.

Upload this to TIRA via.

```
tira-cli dataset-submission --path task-2-spot-check --task longeval-2026 --split train
```
