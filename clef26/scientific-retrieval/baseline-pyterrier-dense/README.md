# PyTerrier Dense Baseline for LongEval'26

This directory contains a PyTerrier Dense baseline for the retrieval task of [LongEval 2026](https://clef-longeval.github.io/). This baseline uses the [LongEval ir_datasets extension](https://github.com/clef-longeval/ir-datasets-longeval) without modification and tracks resource consumption for indexing and retrieval in the ir_metadata format.

## Artifacts
You can directly download and use the index and run created by this baseline to rerank the fist stage ranking or kick-start your own experiments.

### Index
The indices are available in the [longeval-2026-baseline-dense](https://huggingface.co/collections/jueri/longeval-2026-baseline-dense) collection at Hugging Face and can be directly loaded as an [PyTerrier artefact](https://pyterrier.readthedocs.io/en/latest/artifacts/how-to.html).
```Python
import pyterrier as pt

index = pt.Artifact.from_hf('jueri/longeval-2026-snapshot-1-index')
```

### Run
The runs are currently hosted at [Sciebo](https://th-koeln.sciebo.de/s/jYQcwX9aajDLX4z) and the download password is longeval. The runs can be used in PyTerrier after downloading:


```Python
import pyterrier as pt

first_stage = pt.Transformer.from_df(pt.io.read_results("/path/to/run.tar.gz", topics=topics))
```

## Development

This directory is [configured as DevContainer](https://code.visualstudio.com/docs/devcontainers/containers), i.e., you can open this directory with VS Code or some other DevContainer compatible IDE to work directly in the Docker container with all dependencies installed.

If you want to run it locally, please install the dependencies via `pip3 install -r requirements.txt`.

To create a run, please run:

```
./baseline.py --dataset longeval-sci/spot-check/with-prior-data --output output --index indexes
```
