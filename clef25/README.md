# Submission Instructions for LongEval'25

This directory contains example submissions for [LongEval 2025](https://clef-longeval.github.io/).

We use [TIRA.io](https://www.tira.io/) for submissions, you can either make run submissions or optionally software submissions.

## Run Submissions to Task 1 on Web-Retrieval

ToDo: More descriptions:

```
tira-cli upload --dataset web-20250430-test --dry-run --directory web-submission-template
```

## Run Submissions to Task 2 on Sci-Retrieval

```
tira-cli upload --dataset sci-20250430-test --dry-run --directory sci-submission-template
```

## Software Submissions

The [pyterrier-baseline](pyterrier-baseline) directory contains instructions on how to make software submissions with [PyTerrier](https://github.com/terrier-org/pyterrier) as example that uses the [ir_datasets extension for LongEval](https://github.com/clef-longeval/ir-datasets-longeval).
