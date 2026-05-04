---
configs:
- config_name: inputs
  data_files:
  - split: train
    path: ["queries.jsonl", "metadata.json", "documents/*.jsonl"]
- config_name: truths
  data_files:
  - split: train
    path: ["queries.jsonl", "report-requests.jsonl", "metadata.json"]

tira_configs:
  resolve_inputs_to: "."
  resolve_truths_to: "."
  baseline:
    link: https://github.com/clef-longeval/longeval-code/tree/main/clef26/rag/task-a-concatenation-baseline
    command: cp -R $inputDataset /tmp/data; export TIRA_INPUT_DATASET=/tmp/data; /baseline.py --dataset /tmp/data --output $outputDir
    format:
      name: ["LongEvalRAG"]
  input_format:
    name: ["arbitrary"]
  truth_format:
    name: ["arbitrary"]
  evaluator:
    image: mam10eks/rag4reports-evaluator:0.0.2
    command: "/naive-evaluator.py task-b $inputRun $inputDataset $outputDir"
---

# Retrieval Augmented Generation at LongEval'26: Test Dataset

This is the test dataset for Task-4@LongEval on Topic Extraction.

Upload this to TIRA via:

```
tira-cli dataset-submission --path task-4-rag --task longeval-2026 --split train
```
