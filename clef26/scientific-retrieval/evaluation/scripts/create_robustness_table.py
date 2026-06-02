from pathlib import Path

import click
import pandas as pd


@click.command()
@click.option(
    "--input", "input_path", type=str, required=True, help="Path to results.csv"
)
@click.option("--output", type=str, required=True, help="Output directory")
@click.option("--qrels-set", type=str, multiple=True, help="Qrels set to include")
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
    "--snapshot",
    multiple=True,
    required=True,
    help="Snapshot to include in the table",
)
def main(input_path, output, qrels_set, measures, meta_measures, snapshot):
    df = pd.read_csv(input_path)
    # Perform any necessary data processing or analysis here
    df = df[
        (df["measure"].isin(measures))
        & (df["query"] == "all")
        & (df["qrels_set"].isin(qrels_set))
        & (df["meta_measure"].isin(meta_measures))
        & (df["snapshot"].isin(snapshot))
    ]
    pivot = df.pivot_table(
        index="run",
        columns=["qrels_set", "snapshot", "meta_measure", "measure"],
        values="value",
    ).reset_index()

    sort_cols = [
        col for col in pivot.columns 
        if col[1] == "snapshot-3" and col[2] == "RC"
    ]
    if sort_cols:
        pivot = pivot.sort_values(by=sort_cols[0], ascending=False)
    else:
        print("Warning: 'snapshot-3' and 'RC' column not found for sorting.")

    pivot.to_latex(
        Path(output) / "t1-robustness.tex",
        index=False,
        float_format="%.3f",
        column_format="lcccccc",
        multicolumn_format="c",
        caption="Robustness of retrieval approaches compared to the first snapshot, based on nDCG@10 and the DCTR qrels set.",
        label="tab:t1-robustness",
        position="t",
    )
    
    print(pivot.to_string(index=False))
    

if __name__ == "__main__":
    main(
        args=[
            "--input",
            "data/task-1-evaluation/results.csv",
            "--output",
            "data",
            "--qrels-set",
            "dctr",
            "--snapshot",
            "snapshot-3",
            "--snapshot",
            "snapshot-2",
            "--measures",
            "nDCG@10",
            "--meta-measures",
            "ARP",
            # "--meta-measures",
            # "AP",
            "--meta-measures",
            "RC",
            "--meta-measures",
            "DRI",
            # "--meta-measures",
            # "ER",
            # "--meta-measures",
            # "t-test",
        ]
    )
