"""Aggregate-only retrospective analysis of saved initial M4 edit candidates."""
from __future__ import annotations
import argparse, csv, hashlib, itertools, json
from collections import defaultdict
from pathlib import Path
import numpy as np

T = tuple(f"T{i}" for i in range(1, 7))
TOL = 1e-12
BOOT = 10_000
SEEDS = {"pilot64": 2026112801, "development80": 2026112802, "confirmation160": 2026112803}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def choose(group, metrics):
    score = np.asarray([np.mean([r[f"{m}_gain"] for m in metrics]) for r in group], dtype=float)
    m4 = np.asarray([r["M4_gain"] for r in group], dtype=float)
    positive = np.flatnonzero(score > TOL)
    fallback = not len(positive)
    eligible = positive if len(positive) else np.flatnonzero(m4 > TOL)
    if not len(eligible):
        return None, fallback, score
    priority = score if not fallback else m4
    best = max(priority[eligible])
    tied = [int(i) for i in eligible if best - priority[i] <= TOL]
    if not fallback and tied:
        best_m4 = max(m4[tied])
        tied = [i for i in tied if best_m4 - m4[i] <= TOL]
    # All candidate rows in this analysis are M4 task-zone candidates; pair/operation is the frozen canonical order.
    selected = min(tied, key=lambda i: (tuple(group[i]["pair"]), group[i]["operation"]))
    return selected, fallback, score

def midrank(values):
    order = sorted(range(len(values)), key=lambda i: values[i]); ranks = np.zeros(len(values), dtype=float); i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]: j += 1
        ranks[order[i:j]] = (i + j - 1) / 2 + 1; i = j
    return ranks

def analyze_cohort(label, private):
    candidates = json.loads((private / "candidate_values_private.json").read_text(encoding="utf-8"))
    units_path = private / "inputs_private.json"
    if not units_path.is_file(): units_path = private / "pilot_inputs_private.json"
    unit_n = len(json.loads(units_path.read_text(encoding="utf-8"))) if units_path.is_file() else None
    groups = defaultdict(list)
    for r in candidates: groups[r["scm_id"]].append(r)
    multi = {sid: g for sid, g in groups.items() if len(g) >= 2}
    # Keep the complete 63-subset family; every output row remains exploratory and cohort-specific.
    subsets = [s for n in range(1, 7) for s in itertools.combinations(T, n)]
    detail, summary = [], []
    seed = SEEDS[label]
    for metrics in subsets:
        records = []
        for sid, group in sorted(multi.items()):
            selected, fallback, scores = choose(group, metrics)
            utility = np.asarray([r["regret_gain"] for r in group], dtype=float)
            best = max(0.0, float(utility.max()))  # no-op is an allowed ex-post comparator
            chosen_gain = 0.0 if selected is None else float(utility[selected])
            score_best = float(scores.max())
            top = np.flatnonzero(score_best - scores <= TOL)
            tied_set_contains_best = any(abs(float(utility[i]) - best) <= TOL for i in top)
            strict_selected_best = selected is not None and abs(chosen_gain - best) <= TOL
            random_expected = float(np.mean(np.r_[utility, 0.0]))
            pairs = [(i, j) for i in range(len(group)) for j in range(i + 1, len(group)) if abs(utility[i] - utility[j]) > TOL]
            pair_acc = [1.0 if (scores[i] - scores[j]) * (utility[i] - utility[j]) > TOL else .5 if abs(scores[i] - scores[j]) <= TOL else 0.0 for i, j in pairs]
            sr, ur = midrank(scores), midrank(utility)
            spear = float(np.corrcoef(sr, ur)[0, 1]) if np.std(sr) and np.std(ur) else None
            records.append({"scm_id": sid, "selected_regret_gain": chosen_gain, "random_expected_regret_gain": random_expected,
                "optimality_gap": best - chosen_gain, "strict_selected_best": int(strict_selected_best),
                "top_score_tied_set_contains_best": int(tied_set_contains_best), "fallback_to_m4": int(fallback),
                "selected_any_edit": int(selected is not None), "pairwise_rank_accuracy": float(np.mean(pair_acc)) if pair_acc else None,
                "spearman": spear})
        detail.extend([{"cohort": label, "metric_set": "+".join(metrics), **r} for r in records])
        n = len(records)
        if n:
            rng = np.random.default_rng(seed); ix = rng.integers(0, n, size=(BOOT, n))
            cols = {k: np.asarray([r[k] for r in records if r[k] is not None], dtype=float) for k in ("selected_regret_gain", "random_expected_regret_gain", "optimality_gap", "strict_selected_best", "top_score_tied_set_contains_best", "fallback_to_m4", "selected_any_edit")}
            # Statistics involving a defined SCM-level value use the same clustered units.
            def ci(v): return [float(np.quantile(v[ix].mean(axis=1), .025)), float(np.quantile(v[ix].mean(axis=1), .975))]
            paired = np.asarray([r["selected_regret_gain"] - r["random_expected_regret_gain"] for r in records])
            rank = [r["pairwise_rank_accuracy"] for r in records if r["pairwise_rank_accuracy"] is not None]
            spear = [r["spearman"] for r in records if r["spearman"] is not None]
            summary.append({"cohort":label,"metric_set":"+".join(metrics),"scm_count_total":unit_n,"scm_with_any_candidates":len(groups),
                "scm_with_2plus_candidates":n,"candidate_rows_in_2plus_scms":sum(len(multi[s]) for s in multi),
                "mean_selected_regret_gain":float(np.mean(cols["selected_regret_gain"])),"selected_gain_ci95_low":ci(cols["selected_regret_gain"])[0],"selected_gain_ci95_high":ci(cols["selected_regret_gain"])[1],
                "mean_random_expected_gain":float(np.mean(cols["random_expected_regret_gain"])),"mean_selected_minus_random_gain":float(paired.mean()),"selected_minus_random_ci95_low":ci(paired)[0],"selected_minus_random_ci95_high":ci(paired)[1],
                "mean_expost_optimality_gap":float(np.mean(cols["optimality_gap"])),"optimality_gap_ci95_low":ci(cols["optimality_gap"])[0],"optimality_gap_ci95_high":ci(cols["optimality_gap"])[1],
                "strict_selected_best_rate":float(np.mean(cols["strict_selected_best"])),"tied_score_set_contains_best_rate":float(np.mean(cols["top_score_tied_set_contains_best"])),
                "mean_pairwise_rank_accuracy":float(np.mean(rank)) if rank else None,"mean_within_scm_spearman":float(np.mean(spear)) if spear else None,
                "fallback_rate":float(np.mean(cols["fallback_to_m4"])),"no_edit_rate":1-float(np.mean(cols["selected_any_edit"])),"bootstrap_seed":seed,"bootstrap_replicates":BOOT,
                "source_candidates_sha256":sha(private/"candidate_values_private.json"),"source_inputs_sha256":sha(units_path) if units_path.is_file() else None})
    return summary, detail

def main():
    p=argparse.ArgumentParser(); p.add_argument('--pilot-private',type=Path,required=True); p.add_argument('--development-private',type=Path,required=True); p.add_argument('--confirmation-private',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    if a.output.exists() and any(a.output.iterdir()): raise FileExistsError('refusing to overwrite S4 metric analysis output')
    a.output.mkdir(parents=True,exist_ok=True)
    specs=[('pilot64',a.pilot_private),('development80',a.development_private),('confirmation160',a.confirmation_private)]
    rows=[]; details=[]
    for label,path in specs:
        s,d=analyze_cohort(label,path); rows.extend(s);details.extend(d)
    with (a.output/'metric_subset_candidate_selection.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    # Per-SCM diagnostics stay external; only grouped summaries are intended for publication.
    (a.output/'unit_candidate_selection_private.json').write_text(json.dumps(details,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'cohorts':{x:sum(r['cohort']==x for r in rows)//63 for x,_ in specs},'aggregate_rows':len(rows),'private_unit_rows':len(details),'output':str(a.output)},sort_keys=True))
if __name__=='__main__':main()
