from pathlib import Path

import click
import pandas as pd
from scipy.stats import kendalltau, pearsonr


def compute_rank_correlations(
    df: pd.DataFrame, qrels_set: str, reference: str = "snapshot-1"
) -> pd.DataFrame:
    agg = df[
        (df["meta_measure"] == "ARP")
        & (df["query"] == "all")
        & (df["qrels_set"] == qrels_set)
    ]

    snapshots = sorted(s for s in agg["snapshot"].unique() if s != reference)
    results = []

    for (qrels_set, measure), group in agg.groupby(["qrels_set", "measure"]):
        pivot = group.pivot_table(index="run", columns="snapshot", values="value")

        if reference not in pivot.columns:
            continue

        for snapshot in snapshots:
            if snapshot not in pivot.columns:
                continue

            valid = pivot[reference].notna() & pivot[snapshot].notna()
            if valid.sum() < 2:
                continue

            base = pivot.loc[valid, reference]
            comp = pivot.loc[valid, snapshot]

            r, r_p = pearsonr(base, comp)
            tau, tau_p = kendalltau(base, comp)

            results.append(
                {
                    "qrels_set": qrels_set,
                    "measure": measure,
                    "snapshot": snapshot,
                    "n_systems": int(valid.sum()),
                    "pearson_r": round(r, 4),
                    "pearson_p": round(r_p, 4),
                    "kendall_tau": round(tau, 4),
                    "kendall_p": round(tau_p, 4),
                }
            )

    return pd.DataFrame(results)


@click.command()
@click.option(
    "--input", "input_path", type=str, required=True, help="Path to results.csv"
)
@click.option("--output", type=str, required=True, help="Output directory")
@click.option(
    "--qrels-set", default="snapshot-1", show_default=True, help="Reference snapshot"
)
@click.option("--reference", required=True, help="Reference snapshot")
def main(input_path, output, qrels_set, reference):
    df = pd.read_csv(input_path)
    correlations = compute_rank_correlations(df, qrels_set, reference=reference)

    print(correlations.to_string(index=False))

    output_path = Path(output) / f"rank_correlations_{qrels_set}.csv"
    correlations.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
    # main(
    #     args=[
    #         "--input",
    #         "data/results.csv",
    #         "--output",
    #         "data",
    #         "--qrels-set",
    #         "raw",
    #         "--reference",
    #         "snapshot-1",
    #     ]
    # )
