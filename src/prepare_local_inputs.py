"""기존 원본을 수정하지 않고 검증된 최소 입력을 별도 저장소에 복사한다."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "graph_zip": "b4e684cd5af9d6246505643281494a72cc8758bc121369c9c7ff4ee6dff663f7",
    "step6_zip": "28824bc2a98acb77ce8fc5f56439ea4910f7dc9f22ed45b7d1391f7f703f6b22",
    "dataset": "52ae445b4355201db9591822282381c8de861afe49bdbc9452db08b01e7d3711",
    "gt": "238542dbdde50887b5944fb3acc64a792b19a0c56bbfa06e3b267261f2fe6c43",
}
SOURCE_COMMIT = "72b0f5e3d14192478186ee0dc4338b7448087789"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked(data: bytes, key: str) -> bytes:
    value = sha(data)
    if value != EXPECTED[key]:
        raise ValueError(f"{key} SHA-256 불일치: {value}")
    return data


def git_blob(repo: Path, path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{SOURCE_COMMIT}:{path}"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-git", required=True, type=Path)
    p.add_argument("--graph-zip", required=True, type=Path)
    p.add_argument("--step6-zip", required=True, type=Path)
    p.add_argument("--task-dir", required=True, type=Path)
    p.add_argument("--freeze-dir", required=True, type=Path)
    a = p.parse_args()

    local = ROOT / "data" / "local"
    local.mkdir(parents=True, exist_ok=True)
    dataset = checked(git_blob(a.source_git, "TenneseeEastman/datasetTE.csv"), "dataset")
    gt = checked(git_blob(a.source_git, "TenneseeEastman/TEGroundTruth.txt"), "gt")
    (local / "datasetTE.csv").write_bytes(dataset)
    (local / "TEGroundTruth.txt").write_bytes(gt)

    graphs = ROOT / "graphs" / "final"
    graphs.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.graph_zip) as z:
        checked(a.graph_zip.read_bytes(), "graph_zip")
        prefix = "TEP_final_graphs_v1/"
        for member in z.infolist():
            if member.is_dir() or "__pycache__" in member.filename:
                continue
            if not member.filename.startswith(prefix):
                raise ValueError(f"예상하지 못한 ZIP 경로: {member.filename}")
            rel = Path(member.filename[len(prefix):])
            if ".." in rel.parts or rel.is_absolute():
                raise ValueError(f"위험한 ZIP 경로: {rel}")
            dest = graphs / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(member))

    with zipfile.ZipFile(a.step6_zip) as z:
        checked(a.step6_zip.read_bytes(), "step6_zip")
        out = ROOT / "docs" / "audit" / "step6_main_table.csv"
        out.write_bytes(z.read("results/eval/main_table.csv"))

    task_out = ROOT / "docs" / "tasks"
    task_out.mkdir(parents=True, exist_ok=True)
    for name in ["structural_task_candidates_v1_1.json", "task_selection_freeze_v1_1.json"]:
        shutil.copyfile(a.task_dir / name, task_out / name)
    for name in ["pre_fitting_final_freeze.json", "ridge_policy_final.json", "fitting_row_policy.json"]:
        shutil.copyfile(a.freeze_dir / name, ROOT / "docs" / "audit" / name)

    record = {
        "source_git_commit": SOURCE_COMMIT,
        "graph_zip_sha256": EXPECTED["graph_zip"],
        "step6_zip_sha256": EXPECTED["step6_zip"],
        "dataset_sha256": EXPECTED["dataset"],
        "gt_sha256": EXPECTED["gt"],
        "source_files_modified": False,
    }
    (local / "copy_provenance.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[PASS] 데이터·GT·최종 그래프·결과표 해시 검증 후 별도 저장소에 복사")


if __name__ == "__main__":
    main()
