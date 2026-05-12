# Connection between LongEval Task 4 and AutoJudge

### Step 1: Download the data

```
tira-cli download --all-submissions --dataset task-4-rag-20260504-training --output longeval-rag-responses
```

### Step 2: Format the data

```
./reformat-data.py
```

