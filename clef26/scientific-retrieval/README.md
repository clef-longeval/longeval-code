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

The directory [submission-skeleton](submission-skeleton) contains an example (please replace all `ENTER_VALUE_HERE` occurences in the `ir-metadata.yml` file of the skeleton with your actual data to make it valid).

You can verify and submit your submission via `tira-cli`.

1. Install the tira client via:

```
pip3 install --upgrade tira
```

2. Verify your submission (i.e., the `--dry-run` flag):

```
tira-cli upload --dataset task-1-run-upload-20260428-training --dry-run --directory submission-skeleton
```

For valid submissions, the output should look like:

<img width="1638" height="401" alt="Screenshot_20260504_124530" src="https://github.com/user-attachments/assets/556d05a8-d39e-40b9-b6b7-613bad295cbe" />



3. Upload your submission: Please either upload your directory as a zip file in the UI or use the cli (i.e., remove the `--dry-run` flag and login):

```
# First login via your token from TIRA.io submission page
tira-cli login --token YOUR-TOKEN-FROM-TIRA-IO
tira-cli upload --dataset task-1-run-upload-20260428-training --directory YOUR-DIRECTORY
```

## Software Submissions

The [pyterrier-baseline](pyterrier-baseline) directory contains instructions on how to make software submissions with [PyTerrier](https://github.com/terrier-org/pyterrier) as example that uses the [ir_datasets extension for LongEval](https://github.com/clef-longeval/ir-datasets-longeval).
