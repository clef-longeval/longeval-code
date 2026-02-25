# Baseline for the Topic Extraction Task at LongEval'26

This directory contains a baseline for the topic creation task of [LongEval 2026](https://clef-longeval.github.io/). This baseline uses the [LongEval ir_datasets extension](https://github.com/clef-longeval/ir-datasets-longeval) without modification and tracks resource consumption in the [ir_metadata format](https://www.ir-metadata.org/).

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
