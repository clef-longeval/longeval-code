# Evaluation in Progress

Run the evaluation on all (currently two) datasets via:
```
./evaluation-in-progress.py \
  --task longeval-2025 \
  --datasets sci-20250430-test --datasets web-20250430-test \
  --output evaluation-results-in-progress
```

The output `evaluation-results-in-progress` is on gitignore until after the submission deadline.

## ARP table
```
./make_table.py \
  --results /workspaces/longeval-code/clef25/evaluation-in-progress/evaluation-results-in-progress/results \ --task longeval-2025 \
  --datasets web-20250430-test \
  --output evaluation-results-in-progress/
  
```

## Analysis of ir_metadata

Run the evaluation on all (currently two) datasets via:
```
./analyse-ir-metadata.py \
  --task longeval-2025 \
  --datasets sci-20250430-test --datasets web-20250430-test
```


## Create Latex Tables

For Sci
```
./latex_table.py \
  --measures nDCG@10 \
  --measures nDCG@1000 \
  --sortby nDCG@1000 2025-01
```

For Web
```
./latex_table.py \
  --input evaluation-results-in-progress/longeval-2025-web-20250430-test-results.csv \
  --ids evaluation-results-in-progress/longeval-2025-web-20250430-test-results-run-ids.csv \
  --sortby nDCG@10 2023-08 \
  --measures nDCG@10
```

## Create Scatter Plot
For Sci
```
./scatterplot.py \
  --measures nDCG@10 \
  --sortby nDCG@10 2025-01 \
  --output scatter-sci.png
```

For Web
```
./scatterplot.py \
--input evaluation-results-in-progress/longeval-2025-web-20250430-test-results.csv \
--ids evaluation-results-in-progress/longeval-2025-web-20250430-test-results-run-ids.csv \
--sortby nDCG@10 2023-08 \
--measures nDCG@10 \
--output scatter-web.png
```


## Create Replication Evaluation
```
./evaluation-replicability.py \
--task longeval-2025 \
--datasets sci-20250430-test \
--output /workspaces/longeval-code/clef25/evaluation-in-progress/evaluation-results-in-progress/replicability \
--reference 2024-11
```