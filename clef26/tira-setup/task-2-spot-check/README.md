---
configs:
- config_name: inputs
  data_files:
  - split: train
    path: ["documents/*.jsonl", "metadata.json", "queries.txt", "queries.tsv"]
- config_name: truths
  data_files:
  - split: train
    path: ["queries.txt", "metadata.json", "qrels.txt"]

tira_configs:
  resolve_inputs_to: "."
  resolve_truths_to: "."
  baseline:
    link: https://github.com/clef-longeval/longeval-code/tree/main/clef26/topic-extraction/naive-baseline
    command: /baseline.py --dataset $inputDataset --retrieval BM25 --output $outputDir
    format:
      name: ["*.jsonl"]
  input_format:
    name: ["arbitrary"]
  truth_format:
    name: "qrels.txt"
  evaluator:
    image: webis/longeval-topic-evaluator:0.0.1
    command: "/validate.py --dataset $inputDataset --generated-topics $runDir --output $outputDir"
---

# Topic Extraction at LongEval'26: Spot-Check Dataset

This dataset is intended to spot check submissions for Task-2@LongEval on Topic Extraction.

Upload this to TIRA via.

```
tira-cli dataset-submission --path task-2-spot-check --task longeval-2026 --split train
```
