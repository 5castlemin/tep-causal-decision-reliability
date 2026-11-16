"""Write the active Step 4 freeze content manifest after source review."""
from __future__ import annotations

import json
from pathlib import Path

from .step4c2_freeze import FREEZE_MANIFEST, REQUIRED_FREEZE_ARTIFACTS, build_manifest


def main() -> None:
    manifest = build_manifest(sorted(REQUIRED_FREEZE_ARTIFACTS))
    FREEZE_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8", newline="\n")
    print(f"wrote {FREEZE_MANIFEST.name}; file count={len(manifest['artifacts'])}; status={manifest['status']}")


if __name__ == "__main__":
    main()
