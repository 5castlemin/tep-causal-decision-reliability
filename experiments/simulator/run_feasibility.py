"""Real external simulator smoke; no SCM, tuning or recovery scoring."""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np

COMMIT = "9a6c8e5fcef4a2850778704e7793c87b0a187005"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    revision = subprocess.check_output(["git", "-C", str(a.source), "rev-parse", "HEAD"], text=True).strip()
    if revision != COMMIT:
        raise ValueError("소스 commit 불일치")
    if a.output.exists():
        raise FileExistsError("결과 폴더를 덮어쓰지 않습니다")
    a.output.mkdir(parents=True)
    plan = dict(source_url="https://github.com/jkitchin/tennessee-eastman-profbraatz", commit=COMMIT,
                seed=42, seconds=1800, dt_seconds=1, record_seconds=30,
                intervention=dict(mv=10, delta_percentage_points=1.0, start_second=600),
                fault=dict(idv=4, start_second=600), purpose="실행 가능성 smoke. 복구·안전 성능 평가 아님")
    (a.output / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.path.insert(0, str(a.source / "src"))
    from tep import TEPSimulator, ControlMode
    from tep.constants import MEASUREMENT_NAMES, MEASUREMENT_UNITS, MANIPULATED_VAR_NAMES
    arrays, checks = {}, {}
    for name in ["closed_normal_1", "closed_normal_2", "manual_reference", "manual_intervention", "closed_fault"]:
        mode = ControlMode.MANUAL if name.startswith("manual") else ControlMode.CLOSED_LOOP
        sim = TEPSimulator(random_seed=42, control_mode=mode, backend="python")
        sim.initialize()
        initial_observation = sim.get_measurements().copy()
        base = float(sim.get_manipulated_vars()[9])
        command = base + 1.0
        if not 0 <= command <= 100:
            raise ValueError("문서상 MV 범위 초과")
        rows = []
        for second in range(1801):
            if second == 600:
                if name == "manual_intervention":
                    sim.set_mv(10, command)
                if name == "closed_fault":
                    sim.set_disturbance(4, 1)
            if second % 30 == 0:
                rows.append(np.r_[sim.time, sim.get_measurements(), sim.get_manipulated_vars()])
            if second == 1800 or not sim.step():
                break
        data = np.asarray(rows)
        arrays[name] = data
        np.savetxt(a.output / (name + ".csv"), data, delimiter=",", header="time_hours," + ",".join([f"XMEAS{i}" for i in range(1,42)] + [f"XMV{i}" for i in range(1,13)]), comments="")
        checks[name] = dict(record_count=len(data), reached_seconds=float(sim.time * 3600),
                            shutdown=bool(sim.is_shutdown()), finite=bool(np.isfinite(data).all()),
                            initial_mv10=base, final_mv10=float(sim.get_manipulated_vars()[9]))
        checks[name]["terminal_measurements"] = sim.get_measurements().tolist()
        if name == "closed_fault":
            checks[name]["idv4_active_before_clear"] = int(sim.process._idv[3])
            sim.clear_disturbances()
            sim.initialize()
            checks[name]["reset_time_hours"] = float(sim.time)
            checks[name]["disturbances_zero_after_reset"] = bool(np.all(sim.process._idv == 0))
            checks[name]["initial_observation_restored"] = bool(np.array_equal(initial_observation, sim.get_measurements()))
        print(name, checks[name], flush=True)
    common = min(len(arrays["manual_intervention"]), len(arrays["manual_reference"]))
    if not np.allclose(arrays["manual_intervention"][:common,0], arrays["manual_reference"][:common,0]):
        raise ValueError("비교 시점 불일치")
    delta = arrays["manual_intervention"][:common,9] - arrays["manual_reference"][:common,9]
    result = dict(runs=checks, repeat_exact=bool(np.array_equal(arrays["closed_normal_1"], arrays["closed_normal_2"])),
                  last_common_reactor_temperature_difference_degC=float(delta[-1]),
                  last_common_seconds=float(arrays["manual_reference"][common-1,0] * 3600),
                  python=platform.python_version(), numpy=np.__version__,
                  compatibility="VARIABLE_MAPPING_ONLY_NOT_EFFECT_ORACLE")
    (a.output / "variable_schema.json").write_text(json.dumps(dict(measurements=MEASUREMENT_NAMES, units=MEASUREMENT_UNITS, manipulated=MANIPULATED_VAR_NAMES), indent=2), encoding="utf-8")
    result["csv_sha256"] = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in a.output.glob("*.csv")}
    (a.output / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
