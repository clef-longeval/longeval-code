# Evaluation for Task 1

## Effectiveness
The effectiveness is evaluated per snapshot using different qrel sets.
Not all qrel sets are available for all queries at all snapshots.

`uv run evaluate-effectiveness.py --output data/effectiveness --qrels-set raw`
`uv run evaluate-effectiveness.py --output data/effectiveness --qrels-set dctr`
`uv run evaluate-effectiveness.py --output data/effectiveness --qrels-set llm`


## Robustness
`uv run evaluate-robustness.py --output data/robustness --qrels-set raw --pivot-dir data/task-1-submissions/outputs-flat/baseline bm25`
`uv run evaluate-robustness.py --output data/robustness --qrels-set dctr --pivot-dir data/task-1-submissions/outputs-flat/baseline bm25`
`uv run evaluate-robustness.py --output data/robustness --qrels-set llm --pivot-dir data/task-1-submissions/outputs-flat/baseline bm25`
