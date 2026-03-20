#!/usr/bin/env python3
"""python3 ./baseline.py --index index --output output --dataset longeval-sci-2026/clef-2026/sci"""


import click
import numpy as np
from openai import OpenAI
from pyterrier_dr import FlexIndex
import pyterrier as pt
import pandas as pd
from pathlib import Path
from shutil import copy
import pandas as pd
from ir_datasets_longeval import load

# We use the tracker to monitor resource consumption etc. of the indexing and retrieval.
# The tracking is optional, i.e., you can remove it or switch to an alternative such as repro_eval.
from tirex_tracker import tracking


class VLLMEncoder(pt.Transformer):
    def __init__(self, model_name, base_url="http://localhost:6543/v1", batch_size=20):
        super().__init__()
        self.client = OpenAI(base_url=base_url, api_key="vllm-token")
        self.model_name = model_name
        self.batch_size = batch_size

    def transform(self, input_df: pd.DataFrame) -> pd.DataFrame:
        # Determine column names and text processing
        is_query = 'query' in input_df.columns
        text_col = 'query' if is_query else 'text'
        output_col = 'query_vec' if is_query else 'doc_vec'

        # Vectorized instruction prep
        texts = input_df[text_col].tolist()
        if is_query:
            texts = [self._get_detailed_instruct(q) for q in texts]

        # Process in batches to prevent API timeouts or OOM on the server
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i: i + self.batch_size]
            all_embeddings.append(self._get_embeddings(batch))

        # Efficient concatenation
        input_df[output_col] = list(np.vstack(all_embeddings))
        return input_df

    def _get_embeddings(self, texts):
        # The OpenAI client handles list inputs natively
        response = self.client.embeddings.create(
            input=texts,
            model=self.model_name
        )
        # Directly extract to float32
        return np.array([d.embedding for d in response.data], dtype='float32')

    def _get_detailed_instruct(self, query: str) -> str:
        task_description = 'Given a web search query, retrieve relevant passages that answer the query'
        return f'Instruct: {task_description}\nQuery:{query}'


def get_index(ir_dataset, index_directory):
    # PyTerrier needs an absolute path
    index_directory = index_directory.resolve().absolute()

    vllm_encoder = VLLMEncoder(model_name="Qwen/Qwen3-Embedding-4B")

    if not index_directory.exists():
        with tracking(export_file_path=index_directory / "index-ir-metadata.yml"):
            # build the index
            index = FlexIndex(index_directory / "my_index.flex")
            indexer = vllm_encoder >> index

            # you can do some custom document processing here
            docs = (
                {"docno": i.doc_id, "text": i.default_text()}
                for i in ir_dataset.docs_iter()
            )
            indexer.index(docs)

    return FlexIndex(index_directory / "my_index.flex")


def process_dataset(ir_dataset, index_directory, output_directory):
    if (output_directory / "run.txt.gz").exists():
        return

    index = get_index(ir_dataset, index_directory)

    with tracking(export_file_path=output_directory / "retrieval-ir-metadata.yml"):
        vllm_encoder = VLLMEncoder(model_name="Qwen/Qwen3-Embedding-4B")

        # potentially do some query processing
        topics = pd.DataFrame(
            [
                {"qid": i.query_id, "query": i.default_text()}
                for i in ir_dataset.queries_iter()
            ]
        )

        retriever = vllm_encoder >> index.retriever()
        run = retriever(topics)
        pt.io.write_results(run, output_directory / "run.txt.gz")
        copy(index_directory / "index-ir-metadata.yml",
             output_directory / "index-ir-metadata.yml")


@click.command()
@click.option("--dataset", type=str, help="The dataset id or a local directory.")
@click.option("--output", type=Path, required=True, help="The output directory.")
@click.option("--index", type=Path, required=True, help="The index directory.")
def main(dataset, output, index):
    ir_dataset = load(dataset)
    sub_collections = [ir_dataset] if not ir_dataset.get_datasets(
    ) else ir_dataset.get_datasets()

    for snapshot in sub_collections:
        process_dataset(snapshot, index / snapshot.get_snapshot(),
                        Path(output) / snapshot.get_snapshot())

    # The ir-metadata description of your approach
    ir_metadata = Path(__file__).parent / "ir-metadata.yml"

    copy(ir_metadata, output / "ir-metadata.yml")


if __name__ == "__main__":
    main()
