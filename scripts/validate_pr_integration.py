"""Verify preview integration preserves immutable input-PR evidence."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "ceb447deb03f5532dc274cb97de2cd7f317349e7"
PR2 = "e5a0291e48d5426628c0dde8a122fe8ab6b6e195"
PR3 = "b2e455fd37d1e236aa30fe246e4944142bef4bab"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    counts = {}
    for ref, folder in [(MAIN, "graphs/final"), (PR2, "experiments/simulator")]:
        files = git("ls-tree", "-r", "--name-only", ref, "--", folder).decode().splitlines()
        for name in files:
            original = git("show", f"{ref}:{name}")
            if original != git("show", f":{name}"):
                raise ValueError(f"원본 증거 바이트 변경: {name}")
            if name.endswith(".csv") and name.startswith("experiments/simulator/") and original != (ROOT / name).read_bytes():
                raise ValueError(f"원시 CSV 작업 사본 바이트 변경: {name}")
        counts[folder] = len(files)
    name = "docs/audit/step6_main_table.csv"
    if git("show", f"{MAIN}:{name}") != (ROOT / name).read_bytes():
        raise ValueError("Step 6 결과표 변경")
    normalize = lambda data: data.decode("utf-8-sig").replace("\r\n", "\n")
    base = normalize(git("show", f"{MAIN}:WORK_LOG.md"))
    current = (ROOT / "WORK_LOG.md").read_text(encoding="utf-8-sig")
    for ref in (PR2, PR3):
        old = normalize(git("show", f"{ref}:WORK_LOG.md"))
        if not old.startswith(base) or old[len(base):].strip() not in current:
            raise ValueError("원본 PR 작업 기록 누락")
    state = json.loads((ROOT / "docs/research_state.json").read_text(encoding="utf-8"))
    expected = {"SIM-01": "BLOCKED", "SIM-02": "PARTIAL", "GRAPH-01": "VERIFIED",
                "GRAPH-GEN": "BLOCKED", "SCM-01": "PARTIAL", "EFFECT-01": "NOT_RUN"}
    states = {x["id"]: x["status"] for x in state["workstreams"]}
    if any(states.get(key) != value for key, value in expected.items()):
        raise ValueError("필수 연구 상태 누락/변경")
    print(json.dumps(dict(status="PASS", main_merged=False, base_main=MAIN, pr2=PR2, pr3=PR3,
                          preserved_file_counts=counts, required_states=expected), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
