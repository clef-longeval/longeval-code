import gzip
from pathlib import Path

import pytest
from evaluate.core import mean_arp, relative_change
from repro_eval.Evaluator import RplEvaluator
from repro_eval.util import arp_scores


def _write_run(path: Path, queries: list[str]) -> None:
    lines = []
    for qid in queries:
        for rank, (doc, score) in enumerate(
            zip(["d1", "d2", "d3"], [0.9, 0.8, 0.7]), start=1
        ):
            lines.append(f"{qid} Q0 {doc} {rank} {score:.1f} run\n")
    with gzip.open(path, "wt") as f:
        f.writelines(lines)


def _write_qrels(path: Path, queries: list[str]) -> None:
    lines = []
    for qid in queries:
        lines += [f"{qid} 0 d1 1\n", f"{qid} 0 d2 0\n", f"{qid} 0 d3 1\n"]
    path.write_text("".join(lines))


def _make_rpl_eval(
    tmp_path: Path,
    run_queries: list[str],
    judged_orig: list[str],
    judged_rep: list[str],
) -> RplEvaluator:
    for name in [
        "t1_run.txt.gz",
        "t1_pivot.txt.gz",
        "t2_run.txt.gz",
        "t2_pivot.txt.gz",
    ]:
        _write_run(tmp_path / name, run_queries)
    _write_qrels(tmp_path / "orig.qrels", judged_orig)
    _write_qrels(tmp_path / "rep.qrels", judged_rep)

    rpl_eval = RplEvaluator(
        qrels_orig_path=str(tmp_path / "orig.qrels"),
        run_a_orig_path=str(tmp_path / "t1_run.txt.gz"),
        run_b_orig_path=str(tmp_path / "t1_pivot.txt.gz"),
        run_a_rep_path=str(tmp_path / "t2_run.txt.gz"),
        run_b_rep_path=str(tmp_path / "t2_pivot.txt.gz"),
        qrels_rpl_path=str(tmp_path / "rep.qrels"),
    )
    rpl_eval.evaluate()
    return rpl_eval


# ── tests ─────────────────────────────────────────────────────────────────────


def test_unjudged_queries_excluded_from_per_query_scores(tmp_path):
    """Queries present in the run but absent from qrels must not appear in per-query output."""
    rpl_eval = _make_rpl_eval(
        tmp_path,
        run_queries=["q1", "q2", "q3"],
        judged_orig=["q1", "q2"],
        judged_rep=["q1", "q2"],  # q3 has no qrels in either snapshot
    )

    assert set(rpl_eval.run_a_rep_score.keys()) == {"q1", "q2"}
    assert "q3" not in rpl_eval.run_a_rep_score


def test_each_snapshot_uses_its_own_judged_query_set(tmp_path):
    """arp_orig and arp_rep are averaged over their respective snapshot's judged queries,
    not restricted to the intersection across snapshots."""
    rpl_eval = _make_rpl_eval(
        tmp_path,
        run_queries=["q1", "q2", "q3"],
        judged_orig=["q1", "q2", "q3"],  # 3 queries judged in reference snapshot
        judged_rep=["q1", "q2"],  # only 2 judged in comparison snapshot
    )

    assert len(rpl_eval.run_a_orig_score) == 3
    assert len(rpl_eval.run_a_rep_score) == 2

    arp_orig = arp_scores(rpl_eval.run_a_orig_score)
    arp_rep = arp_scores(rpl_eval.run_a_rep_score)

    result = mean_arp(arp_orig, arp_rep)
    for measure in result:
        expected = (arp_orig[measure] + arp_rep[measure]) / 2
        assert result[measure] == pytest.approx(expected)

    rc = relative_change(arp_orig, arp_rep)
    for measure in rc:
        if arp_orig[measure] != 0:
            expected = (arp_orig[measure] - arp_rep[measure]) / arp_orig[measure]
            assert rc[measure] == pytest.approx(expected)
