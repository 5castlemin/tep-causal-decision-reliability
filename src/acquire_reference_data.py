"""Pinned, checksum-verified acquisition of local CPCaD-Bench TEP inputs.

No network download or mutation of the source repository is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "72b0f5e3d14192478186ee0dc4338b7448087789"
FILES = {
    "datasetTE.csv": "52ae445b4355201db9591822282381c8de861afe49bdbc9452db08b01e7d3711",
    "TEGroundTruth.txt": "238542dbdde50887b5944fb3acc64a792b19a0c56bbfa06e3b267261f2fe6c43",
}


def acquire(source_git: Path, destination: Path) -> None:
    if not (source_git / ".git").exists():
        raise ValueError("CPCaD-Bench Git 저장소 경로가 필요합니다")
    blobs = {}
    for name, expected in FILES.items():
        data = subprocess.run(
            ["git", "-C", str(source_git), "show", f"{COMMIT}:TenneseeEastman/{name}"],
            check=True, capture_output=True,
        ).stdout
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise ValueError(f"{name}: SHA-256 불일치: {actual}")
        blobs[name] = data
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in blobs.items():
        target = destination / name
        if target.exists() and target.read_bytes() != data:
            raise FileExistsError(f"기존 파일을 덮어쓰지 않습니다: {target}")
        if not target.exists():
            target.write_bytes(data)
        print(f"[PASS] {name} SHA-256 검증: {FILES[name]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-git", type=Path, required=True)
    parser.add_argument("--destination", type=Path, default=ROOT / "data" / "local")
    args = parser.parse_args()
    acquire(args.source_git, args.destination)
