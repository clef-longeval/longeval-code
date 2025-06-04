#!/usr/bin/env python3
import click
import pandas as pd


def results_table(df, measures, sort_by=(), output=None):
    def fix_run_tags(row, run_ids):
        """fix run_ids to include version if there are multiple versions"""
        if row["run_id"] in run_ids:
            return row["run_id"] + " (v" + row["version"] + ")"
        else:
            return row["run_id"]

    columns = ["team", "run_id", "version", "snapshot"] + measures
    table = df[columns]
    columns.remove("version")

    # Remove results where everything except the version is the same
    table = table.drop_duplicates(columns)

    # Fix run_ids and rem,ove version
    run_ids = table[table.duplicated(["run_id", "snapshot"])]["run_id"].unique()
    table["run_id"] = table.apply(lambda row: fix_run_tags(row, run_ids), axis=1)
    table.drop(columns=["version"], inplace=True)

    # Fix team names
    table["team"] = table["team"].str.strip("clef25-")

    # Pivot the table to have snapshots as columns
    table = table.pivot(index=["team", "run_id"], columns="snapshot", values=measures)
    table.columns = table.columns.swaplevel(0, 1)
    table = table.sort_index(axis=1, level=0)  # Optional: sort by snapshot
    table = table.reset_index()

    # Sort
    if sort_by:
        table = table.sort_values(by=sort_by, ascending=False)

    # round
    table = table.round(3)

    if output:
        table.to_latex(
            output,
            caption=f"Evaluation Results for . The results are sorted by the {sort_by[0]} for the {sort_by[1]} snapshot.",
            label="tab:xxx-results",
            column_format="ll" + "c" * (len(table.columns) - 2),
            multicolumn=True,
            multirow=True,
            escape=True,
            index_names=True,
            float_format="%.3f",
            index=False,
        )
    print(table)
    return table


@click.command()
@click.option(
    "--input",
    type=str,
    required=True,
    help="The path to the input table CSV file from make table.py.",
    default="evaluation-results-in-progress/longeval-2025-sci-20250430-test-results.csv",
)
@click.option(
    "--ids",
    type=str,
    required=True,
    help="Path to the valid ID file.",
    default="evaluation-results-in-progress/longeval-2025-sci-20250430-test-results-run-ids.csv",
)
@click.option(
    "--sortby",
    type=(str, str),
    default=("2025-01", "nDCG@10"),
    help="The snapshot and measure to sort the table by.",
)
@click.option(
    "--measures",
    type=(str),
    multiple=True,
    default=("nDCG", "nDCG@10"),
    help="One or more measures to include in the table...",
)
@click.option(
    "--output",
    type=str,
    help="The output directory.",
)
def main(input, ids, sortby, measures, output):
    df = pd.read_csv(input)
    valid_ids = pd.read_csv(ids, header=None)[0].tolist()
    df = df[df["run_id"].isin(valid_ids)]

    assert len(measures) > 0, "At least one measure must be specified."
    assert (
        sortby[1] in measures
    ), f"Sort by measure {sortby[1]} must be in the measures list."
    results_table(df, list(measures), sort_by=sortby, output=output)


if __name__ == "__main__":
    main()

# ./latex_table.py --measures nDCG@10 --measures nDCG@1000 --sortby 2025-01 nDCG@1000

# ./latex_table --input evaluation-results-in-progress/longeval-2025-sci-20250430-test-results.csv --ids evaluation-results-in-progress/longeval-2025-web-20250430-test-results-run-ids.csv --sortby 2025-01 nDCG@10 --measures nDCG nDCG@10 --output ../paper/results-sci.tex

# ./latex_table --input evaluation-results-in-progress/longeval-2025-web-20250430-test-results.csv --ids evaluation-results-in-progress/longeval-2025-web-20250430-test-results-run-ids.csv --sortby 2025-01 nDCG@10 --measures nDCG nDCG@10 --output ../paper/results-web.tex
