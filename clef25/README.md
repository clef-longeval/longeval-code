# Submission Instructions for LongEval'25

This directory contains example submissions for [LongEval 2025](https://clef-longeval.github.io/).

We use [TIRA.io](https://www.tira.io/) for submissions, you can either make run submissions or optionally software submissions.

## Run Submissions to Task 1 on Web-Retrieval

Submissions to the Web-Retrieval Task are expected to have the following structure:

```
tira-cli upload --dataset web-20250430-test --dry-run --directory web-submission-skeleton
```

## Run Submissions to Task 2 on Sci-Retrieval

Submissions to the Sci-Retrieval Task are expected to have the following structure:

```
/YOUR-SUBMISSION
├── 2024-11
│   └── run.txt.gz
├── 2025-01
│   └── run.txt.gz
└── ir-metadata.yml
```

The `ir-metadata.yml` file describes your approach in the [ir-metadata format](https://www.ir-metadata.org/) and the `run.txt.gz` files are standard TREC-style run files for the test snapshots (november 2024 and january 2025).

The directory [sci-submission-skeleton](sci-submission-skeleton) contains an example.

We use 

```
tira-cli login --token YOUR-TOKEN-FROM-TIRA-IO
```


```
tira-cli upload --dataset sci-20250430-test --dry-run --directory sci-submission-skeleton
```

## Software Submissions

The [pyterrier-baseline](pyterrier-baseline) directory contains instructions on how to make software submissions with [PyTerrier](https://github.com/terrier-org/pyterrier) as example that uses the [ir_datasets extension for LongEval](https://github.com/clef-longeval/ir-datasets-longeval).
