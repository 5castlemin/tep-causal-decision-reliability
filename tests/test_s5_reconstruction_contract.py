import json
import subprocess
import sys
from pathlib import Path

from research.within_task_repair_prioritization.s4_reconstruction.analyze_s5_results import loss
from research.within_task_repair_prioritization.s4_reconstruction.run_s5_reconstruction import load_resumed_training, write_g0_checkpoint, load_g0_checkpoint, seed
from research.external_validation.semisynthetic_evaluation.reproducibility import serialize_training_frame
import hashlib
import numpy as np
import pandas as pd
import unittest
import tempfile


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


def test_resume_reuses_exact_locked_training_bytes_and_numeric_values(tmp_path):
    values = np.zeros((512, 2), dtype=np.float64)
    values[0] = [0.1, 0.2]
    values[1] = [1.2345678901234567, -0.0000000000007]
    frame = pd.DataFrame(values, columns=["X", "Y"])
    path = tmp_path / "training.csv"
    raw = serialize_training_frame(frame)
    path.write_bytes(raw)
    numeric = hashlib.sha256(values.tobytes(order="C")).hexdigest()
    recovered = load_resumed_training(path, ["X", "Y"], hashlib.sha256(raw).hexdigest(), numeric)
    assert recovered.to_numpy(dtype=np.float64).tobytes(order="C") == values.tobytes(order="C")
    with unittest.TestCase().assertRaisesRegex(ValueError, "raw hash"):
        load_resumed_training(path, ["X", "Y"], "0" * 64, numeric)


class TestG0Checkpoint(unittest.TestCase):
    def test_round_trip_revalidates_locked_seed_and_graph(self):
        from research.original_objective import policy_engine as pe
        from research.original_objective.g0_candidate import corrupt_graph_candidate
        contract = json.loads((HERE / "s5_reconstruction_contract.json").read_text())
        contract["g0"].update({"count": 1, "id_start": 811001, "namespace": "checkpoint-test"})
        nodes = [f"Station1_mp_{i}" for i in range(6)]
        truth = pe.state([(nodes[0], nodes[1]), (nodes[1], nodes[4]), (nodes[1], nodes[2]), (nodes[2], nodes[3]), (nodes[3], nodes[5])])
        sid = contract["g0"]["id_start"]
        master = seed(contract["g0"]["namespace"], f"g0|{sid}")
        record = corrupt_graph_candidate(truth, nodes=nodes, action="Station1_mp_0", target="Station1_mp_4", master_seed=master, task_id=f"{contract['run_id']}:{sid}", true_corruption_rate=0.15, false_adjacency_rate=0.05)
        helper = __import__("research.within_task_repair_prioritization.s4_reconstruction.run_s5_reconstruction", fromlist=["as_graph"])
        graph = helper.as_graph(record["initial_graph"]["edges"], record["initial_graph"]["unresolved"])
        rows = [{"seed_id": sid, "master_seed": master, "record": record, "graph_hash": pe.graph_hash(graph)}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "g0_checkpoint.json"
            write_g0_checkpoint(path, rows)
            resumed = load_g0_checkpoint(path, truth, nodes, contract)
        self.assertEqual(resumed[0]["graph_hash"], pe.graph_hash(graph))
        self.assertEqual(resumed[0]["graph"], graph)

    def test_rejects_modified_checkpoint_bytes(self):
        from research.original_objective import policy_engine as pe
        contract = json.loads((HERE / "s5_reconstruction_contract.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "g0_checkpoint.json"
            path.write_text('{"schema":"S5_G0_CHECKPOINT_V1","rows":[],"file_sha256":"bad"}')
            with self.assertRaisesRegex(ValueError, "checkpoint schema or file hash"):
                load_g0_checkpoint(path, pe.state([]), [], contract)
