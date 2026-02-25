# Baseline for the Topic Extraction Task at LongEval'26

This directory contains a baseline for the topic extraction task of [LongEval 2026](https://clef-longeval.github.io/). This baseline uses the [LongEval ir_datasets extension](https://github.com/clef-longeval/ir-datasets-longeval) without modification and tracks resource consumption in the [ir_metadata format](https://www.ir-metadata.org/).

## Input and Output

The software should create a topic for each unique query in the dataset. The `ir_datasets` ID for the CLEF 2026 test set is not yet published, but you can use the 2025 data or the spot check dataset `longeval-sci/spot-check/with-prior-data` to verify that your software works as expected.

The topics should be in `.jsonl` format with the fields:
- `qid`: The ID of the query.
- `query`: The original query.
- `description`: The generated description for the information need, i.e., what searchers for this topic had in their mind.
- `narrative`: The generated narrative for the information need, i.e., specifiyng which documents will be relevant or which will be not relevant.


For instance, for the query `ransomware detection` with id `1` from the spot-check dataset, a valid output could look like:

```
{"qid": "1", "query": "ransomware detection", "description": "I want to know which algorithms for ransomware detection are effective.", "narrative": "Papers that describe algorithms for ransomware detection are relevant when they also have an evaluation. Evaluation papers that just compare multiple ransomware detection algorithms are also relevant. Other aspects, such as describing which ransomware attacks exist, the history of ransomware detection, etc., are not relevant."}
```

## Development

This directory is [configured as DevContainer](https://code.visualstudio.com/docs/devcontainers/containers), i.e., you can open this directory with VS Code or some other DevContainer compatible IDE to work directly in the Docker container with all dependencies installed.

If you want to run it locally, please install the dependencies via `pip3 install -r requirements.txt`.

The baseline needs an OPENAI compatible LLM, please export the OPENAI_API_KEY, OPENAI_BASE_URL, and OPENAI_MODEL environment variables, e.g.,:

```
export OPENAI_API_KEY=...
export OPENAI_BASE_URL=https://openrouter.ai/api/v1
export OPENAI_MODEL=mistralai/mistral-small-3.1-24b-instruct:free
```

To create a run, please run:

```
./baseline.py --dataset longeval-sci/spot-check/with-prior-data --output output
```

## Verify that your outputs are valid

To verify that your submission in the `output` directory is valid, please run the validator:

```
../evaluation/validate.py --dataset longeval-sci/spot-check/with-prior-data --generated-topics output/topics.jsonl
```

This checks if the format is correct and if no descriptions respectively narratives are missing, a valid output should look like:

```
{'description-valid': 3, 'narrative-valid': 3, 'description-missing': 0, 'narrative-missing': 0}
```

## Optional: Code Submission to TIRA

**TBD.**
