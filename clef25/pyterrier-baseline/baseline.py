#!/usr/bin/env python3
from pathlib import Path
from shutil import copy

import click
import pandas as pd
import pyterrier as pt
from ir_datasets_longeval import load

#
# We use the tracker to monitor resource consumption etc. of the indexing and retrieval.
# The tracking is optional, i.e., you can remove it or switch to an alternative such as repro_eval.
from tirex_tracker import tracking


def get_index(ir_dataset, index_directory):
    # PyTerrier needs an absolute path
    index_directory = index_directory.resolve().absolute()

    if (
        not index_directory.exists()
        or not (index_directory / "data.properties").exists()
    ):
        with tracking(export_file_path=index_directory / "index-ir-metadata.yml"):
            # build the index
            indexer = pt.IterDictIndexer(
                str(index_directory), overwrite=True, meta={"docno": 100, "text": 20480}
            )

            # you can do some custom document processing here
            docs = (
                {"docno": i.doc_id, "text": i.default_text()}
                for i in ir_dataset.docs_iter()
            )
            indexer.index(docs)

    return pt.IndexFactory.of(str(index_directory))


def process_dataset(ir_dataset, output_directory):
    if (output_directory / "run.txt.gz").exists():
        return

    index = get_index(ir_dataset, output_directory / "index")
    with tracking(export_file_path=output_directory / "retrieval-ir-metadata.yml"):
        bm25 = pt.terrier.Retriever(index, wmodel="BM25")

        # potentially do some query processing
        topics = pd.DataFrame(
            [
                {"qid": i.query_id, "query": i.default_text()}
                for i in ir_dataset.queries_iter()
            ]
        )

        # PyTerrier needs to use pre-tokenized queries
        tokeniser = pt.java.autoclass(
            "org.terrier.indexing.tokenisation.Tokeniser"
        ).getTokeniser()

        topics["query"] = topics["query"].apply(
            lambda i: " ".join(tokeniser.getTokens(i))
        )

        run = bm25(topics)
        pt.io.write_results(run, output_directory / "run.txt.gz")


@click.command()
@click.option("--dataset", type=str, help="The dataset id or a local directory.")
@click.option(
    "--output-directory", type=click.Path(), required=True, help="The output directory."
)
def main(dataset, output_directory):
    ir_dataset = load(dataset)

    if not ir_dataset.get_lags():
        process_dataset(ir_dataset, Path(output_directory))
    else:
        for ds in ir_dataset.get_lags():
            process_dataset(ds, Path(output_directory) / ds.get_lag())

    copy(
        Path(__file__).parent / "ir-metadata.yml",
        Path(output_directory) / "ir-metadata.yml",
    )


if __name__ == "__main__":
    main()
