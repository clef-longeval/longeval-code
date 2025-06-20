#!/usr/bin/env python3
import click
import pandas as pd
import numpy as np

EXCLUDE = [
    {"run_id": "test-system-maik-1234567", "version": "2025-01"},
    {"run_id": "bm25+reranker", "version": "2025-05-19-15-39-38"},
    {"run_id": "bm25+reranker", "version": "2025-05-21-12-45-30"},
    {"run_id": "bm25+reranker", "version": "2025-05-21-15-04-09"},
    {"run_id": "bm25+reranker", "version": "2025-05-22-15-40-14"},
    {"run_id": "bm25+reranker", "version": "2025-05-22-16-08-06"},
    {"run_id": "bm25+reranker", "version": "2025-05-22-16-11-21"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-08-15"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-08-52"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-09-00"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-09-08"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-09-26"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-09-34"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-09-43"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-09-57"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-10-09"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-10-21"},
    {"run_id": "bm25+reranker", "version": "2025-05-21-12-54-02"},
    {"run_id": "bm25+reranker", "version": "2025-05-22-15-51-48"},
    {"run_id": "bm25+reranker", "version": "2025-05-21-12-45-30"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-08-27"},
    {"run_id": "bm25+reranker", "version": "2025-05-24-18-08-35"},
    {"run_id": "bm25+reranker+weighted", "version": "2025-05-26-14-37-40"},
    {"run_id": "bm25+reranker+weighted", "version": "2025-05-26-14-36-24"},
    {"run_id": "bm25+reranker+weighted", "version": "2025-05-26-14-37-56"},
    {"run_id": "bm25+reranker+weighted", "version": "2025-05-26-14-34-01"},
    {"run_id": "bm25+reranker+weighted", "version": "2025-05-26-14-33-04"},
    # web
    {
        "run_id": "clef25-seupd2425-rise",
        "version": "2025-05-20-15-47-16",
    },
    {
        "run_id": "clef25-seupd2425-rise",
        "version": "2025-05-20-16-20-56",
    },
    {
        "run_id": "clef25-seupd2425-rise",
        "version": "2025-05-20-15-55-39",
    },
    {
        "run_id": "clef25-seupd2425-rise",
        "version": "2025-05-20-15-38-06",
    },
    {
        "run_id": "query_expansion_time_dependence",
        "version": "2025-05-24-22-54-13",
    }
]

TEAMS = {
    "cir-cluster": "\cite{CIRcluster}",
    "cir-jmft": "\cite{CIR}",
    "cir-sauerkraut": "\cite{CIR}",
    "cir-super-team-123": "\cite{CIR}",
    "cir-fair-schaer": "\cite{CIR}",
    "cir-schared-retrieval": "\cite{CIR}",
    "seupd2425-datahunter": "\cite{DataHunter}",
    "seupd2425-racoon": "\cite{RACOON}",
    "seupd2425-basette": "\cite{BASETTE}",
    "seupd2425-rise": "\cite{RISE}",
    "ds-gt": "\cite{DS@GT}",
    "seupd2425-rand": "\cite{RAND}",
    "agh-cracow": "\cite{EAIiIB}",
    "open-web-search": "\cite{OWS}",
    "seupd2425-3ds2a": "\cite{3DS2A}",
    "seupd2425-sard": "\cite{SARD}",
}

def results_table(df, measures, sort_by=(), output=None, snapshots=None, format="latex"):
    def fix_run_tags(row, run_ids):
        """fix run_ids to include version if there are multiple versions"""
        if row["run_id"] in run_ids:
            return row["run_id"] + " (v" + row["version"] + ")"
        else:
            return row["run_id"]

    columns = ["team", "run_id", "version", "snapshot"] + measures
    table = df[columns]
    columns.remove("version")

    # filter out excluded runs
    for exclusion in EXCLUDE:
        table = table[
            ~(
                (table["run_id"] == exclusion["run_id"])
                & (table["version"] == exclusion["version"])
            )
        ]
    
    # filter out snapshots
    if snapshots:
        table = table[table["snapshot"].isin(snapshots)]

    # Remove results where everything except the version is the same
    table = table.drop_duplicates(columns)

    # Fix run_ids and rem,ove version
    run_ids = table[table.duplicated(["run_id", "snapshot"])]["run_id"].unique()
    table["run_id"] = table.apply(lambda row: fix_run_tags(row, run_ids), axis=1)
    table.drop(columns=["version"], inplace=True)

    # Fix team names
    table["team"] = table["team"].str.replace("clef25-", "")
    table["team"] = table["team"].apply(lambda x: TEAMS.get(x, x))
    table["run_id"] = table["run_id"] + " " + table["team"]
    table.drop(columns=["team"], inplace=True)

    # Pivot the table to have snapshots as columns
    table = table.pivot(index=["run_id"], columns="snapshot", values=measures)
    # table.columns = table.columns.swaplevel(0, 1)
    # table = table.sort_index(axis=1, level=0)  # Optional: sort by snapshot
    table = table.reset_index()

    # Sort
    if sort_by:
        table = table.sort_values(by=sort_by, ascending=False)

    # round
    table = table.round(3)

    if output:
        if format == "latex":    
            # Identify which columns are numeric (i.e., measures under each snapshot)
            numeric_cols = table.select_dtypes(include=[np.number]).columns

            # Create a Styler and apply a green gradient per column (higher → darker green)
            styled = table.style.background_gradient(
                subset=numeric_cols, cmap="Greens", axis=0
            ).format({col: f"{{:.{3}f}}" for col in numeric_cols})

            # Export to LaTeX. We still supply the same column_format, label, etc.
            styled.to_latex(
                buf=output,
                label="tab:xxx-results",
                column_format="ll" + "c" * (len(table.columns) - 2),
                multicol_align="c",
                convert_css=True,
            )
        
        elif format == "csv":
            table.to_csv(output, index=False)
        
    print(table)


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
    "--snapshots",
    type=(str),
    multiple=True,
    default=None,
    help="One or more measures to include in the table...",
)
@click.option(
    "--output",
    type=str,
    help="The output directory.",
)
@click.option(
    "--format",
    default="latex",
    type=str,
    help="The output directory.",
)
def main(input, ids, sortby, measures, snapshots, output, format):
    df = pd.read_csv(input)
    # valid_ids = pd.read_csv(ids, header=None)[0].tolist()
    # df = df[df["run_id"].isin(valid_ids)]
    assert len(measures) > 0, "At least one measure must be specified."
    # assert (
    #     sortby[1] in measures
    # ), f"Sort by measure {sortby[1]} must be in the measures list."
    results_table(df, list(measures), sort_by=sortby, snapshots=snapshots, output=output, format=format)


if __name__ == "__main__":
    main()
