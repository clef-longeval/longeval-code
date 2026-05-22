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
    "--snapshot",
    type=str,
    required=True,
    help="Snapshot to include in the table",
)
def main(input_path, output, measures, meta_measures, snapshot):
    df = pd.read_csv(input_path)
    # Perform any necessary data processing or analysis here
    df = df[
        (df["measure"].isin(measures))
        & (df["query"] == "all")
        & (df["meta_measure"].isin(meta_measures))
        & (df["snapshot"] == snapshot)
    ]
    pivot = df.pivot_table(
        index="run",
        columns=["qrels_set", "meta_measure", "measure"],
        values="value",
    ).reset_index()

    print(pivot.to_string(index=False))
    output_path = Path(output) / "result_table.csv"
    # pivot.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main(
        args=[
            "--input",
            "data/results.csv",
            "--output",
            "data",
            "--snapshot",
            "snapshot-3",
            "--measures",
            "nDCG@10",
            "--meta-measures",
            "ARP",
            "--meta-measures",
            "AP",
            "--meta-measures",
            "RC",
            "--meta-measures",
            "DRI",
            "--meta-measures",
            "ER",
            "--meta-measures",
            "t-test",
        ]
    )
