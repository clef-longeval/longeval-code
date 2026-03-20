# Scientific Search at LongEval'26

This directory contains example submissions for [LongEval 2026](https://clef-longeval.github.io/).

We use [TIRA.io](https://www.tira.io/task-overview/longeval-2026) for submissions, you can either make run submissions or optionally software submissions.


## Run Submissions to Task 1 on Sci-Retrieval

Submissions to the Sci-Retrieval Task are expected to have the following structure:

```
YOUR-SUBMISSION
├── snapshot-1
│   └── run.txt.gz
├── snapshot-2
│   └── run.txt.gz
├── snapshot-3
│   └── run.txt.gz
└── ir-metadata.yml
```

The `ir-metadata.yml` file describes your approach in the [ir-metadata format](https://www.ir-metadata.org/) and the `run.txt.gz` files are standard TREC-style run files for the three new test snapshots (snapshot 1 from March to May, snapshot 2 from June to August, and snapshot 3 from September to November).

The directory [sci-submission-skeleton](sci-submission-skeleton) contains an example (please replace all `ENTER_VALUE_HERE` occurences in the `ir-metadata.yml` file of the skeleton with your actual data to make it valid).

You can verify and submit your submission via `tira-cli`.

1. Install the tira client via:

```
pip3 install --upgrade tira
```

2. Verify your submission (i.e., the `--dry-run` flag):

```
tira-cli upload --dataset sci-20250430-test --dry-run --directory sci-submission-skeleton
```

For valid submissions, the output should look like:

![Screenshot_20250430_181548](https://github.com/user-attachments/assets/751fdaff-51fb-4259-acda-1d3907d48f26)


3. Upload your submission (i.e., remove the `--dry-run` flag and login):

```
# First login via your token from TIRA.io submission page
tira-cli login --token YOUR-TOKEN-FROM-TIRA-IO
tira-cli upload --dataset sci-20250430-test --directory sci-submission-skeleton
```

## Software Submissions

The [pyterrier-baseline](pyterrier-baseline) directory contains instructions on how to make software submissions with [PyTerrier](https://github.com/terrier-org/pyterrier) as example that uses the [ir_datasets extension for LongEval](https://github.com/clef-longeval/ir-datasets-longeval).
