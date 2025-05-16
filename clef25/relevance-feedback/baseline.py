#!/usr/bin/env python3
from pathlib import Path
from shutil import copy
from typing import Optional
import click
import pandas as pd
import pyterrier as pt
from ir_datasets_longeval import load
import math

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
        print(f">>> Index not found at {index_directory}, building it")
        with tracking(export_file_path=index_directory / "index-ir-metadata.yml"):
            # build the index
            indexer = pt.IterDictIndexer(
                str(index_directory),
                overwrite=True,
                meta={"docno": 100, "text": 20480},
                meta_reverse=["docno"],
            )

            # you can do some custom document processing here
            docs = (
                {"docno": i.doc_id, "text": i.default_text()}
                for i in ir_dataset.docs_iter()
            )
            indexer.index(docs)

    return pt.IndexFactory.of(str(index_directory))


class HistoricIndex:
    def __init__(self, ir_dataset, indices_dir: Path):
        self.index = get_index(ir_dataset, indices_dir)
        self.di = self.index.getDirectIndex()
        self.doi = self.index.getDocumentIndex()
        self.lex = self.index.getLexicon()
        self.meta = self.index.getMetaIndex()

    def get_tf_idf_scores(self, docno, fb_terms: int = 10):
        docid = self.meta.getDocument("docno", docno)

        scores = []
        for posting in self.di.getPostings(self.doi.getDocumentEntry(docid)):
            termid = posting.getId()
            lee = self.lex.getLexiconEntry(termid)
            le = self.lex.getLexiconEntry(lee.getKey())
            term_in_doc = posting.getFrequency()
            document_frequency = le.getDocumentFrequency()
            max_document_frequency = le.getMaxFrequencyInDocuments()

            tf = term_in_doc / max_document_frequency
            idf = math.log(self.doi.getNumberOfDocuments() / document_frequency)
            tf_idf = tf * idf
            scores.append((tf_idf, lee.getKey()))

        ret = (
            pd.DataFrame(scores, columns=["score", "term"])
            .sort_values("score", ascending=False)
            .head(fb_terms)
        )
        return ret

    def apply_scores(self, docno, fb_terms: int = 10):
        try:
            return self.get_tf_idf_scores(docno, fb_terms)
        except:
            return pd.DataFrame()


class RF(pt.Transformer):
    def __init__(
        self,
        dataset,
        indices_dir: Path,
        memory: Optional[int] = None,
        fb_terms: int = 10,
        fb_docs: int = 3,
    ):
        super().__init__()
        self.dataset = dataset
        self.indices_dir = indices_dir
        self.memory = memory if memory is not None else len(dataset.prior_datasets)
        self.fb_terms = fb_terms
        self.fb_docs = fb_docs

    def get_candidates(self, df, prior_dataset):
        # Load qrels
        historic_qrels = pt.io.read_qrels(prior_dataset.qrels_path())

        # load candidate docs for query expansion
        candidade_docs = df.merge(historic_qrels, on=["qid", "qid"])
        candidade_docs = candidade_docs[candidade_docs["label"] >= 1]
        candidade_docs = (
            candidade_docs.sort_values(["qid", "label"], ascending=[True, False])
            .groupby("qid")
            .head(self.fb_docs)
        )
        return candidade_docs

    def top_terms(self, series):
        df = pd.concat(series.tolist())
        if df.empty:
            return pd.DataFrame(columns=["score", "term"])
        df = (
            df.sort_values("score", ascending=False)
            .drop_duplicates("term", keep="first")
            .head(self.fb_terms)
        )
        terms = df["term"].tolist()
        return terms

    def transform(self, df):
        print(f">>> Applying boost to {self.memory} prior datasets")

        candidates = []
        # limit to the n last
        for prior_dataset in self.dataset.get_prior_datasets()[: self.memory]:
            if prior_dataset.has_qrels():
                print(f">>> Loading index for {prior_dataset.snapshot}")
                prior_index_dir = self.indices_dir / prior_dataset.snapshot
                hi = HistoricIndex(prior_dataset, prior_index_dir)

                candidade_docs = self.get_candidates(df, prior_dataset)

                # get tf-idf scores
                candidade_docs["terms"] = candidade_docs.apply(
                    lambda x: hi.apply_scores(x["docno"], fb_terms=self.fb_terms), axis=1
                )

                candidates.append(candidade_docs)
            else:
                print(
                    f"Skipping prior dataset {prior_dataset.get_snapshot()}, no qrels available"
                )
                continue
          

        all_candidates = pd.concat(candidates)
        expanded = all_candidates.groupby("qid")["terms"].agg(self.top_terms)

        print(
            f">>> Expanded terms: {len(expanded)} of {len(df)} queries. Returning original queries for the rest."
        )
        df = df.merge(
            expanded, on=["qid", "qid"], how="left"
        )  # this keeps the original queries that can not be expanded
        print(">>> Examples:")
        for _, q in df[df["terms"].notnull()].head().iterrows():
            print(f"Query: `{q['query']}` expansion terms: `{q['terms']}`")

        df["terms"] = df["terms"].fillna("")
        df["query"] = df.apply(
            lambda x: x["query"] + " " + " ".join(x["terms"]), axis=1
        )
        df = df.drop(columns=["terms"])

        # Clean queries
        tokeniser = pt.java.autoclass(
            "org.terrier.indexing.tokenisation.Tokeniser"
        ).getTokeniser()

        df["query"] = df["query"].apply(lambda i: " ".join(tokeniser.getTokens(i)))

        return df


def process_dataset(ir_dataset, index_directory, output_directory, memory):
    if (output_directory / "run.txt.gz").exists():
        print(f">>> {output_directory} already exists, skipping")
        return

    index = get_index(ir_dataset, index_directory)
    with tracking(export_file_path=output_directory / "retrieval-ir-metadata.yml"):
        bm25 = pt.terrier.Retriever(index, wmodel="BM25")
        if ir_dataset.get_prior_datasets():
            print(">>> Using Relevance Feedback")
            indices_dir = index_directory.parent
            pipeline = RF(ir_dataset, memory=memory, indices_dir=indices_dir) >> bm25
        else:
            print(">>> No prior datasets, returning BM25")
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
    print(f">>> Processing {dataset} with memory {memory}")
    ir_dataset = load(dataset)
    sub_collections = (
        [ir_dataset] if not ir_dataset.get_datasets() else ir_dataset.get_datasets()
    )

    for snapshot in sub_collections:
        print(f">>> Processing {snapshot.get_snapshot()}")
        process_dataset(
            snapshot,
            index / snapshot.get_snapshot(),
            output / snapshot.get_snapshot(),
            memory,
        )

    # The ir-metadata description of your approach
    ir_metadata = Path(__file__).parent / "ir-metadata.yml"

    copy(ir_metadata, output / "ir-metadata.yml")


if __name__ == "__main__":
    main()
