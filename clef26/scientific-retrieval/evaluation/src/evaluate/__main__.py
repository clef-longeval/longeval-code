from pathlib import Path

import click
import pandas as pd

from evaluate.core import do_evaluate


@click.command()
@click.option(
    "--qrels-set",
    type=click.Choice(["dctr", "raw", "llama3-1-8b", "gpt-oss-20b", "gpt-oss-120b", "qwen3-32b"]),
    required=True,
    help="name of the qrels set to be used for the evaluation.",
)
@click.option(
    "--runs",
    type=str,
    default="data/task-1-submissions/outputs-flat",
    help="Path to the flattend run files",
)
@click.option("--output", type=str, required=True, help="The output directory.")
@click.option("--pivot-dir", type=str, required=True, help="Path to the pivot system.")
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing results file instead of appending.",
)
def main(qrels_set, runs, output, pivot_dir, overwrite):
    results = []
    for run_dir in Path(runs).glob("*"):
        run_id = run_dir.stem
        results.extend(do_evaluate(run_dir, qrels_set, run_id, Path(pivot_dir)))

    output_path = Path(output) / "results.csv"
    df = pd.DataFrame(results)
    if output_path.exists() and not overwrite:
        df.to_csv(output_path, mode="a", header=False, index=False)
    else:
        df.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
