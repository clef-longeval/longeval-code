import yaml
from ir_datasets_longeval import load
from repro_eval.Evaluator import RplEvaluator
from repro_eval.util import arp_scores


def mean_arp(arp_orig, arp_rep):
    """Calculate the arythmetic mean of the averaged retrieval performance for the two snapshots."""
    res = {}
    for measure, score in arp_orig.items():
        res[measure] = (score + arp_rep[measure]) / 2
    return res


def relative_change(arp_orig, arp_rep):
    """Calculate the relative change for the two snapshots."""
    res = {}
    for measure, score in arp_orig.items():
        if score == 0:
            res[measure] = 0
        else:
            res[measure] = (score - arp_rep[measure]) / score
    return res


def read_metadata(metadata_path):
    with open(metadata_path, "r") as f:
        return yaml.safe_load(f)


def results_to_rows(team, run_id, snapshot, qrels_set, query, meta_measure, measure_dict):
    return [
        {
            "team": team,
            "run": run_id,
            "snapshot": snapshot,
            "qrels_set": qrels_set,
            "query": query,
            "meta_measure": meta_measure,
            "measure": measure,
            "value": value,
        }
        for measure, value in measure_dict.items()
    ]


def do_evaluate(run_directory, qrels_set, run_id, pivot_directory, reference="snapshot-1"):
    metadata = read_metadata(run_directory / "ir-metadata.yml")
    team = metadata["actor"]["team"]
    tag = metadata["tag"]

    print("\nTeam: ", team)
    print("Tag: ", tag)

    ir_dataset_reference = load(f"longeval-sci-2026/{reference}/{qrels_set}")

    # runs from t1, repro-eval refers to them as original (ORIG)
    t1_run = run_directory / reference / "run.txt.gz"
    t1_pivot_run = pivot_directory / reference / "run.txt.gz"

    table = []
    for snapshot in ["snapshot-1", "snapshot-2", "snapshot-3"]:
        if snapshot == reference:
            continue

        ir_dataset = load(f"longeval-sci-2026/{snapshot}/{qrels_set}")

        # runs from t2, repro-eval refers to them as replicated (REP)
        t2_run = run_directory / snapshot / "run.txt.gz"
        t2_pivot_run = pivot_directory / snapshot / "run.txt.gz"

        try:
            rpl_eval = RplEvaluator(
                qrels_orig_path=ir_dataset_reference.qrels_path(),
                run_b_orig_path=str(t1_pivot_run),
                run_a_orig_path=str(t1_run),
                run_b_rep_path=str(t2_pivot_run),
                run_a_rep_path=str(t2_run),
                qrels_rpl_path=ir_dataset.qrels_path(),
            )
            rpl_eval.evaluate()

            try:
                arp_orig = arp_scores(rpl_eval.run_a_orig_score)
                arp_rep = arp_scores(rpl_eval.run_a_rep_score)
            except Exception as e:
                print(
                    f">>> Run scores not available for {run_id} in {snapshot} or baseline is unavailable. Skipping..., Error: {e}"
                )
                continue

            for query, scores in rpl_eval.run_a_rep_score.items():
                table.extend(results_to_rows(team, run_id, snapshot, qrels_set, query, "per-query", scores))

            table.extend(results_to_rows(team, run_id, snapshot, qrels_set, "all", "ARP", arp_rep))
            table.extend(results_to_rows(team, run_id, snapshot, qrels_set, "all", "ER", rpl_eval.er()))
            table.extend(results_to_rows(team, run_id, snapshot, qrels_set, "all", "DRI", rpl_eval.dri()))
            table.extend(results_to_rows(team, run_id, snapshot, qrels_set, "all", "t-test", rpl_eval.ttest()["advanced"]))
            table.extend(results_to_rows(team, run_id, snapshot, qrels_set, "all", "AP", mean_arp(arp_orig, arp_rep)))
            table.extend(results_to_rows(team, run_id, snapshot, qrels_set, "all", "RC", relative_change(arp_orig, arp_rep)))


        except Exception as e:
            print(f"Error evaluating {team} - {run_id} - {snapshot}: {e}")

    # save reference snapshot ARP
    for query, scores in rpl_eval.run_a_orig_score.items():
        table.extend(results_to_rows(team, run_id, reference, qrels_set, query, "per-query", scores))
    
    table.extend(results_to_rows(team, run_id, reference, qrels_set, "all", "ARP", arp_orig))
        
        
    return table
