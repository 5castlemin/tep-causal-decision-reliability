import json
import subprocess
import sys
from pathlib import Path

from research.within_task_repair_prioritization.s4_reconstruction.analyze_s5_results import loss


HERE = Path(__file__).resolve().parents[1] / "research" / "within_task_repair_prioritization" / "s4_reconstruction"


def test_s5_lock_fixes_scope_and_sample_caps():
    contract = json.loads((HERE / "s5_reconstruction_contract.json").read_text())
    assert contract["status"] == "LOCKED_BEFORE_GENERATION"
    assert contract["g0"]["count"] == 200
    assert contract["training"]["rows"] == 512
    assert contract["evaluation"]["rows_per_action"] == 4999
    assert contract["evaluation"]["total_intervention_rows"] == 24995
    assert contract["evaluation"]["total_intervention_rows"] + contract["evaluation"]["smoke_intervention_rows_before_run"] <= contract["evaluation"]["total_intervention_cap_including_smoke"]
    assert contract["primary"]["budget"] == 2


def test_bias_corrected_loss_is_not_clipped_at_zero():
    # Large sample variance makes the finite-sample corrected estimate negative.
    assert loss([-1.0, 1.0], target=0.0, scale=1.0) == -1.0


def test_s5_evaluator_module_import_does_not_load_repair_policy_engine():
    code = "import sys; import research.within_task_repair_prioritization.s4_reconstruction.run_s5_reconstruction; print(any(n.startswith('research.original_objective') for n in sys.modules))"
    result = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    assert result == "False"
