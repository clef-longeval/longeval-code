from pathlib import Path

import click
import pandas as pd


@click.command()
@click.option(
    "--input", "input_path", type=str, required=True, help="Path to results.csv"
)
@click.option("--output", type=str, required=True, help="Output directory")
@click.option(
    "--measures", multiple=True, required=True, help="Measures to include in the table"
)
@click.option(
    "--meta-measures",
    multiple=True,
    required=False,
    help="Meta-measures to include in the table",
)
@click.option(
    "--qrels-sets",
    multiple=True,
    required=False,
    help="Qrels sets to include in the table",
)
def main(input_path, output, measures, meta_measures, qrels_sets=["dctr"]):
    df = pd.read_csv(input_path)
    df = df[
        (df["measure"].isin(measures))
        & (df["query"] == "all")
        & (df["qrels_set"].isin(qrels_sets))
        & (df["meta_measure"].isin(meta_measures))
    ]
    pivot = df.pivot_table(
        index="run",
        columns=["qrels_set", "meta_measure", "measure", "snapshot"],
        values="value",
    )

    sort_cols = [col for col in pivot.columns if col[-1] == "snapshot-3"]

    if sort_cols:
        pivot = pivot.sort_values(by=sort_cols[0], ascending=False)
    else:
        print("Warning: 'snapshot-3' column not found for sorting.")

    pivot = pivot.reset_index()

    pivot.to_latex(
        Path(output) / "t1-effectiveness.tex",
        index=False,
        float_format="%.3f",
        column_format="lcccccc",
        multicolumn_format="c",
        caption="Effectiveness of retrieval approaches across the three test snapshots, measured by nDCG@10 and the DCTR qrels set.",
        label="tab:t1-effectiveness",
        position="h",
    )


if __name__ == "__main__":
    main(
        args=[
            "--input",
            "data/task-1-evaluation/results.csv",
            "--output",
            "data",
            "--measures",
            "nDCG@10",
            "--meta-measures",
            "ARP",
            "--qrels-sets",
            "dctr",
            "--qrels-sets",
            "gpt-oss-120b",
        ]
    )
