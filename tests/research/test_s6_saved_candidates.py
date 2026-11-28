from research.supplementary_validation.s6.analyze_s6_saved_candidates import pick


def row(kind, m4, t5=0.0, regret=0.0, pair=("A", "B"), op="ADD"):
    return {"error_type": kind, "M4_gain": m4, "T5_gain": t5,
            "regret_gain": regret, "pair": list(pair), "operation": op}


def test_type_rank_uses_highest_available_development_type():
    rows = [row("FP", 8.0), row("REV", 0.2)]
    assert pick(rows, "TYPE", ["REV", "FN", "UNRES", "FP"]) == rows[1]


def test_type_rank_falls_back_to_frozen_m4_when_no_positive_candidate():
    rows = [row("REV", 0.0), row("FP", 0.7)]
    assert pick(rows, "TYPE", ["REV", "FN", "UNRES", "FP"]) == rows[1]


def test_t5_falls_back_to_m4_if_no_positive_t5_gain():
    rows = [row("FN", 0.4), row("REV", 0.9, t5=-0.1)]
    assert pick(rows, "T5", ["REV", "FN", "UNRES", "FP"]) == rows[1]


def test_m4_tie_uses_canonical_pair_then_operation():
    rows = [row("FN", 1.0, pair=("B", "C")), row("REV", 1.0, pair=("A", "C"))]
    assert pick(rows, "M4", []) == rows[1]


def test_ex_post_oracle_includes_noop_as_candidate():
    rows = [row("FN", 2.0, regret=-0.2)]
    assert pick(rows, "ORACLE", []) is None
