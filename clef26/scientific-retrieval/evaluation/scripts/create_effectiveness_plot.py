from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@click.command()
@click.option(
    "--input", "input_path", type=str, required=True, help="Path to results.csv"
)
@click.option("--output", type=str, required=True, help="Output directory")
@click.option("--qrels-set", type=str, required=True, help="Qrels set to include")
@click.option(
    "--measure", type=str, required=True, help="Measures to include in the table"
)
def main(input_path, output, qrels_set, measure):
    df = pd.read_csv(input_path)
    # Filter results
    df = df[
        (df["measure"] == measure)
        & (df["qrels_set"] == qrels_set)
        & (df["query"] == "all")
        & (df["meta_measure"] == "ARP")
    ]
    pivot = df.pivot_table(
        index="run",
        columns="snapshot",
        values="value",
    )
    pivot = pivot.sort_values(by="snapshot-1", ascending=False)

    # Plot
    fig, ax = plt.subplots(figsize=(7, 7))
    pivot.plot(
        kind="line",
        marker="o",
        linestyle="",
        legend=True,
        ax=ax,
    )
    ax.set_xticks(np.arange(len(pivot.index)))

    ax.legend(title="Snapshot", loc="lower left", framealpha=1)
    ax.set_xticklabels(pivot.index, rotation=90, ha="center")
    ax.set_title(
        # f"Effectiveness by Approach Measured with {qrels_set.upper()} Qrels and {measure}",
        f"Effectiveness by Approach Measured by {measure}",
        # fontsize=18,
        pad=15,
    )
    ax.set_ylabel(measure)
    ax.set_xlabel("")
    ax.set_ylim(0, 0.35)
    ax.grid(True)

    plt.tight_layout()
    output_path = Path(output) / f"t1-plot-effectiveness.pdf"
    plt.savefig(output_path, bbox_inches="tight")


if __name__ == "__main__":
    main(
        args=[
            "--input",
            "data/task-1-evaluation/results.csv",
            "--output",
            "data",
            "--qrels-set",
            "dctr",
            "--measure",
            "nDCG@10",
        ]
    )
