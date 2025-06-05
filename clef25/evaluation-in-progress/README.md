# Evaluation in Progress

Run the evaluation on all (currently two) datasets via:
```
./evaluation-in-progress.py \
  --task longeval-2025 \
  --datasets sci-20250430-test --datasets web-20250430-test \
  --output evaluation-results-in-progress
```

The output `evaluation-results-in-progress` is on gitignore until after the submission deadline.


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

## Create Box Plot
For Sci
```
./boxplot.py \
  --measures nDCG@10 
  --sortby nDCG@10 2025-01 
  --output .
```

For Web
```
./boxplot.py \
--input evaluation-results-in-progress/longeval-2025-web-20250430-test-results.csv \
--ids evaluation-results-in-progress/longeval-2025-web-20250430-test-results-run-ids.csv \
--sortby nDCG@10 2023-08 
--measures nDCG@10 \
--output . 
```