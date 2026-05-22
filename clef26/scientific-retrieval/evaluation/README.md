# Evaluation for Task 1


## Evaluate Measures
- `uv run python -m src.evaluate --qrels-set raw --output data --pivot-dir data/task-1-submissions/outputs-flat/put-to-front`

## Evaluate RoS
- `uv run python -m scripts.evaluate_system_ranking --input data/results.csv --output data --qrels-set raw --reference snapshot-1`
- `uv run python -m scripts.evaluate_system_ranking --input data/results.csv --output data --qrels-set dctr --reference snapshot-1`

## Create result table effectiveness
- `uv run python -m scripts.create_effectiveness_table --input data/results.csv --output data --measures nDCG@10--meta-measures ARP`
- `uv run python -m scripts.create_effectiveness_table --input data/results.csv --output data --measures nDCG@10 --meta-measures ARP`


## Create result plot effectiveness
- `uv run python -m scripts.create_effectiveness_plot --input data/results.csv --output data --qrels-set raw --reference snapshot-1 --measure nDCG@10`
- `uv run python -m scripts.create_effectiveness_plot --input data/results.csv --output data --qrels-set dctr --reference snapshot-1 --measure nDCG@10`


## Create result table robustness
- `uv run python -m scripts.create_robustness_plot --input data/results.csv --output data --snapshot snapshot-3 --measures nDCG@10 --meta-measures ARP --meta-measures AP --meta-measures RC --meta-measures DRI --meta-measures ER --meta-measures t-test`
- `uv run python -m scripts.create_robustness_plot --input data/results.csv --output data --snapshot snapshot-3 --measures nDCG@10 --meta-measures ARP --meta-measures AP --meta-measures RC --meta-measures DRI --meta-measures ER --meta-measures t-test`
