#!/usr/bin/env python3
import click
from ir_datasets_longeval import load
from pathlib import Path
import pyterrier as pt
import pandas as pd

tirex tracker load
def get_index(ir_dataset, index_directory):
    # PyTerrier needs an absolute path
    index_directory = index_directory.resolve().absolute()

    if not index_directory.exists() or not (index_directory / "data.properties").exists():
        # build the index
        indexer = pt.IterDictIndexer(str(index_directory), overwrite=True, meta={'docno': 100, 'text': 20480})

        # you can do some custom document processing here
        docs = ({"docno": i.doc_id, "text": i.default_text()} for i in ir_dataset.docs_iter())
        indexer.index(docs)

    return pt.IndexFactory.of(str(index_directory))


def process_dataset(ir_dataset, output_directory):
    if (output_directory / "run.txt.gz").exists():
        return

    if not pt.started():
        pt.init()

    index = get_index(ir_dataset, output_directory / "index")
    bm25 = pt.BatchRetrieve(index, wmodel="BM25")

    # potentially do some query processing
    topics = pd.DataFrame([{'qid': i.query_id, 'query': i.default_text()} for i in ir_dataset.queries_iter()])
    
    # PyTerrier needs to use pre-tokenized queries
    tokeniser = pt.autoclass("org.terrier.indexing.tokenisation.Tokeniser").getTokeniser()

    topics["query"] = topics["query"].apply(lambda i: ' '.join(tokeniser.getTokens(i)))

    run = bm25(topics)
    pt.io.write_results(run, output_directory / "run.txt.gz")


@click.command()
@click.option('--dataset', type=str, help='The dataset id or a local directory.')
@click.option('--output-directory', type=click.Path(), help='The output directory.')
def main(dataset, output_directory):
    ir_dataset = load(dataset)

    if not ir_dataset.get_lags():
        process_dataset(ir_dataset, Path(output_directory))
    else:
        for ds in ir_dataset.get_lags():
            process_dataset(ds, Path(output_directory) / ds.get_lag())

if __name__ == '__main__':
    main()
