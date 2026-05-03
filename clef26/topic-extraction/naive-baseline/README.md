# Naive Baseline for the Topic Extraction Task at LongEval'26

This directory contains a naive baseline for the topic extraction task of [LongEval 2026](https://clef-longeval.github.io/). This baseline just injects the query with a simplistic template into description and narratives. We use the [LongEval ir_datasets extension](https://github.com/clef-longeval/ir-datasets-longeval) without modification and track resource consumption in the [ir_metadata format](https://www.ir-metadata.org/).

## Input and Output

The software should create a topic for each unique query in the dataset. The `ir_datasets` ID for the CLEF 2026 test set is `longeval-sci-2026/clef-2026/sci`. If you want to verify that your software produces expected outputs, you can run your software on the spot check dataset `longeval-sci/spot-check/with-prior-data` to verify that your software works as expected.

The topics should be in `.jsonl` format with the fields:
- `qid`: The ID of the query.
- `query`: The original query.
- `description`: The generated description for the information need, i.e., what searchers for this topic had in their mind.
- `narrative`: The generated narrative for the information need, i.e., specifiyng which documents will be relevant or which will be not relevant.


For instance, for the query `ransomware detection` with id `1` from the spot-check dataset, a valid output could look like:

```
{"qid": "1", "query": "ransomware detection", "description": "I am looking for information on ransomware detection.", "narrative": "Only papers that are highly relevant to ransomware detection in the most plausible way are relevant. Everything else is not relevant."}
```

## Development

This directory is [configured as DevContainer](https://code.visualstudio.com/docs/devcontainers/containers), i.e., you can open this directory with VS Code or some other DevContainer compatible IDE to work directly in the Docker container with all dependencies installed.

If you want to run it locally, please install the dependencies via `pip3 install -r requirements.txt`.

To create a `topics.jsonl` file, please run:

```
./baseline.py --dataset longeval-sci-2026/clef-2026/sci --output output
```

## Verify that your outputs are valid

To verify that your submission in the `output` directory is valid, please run the validator:

```
../evaluation/validate.py --dataset longeval-sci-2026/clef-2026/sci --generated-topics output/topics.jsonl
```

This checks if the format is correct and if no descriptions respectively narratives are missing, a valid output should look like:

```
{'description-valid': 381, 'narrative-valid': 381, 'description-missing': 0, 'narrative-missing': 0}
```

## Run Submissions

For a run submission, please navigate to [https://www.tira.io/task-overview/longeval-2026](https://www.tira.io/task-overview/longeval-2026), register, click on submit. Please upload your output in a single zip file. The structure of this zip file should be:

```
.
├── ir-metadata.yml
└── topics.jsonl
```


## Optional: Code Submission to TIRA

If you want to make a code submission (for improved reproducibility and to help to run your approach in the future), submit this code via:

```
tira-cli code-submission \
    --path . \
    --task longeval-2026 \
    --dataset task-2-spot-check-20260225-training \
    --command '/baseline.py --dataset $inputDataset --output $outputDir' \
    --dry-run
```

The output should look like this:

```
TIRA Code Submission:
✓ The dataset task-2-spot-check-20260225-training is available locally.
✓ The code is in a git repository /home/maik/workspace/longeval-code.
✓ The code is embedded into the docker image clef26-topic-extraction-naive-baseline-0e18f.
✓ The docker image produced valid outputs on the dataset task-2-spot-check-20260225-training. (You can verify them at /tmp/tira-i54x_3s1)
```

If everything works like that on your local machine, you can upload to tira by removing the `--dry-run` flag from above.


