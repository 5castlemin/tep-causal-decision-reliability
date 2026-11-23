"""Resource guards for isolated Research C execution units.

The current envelope is TEST_ONLY. RSS is sampled and can overshoot between
polls; storage checks are pre-write checks, not an OS filesystem quota.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import shutil


class ResourceLimitStop(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class ResourceLimits:
    unit_timeout_seconds: float
    scm_active_seconds: float
    cohort_active_seconds: float
    sampled_rss_bytes: int | None
    max_result_bytes: int
    max_ledger_bytes: int
    max_cohort_storage_bytes: int
    minimum_free_disk_bytes: int
    failure_reserve_bytes: int = 4096
    max_concurrent_scms: int = 1
    classification: str = "TEST_ONLY_RESOURCE_ENVELOPE"

    def __post_init__(self):
        if self.classification not in {"TEST_ONLY_RESOURCE_ENVELOPE",
                                       "USER_APPROVED_RESEARCH_RESOURCE_PROFILE"}:
            raise ValueError("unsupported resource-limit classification")
        if any(v <= 0 for v in (self.unit_timeout_seconds, self.scm_active_seconds,
                                self.cohort_active_seconds, self.max_result_bytes,
                                self.max_ledger_bytes, self.max_cohort_storage_bytes)):
            raise ValueError("time and storage caps must be positive")
        if self.max_ledger_bytes < 64 * 1024 or self.max_cohort_storage_bytes < 64 * 1024:
            raise ValueError("SQLite-backed run caps must allow at least 64 KiB for schema and stop records")
        if self.minimum_free_disk_bytes < 0 or self.failure_reserve_bytes < 0:
            raise ValueError("disk reserves cannot be negative")
        if (self.sampled_rss_bytes is not None and self.sampled_rss_bytes <= 0):
            raise ValueError("sampled RSS cap must be positive or None")
        if self.failure_reserve_bytes >= self.max_cohort_storage_bytes:
            raise ValueError("failure reserve must be smaller than cohort storage cap")
        if self.max_concurrent_scms != 1:
            raise ValueError("this runner serializes SCMs and supports max_concurrent_scms=1 only")

    def binding(self) -> dict:
        return asdict(self)


def directory_usage_bytes(root: Path) -> int:
    root = Path(root)
    return sum(p.stat().st_size for p in root.rglob("*")
               if p.is_file() and not p.is_symlink())


def check_storage(root: Path, *, next_bytes: int, limits: ResourceLimits,
                  emergency: bool = False) -> dict:
    """Check run directory and filesystem before writes; preserve failure reserve."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    used = directory_usage_bytes(root)
    reserve = 0 if emergency else limits.failure_reserve_bytes
    if used + next_bytes + reserve > limits.max_cohort_storage_bytes:
        raise ResourceLimitStop(
            "COHORT_STORAGE_CAP",
            f"used={used}, next={next_bytes}, reserve={reserve}, cap={limits.max_cohort_storage_bytes}")
    free = shutil.disk_usage(root).free
    required = next_bytes + (0 if emergency else limits.minimum_free_disk_bytes)
    if free < required:
        raise ResourceLimitStop("MINIMUM_FREE_DISK",
                                f"free={free}, required={required}")
    return {"directory_bytes": used, "free_disk_bytes": free}


def run_isolated(callable_unit, *, timeout_seconds: float, rss_cap_bytes: int | None):
    """Run one SCM unit in a spawned child; reuse the tested Step 4 monitor.

    Returns (value, stop_code, elapsed_seconds, sampled_peak_rss). The monitor
    terminates then kills and joins a child on timeout/RSS detection.
    """
    from research.budget_aware_refinement.step4b4_mock_runner import _run_isolated
    value, status, elapsed, peak = _run_isolated(callable_unit, timeout_seconds, rss_cap_bytes)
    if status == "TIMEOUT":
        return None, "UNIT_TIMEOUT", elapsed, peak
    if status == "RSS_LIMIT":
        return None, "SAMPLED_RSS_CAP", elapsed, peak
    if status:
        return None, f"CHILD_{status}", elapsed, peak
    return value, None, elapsed, peak
