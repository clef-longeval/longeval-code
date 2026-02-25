---
configs:
- config_name: inputs
  data_files:
  - split: train
    path: ["documents/*.jsonl", "metadata.json", "queries.txt"]
- config_name: truths
  data_files:
  - split: train
    path: ["queries.txt", "metadata.json", "qrels.txt", "documents/*.jsonl"]

tira_configs:
  resolve_inputs_to: "."
  resolve_truths_to: "."
  baseline:
    link: https://github.com/clef-longeval/longeval-code/tree/main/clef26/topic-extraction/naive-baseline
    command: /baseline.py --dataset $inputDataset --output $outputDir
    format:
      name: ["LongEvalLags"]
      config: {"lags":"2024-10"}
  input_format:
    name: ["arbitrary"]
  truth_format:
    name: "qrels.txt"
  evaluator:
    measures: ["Docs Per Query (Avg)","Docs Per Query (Min)", "Docs Per Query (Max)", "NumQueries"]
---

# Sci-Retrieval at LongEval'26: Spot-Check Dataset

This dataset is intended to spot check submissions for Task-1@LongEval on Scientific Retrieval.

Upload this to TIRA via:

```
tira-cli dataset-submission --path task-1-spot-check --task longeval-2026 --split train --dry-run
```

This yields something like:

```
IRA Dataset Submission:
✓ Your tira installation is valid.
✓ The configuration of the dataset task-2-spot-check is valid.
✓ The system inputs are valid.
✓ The truth data is valid.
✓ Repository for the baseline is cloned from https://github.com/clef-longeval/longeval-code.
✓ The baseline clef26/topic-extraction/naive-baseline is embedded in a Docker image.
✓ The baseline produced valid outputs at /tmp/tira-nh0b1krf for input /tmp/tira-iyv2oh01.
✓ The evaluation of the baseline produced valid outputs: {"Description-Valid": 3, "Narrative-Valid": 3, "Description-Missing": 0, "Narrative-Missing": 0}.
```
