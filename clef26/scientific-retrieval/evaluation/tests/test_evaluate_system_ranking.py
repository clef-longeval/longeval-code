import pandas as pd
import pytest
from evaluate_system_ranking import compute_rank_correlations
from scipy.stats import kendalltau, pearsonr


def make_df(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal long-format results DataFrame for testing."""
    defaults = {
        "team": "team-a",
        "qrels_set": "raw",
        "query": "all",
        "meta_measure": "ARP",
        "measure": "ndcg",
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_basic_correlation():
    """Pearson r and Kendall tau match scipy reference values."""
    scores = {"run1": (0.5, 0.6), "run2": (0.3, 0.2), "run3": (0.1, 0.4)}
    df = make_df(
        [
            {"run": run, "snapshot": "snapshot-1", "value": v1}
            for run, (v1, _) in scores.items()
        ]
        + [
            {"run": run, "snapshot": "snapshot-2", "value": v2}
            for run, (_, v2) in scores.items()
        ]
    )

    result = compute_rank_correlations(df)
    assert len(result) == 1
    row = result.iloc[0]

    base = [v for v, _ in scores.values()]
    comp = [v for _, v in scores.values()]
    expected_r, expected_r_p = pearsonr(base, comp)
    expected_tau, expected_tau_p = kendalltau(base, comp)

    assert row["pearson_r"] == pytest.approx(expected_r, abs=1e-3)
    assert row["pearson_p"] == pytest.approx(expected_r_p, abs=1e-3)
    assert row["kendall_tau"] == pytest.approx(expected_tau, abs=1e-3)
    assert row["kendall_p"] == pytest.approx(expected_tau_p, abs=1e-3)
    assert row["n_systems"] == 3


def test_non_arp_rows_are_ignored():
    """Rows with meta_measure != ARP or query != all must not affect results."""
    df = make_df(
        [
            {"run": "run1", "snapshot": "snapshot-1", "value": 0.5},
            {"run": "run2", "snapshot": "snapshot-1", "value": 0.3},
            {"run": "run1", "snapshot": "snapshot-2", "value": 0.4},
            {"run": "run2", "snapshot": "snapshot-2", "value": 0.6},
            # should be ignored
            {
                "run": "run3",
                "snapshot": "snapshot-1",
                "value": 0.9,
                "meta_measure": "ER",
            },
            {
                "run": "run3",
                "snapshot": "snapshot-2",
                "value": 0.1,
                "meta_measure": "ER",
            },
            {"run": "run4", "snapshot": "snapshot-1", "value": 0.9, "query": "q1"},
            {"run": "run4", "snapshot": "snapshot-2", "value": 0.1, "query": "q1"},
        ]
    )

    result = compute_rank_correlations(df)
    assert result["n_systems"].iloc[0] == 2


def test_run_missing_from_one_snapshot_is_dropped():
    """Runs absent from either snapshot must not be included in the correlation."""
    df = make_df(
        [
            {"run": "run1", "snapshot": "snapshot-1", "value": 0.5},
            {"run": "run2", "snapshot": "snapshot-1", "value": 0.3},
            {"run": "run3", "snapshot": "snapshot-1", "value": 0.1},
            {"run": "run1", "snapshot": "snapshot-2", "value": 0.4},
            {"run": "run2", "snapshot": "snapshot-2", "value": 0.2},
            # run3 missing from snapshot-2
        ]
    )

    result = compute_rank_correlations(df)
    assert result["n_systems"].iloc[0] == 2


def test_fewer_than_two_systems_is_skipped():
    """A (qrels_set, measure) with only one valid system produces no output row."""
    df = make_df(
        [
            {"run": "run1", "snapshot": "snapshot-1", "value": 0.5},
            {"run": "run1", "snapshot": "snapshot-2", "value": 0.4},
        ]
    )

    result = compute_rank_correlations(df)
    assert len(result) == 0


def test_multiple_measures_and_qrels_sets():
    """Each (qrels_set, measure) combination produces a separate output row."""
    base_rows = [
        {"run": "run1", "snapshot": "snapshot-1", "value": 0.5},
        {"run": "run2", "snapshot": "snapshot-1", "value": 0.3},
        {"run": "run1", "snapshot": "snapshot-2", "value": 0.4},
        {"run": "run2", "snapshot": "snapshot-2", "value": 0.6},
    ]
    df = make_df(
        [{**r, "measure": "ndcg", "qrels_set": "raw"} for r in base_rows]
        + [{**r, "measure": "map", "qrels_set": "raw"} for r in base_rows]
        + [{**r, "measure": "ndcg", "qrels_set": "dctr"} for r in base_rows]
    )

    result = compute_rank_correlations(df)
    assert len(result) == 3
    assert set(zip(result["qrels_set"], result["measure"])) == {
        ("raw", "ndcg"),
        ("raw", "map"),
        ("dctr", "ndcg"),
    }
