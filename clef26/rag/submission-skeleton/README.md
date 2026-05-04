# Submission Skeleton for LongEval Task 4 on RAG

The expected directory structure is:

```
.
├── generated-responses.jsonl
└── ir-metadata.yml
```

You can verify if your data is in a valid structure locally via (where `.` is the directory containing your data):

```
# Update your tira client (the RAG format for LongEval was only added recently)
pip3 install --upgrade tira
#
tira-cli upload --dataset task-4-rag-20260504-training --dry-run --directory .
```


If the output is valid, please compress the files into a zip file and upload the zip file to TIRA.

