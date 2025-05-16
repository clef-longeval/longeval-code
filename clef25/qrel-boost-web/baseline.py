#!/usr/bin/env python3
from pathlib import Path
from shutil import copy
from typing import Optional
import click
import pandas as pd
import pyterrier as pt
from ir_datasets_longeval import load

# We use the tracker to monitor resource consumption etc. of the indexing and retrieval.
# The tracking is optional, i.e., you can remove it or switch to an alternative such as repro_eval.
from tirex_tracker import tracking


class QrelBoost(pt.Transformer):
    def __init__(self, dataset, memory: Optional[int] = None):
        super().__init__()
        self.dataset = dataset
        self.memory = memory if memory is not None else len(dataset.prior_datasets)

    def boost(self, doc, _lambda=0.7, mu=2):
        if doc["label"] == 1:
            return doc["score"] * _lambda**2
        elif doc["label"] == 2:
            return doc["score"] * _lambda**2 * mu
        else:
            return doc["score"] * (1 - _lambda) ** 2

    def apply_boost(self, df, prior_dataset):
        assert prior_dataset != self.dataset.timestamp.strftime(
            "%Y-%m"
        ), "Cannot apply boost to the same sub-collection"

        historic_qrels = pt.io.read_qrels(prior_dataset.qrels_path())

        df = df.merge(historic_qrels, on=["docno", "qid"], how="left")
        df = df.drop_duplicates(keep="first")

        df["score"] = df.apply(self.boost, axis=1)
        df.drop(columns=["label"], inplace=True)
        return df

    def transform(self, df):
        print(f"Applying boost to {self.memory} prior datasets")
        # df["score"] = df.groupby("qid")["score"].transform(lambda x: x / x.max())

        for prior_dataset in self.dataset.get_prior_datasets()[: self.memory]:
            if prior_dataset.has_qrels():
                df = self.apply_boost(df, prior_dataset).copy()
            else:
                print(
                    f"Skipping prior dataset {prior_dataset.get_snapshot()}, no qrels available"
                )
                continue

        df["rank"] = df.groupby("qid")["score"].rank(ascending=False).astype(int)
        df = df.sort_values(["qid", "rank"])

        return df


def doc_generator(ir_dataset):
    indexed = set()
    # This is a generator function that yields documents from the dataset
    for doc in ir_dataset.docs_iter():
        if doc.doc_id in indexed or not doc.default_text():
            continue
        indexed.add(doc.doc_id)
        yield {
            "docno": doc.doc_id,
            "text": doc.default_text(),
        }


def get_index(ir_dataset, index_directory):
    # PyTerrier needs an absolute path
    index_directory = index_directory.resolve().absolute()

    if (
        not index_directory.exists()
        or not (index_directory / "data.properties").exists()
    ):
        # build the index
        with tracking(export_file_path=index_directory / "index-ir-metadata.yml"):
            indexer = pt.IterDictIndexer(
                str(index_directory),
                overwrite=True,
                meta={"docno": 20, "text": 20480},
                meta_reverse=["docno"],
                stemmer="FrenchSnowballStemmer",
                stopwords=None,
                tokeniser="UTFTokeniser",
                verbose=True,
            )

            # you can do some custom document processing here
            indexer.index(doc_generator(ir_dataset))

    return pt.IndexFactory.of(str(index_directory))


def process_dataset(ir_dataset, index_directory, output_directory, memory):
    if (output_directory / "run.txt.gz").exists():
        return

    index = get_index(ir_dataset, index_directory)
    with tracking(export_file_path=output_directory / "retrieval-ir-metadata.yml"):

        bm25 = pt.terrier.Retriever(index, wmodel="BM25")
        if ir_dataset.get_prior_datasets():
            print(">>> Using QrelBoost")
            pipeline = bm25 >> QrelBoost(ir_dataset, memory)
        else:
            print(">>> No prior datasets, using BM25")
            pipeline = bm25

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

        run = pipeline(topics)
        pt.io.write_results(run, output_directory / "run.txt.gz")
        copy(
            index_directory / "index-ir-metadata.yml",
            output_directory / "index-ir-metadata.yml",
        )


@click.command()
@click.option("--dataset", type=str, help="The dataset id or a local directory.")
@click.option("--output", type=Path, required=True, help="The output directory.")
@click.option("--index", type=Path, required=True, help="The index directory.")
@click.option(
    "--memory",
    type=int,
    default=None,
    required=False,
    help="The number of prior datasets to be used.",
)
def main(dataset, output, index, memory):
    ir_dataset = load(dataset)
    datasets = (
        [ir_dataset] if not ir_dataset.get_datasets() else ir_dataset.get_datasets()
    )

    for d in datasets:
        process_dataset(d, index / d.get_snapshot(), output / d.get_snapshot(), memory)

    # The ir-metadata description of your approach
    ir_metadata = Path(__file__).parent / "ir-metadata.yml"

    copy(ir_metadata, output / "ir-metadata.yml")


if __name__ == "__main__":
    main()
