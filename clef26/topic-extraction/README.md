# Topic Extraction at LongEval'26

This directory contains baselines and evaluation scripts for the topic extraction task of [LongEval 2026](https://clef-longeval.github.io/).

## Baselines

We provide the following baselines:

- [baseline](baseline): is a baseline that uses an LLM to extract a topic from a LongEval query.
- [naive-baseline](naive-baseline): is a simplistic baseline that uses a template to create a topic description and narrative from a LongEval query.

## Evaluation

The [evaluation/validate.py](evaluation/validate.py) script is used during the shared task to validate that topics that are generated are complete. After all topics have been generated, we will use [Auto-Judge LLM relevance assessors](https://trec-auto-judge.cs.unh.edu/) to create relevance judgments and will validate the resulting relevance judgments. For this evaluation, we will verify:

1. how well the created relevance judgments are aligned over time with the future query logs (agreement with click-log qrels),
2. how well the created relevance judgments can distinguish retrieval systems submitted to Task-1 (ability to separate runs via nDCG),
3. how subjective the relevance judgments are (i.e., clarity: how consist are the annotations across different large language models).

