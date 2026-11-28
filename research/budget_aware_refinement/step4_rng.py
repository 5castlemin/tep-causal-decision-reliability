"""Stable, context-keyed random streams for future Step 4 cohorts.

Different keys map to SHA-256-derived seeds. This is an auditable
domain-separation design; it is not a proof of mathematical independence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json


RNG_PROTOCOL_VERSION = "step4-rng-v1"
COHORTS = ("development", "confirmation")
STREAMS = (
    "topology", "coefficient", "exogenous_noise", "observational_sample",
    "node_relabeling", "task_selection", "error_injection",
    "policy_schedule", "random_baseline", "q_recipe_selection",
)


@dataclass(frozen=True)
class RNGKey:
    protocol_version: str
    cohort: str
    master_seed: int
    scm_id: str
    topology_template: str
    node_count: int
    topology_attempt: int
    stream_name: str
    replicate: int = 0
    substream: str = ""


def derive_seed(key: RNGKey) -> int:
    """Derive a stable 256-bit integer seed from the complete declared key."""
    if key.protocol_version != RNG_PROTOCOL_VERSION:
        raise ValueError("unsupported RNG protocol version")
    if key.cohort not in COHORTS:
        raise ValueError("cohort must be development or confirmation")
    if type(key.master_seed) is not int or key.master_seed < 0:
        raise ValueError("master_seed must be a nonnegative integer")
    if not key.scm_id or not key.topology_template or key.node_count < 1:
        raise ValueError("SCM ID, template and positive node count are required")
    if type(key.topology_attempt) is not int or key.topology_attempt < 0:
        raise ValueError("topology_attempt must be a nonnegative integer")
    if key.stream_name not in STREAMS:
        raise ValueError("unknown stream name")
    if type(key.replicate) is not int or key.replicate < 0:
        raise ValueError("replicate must be a nonnegative integer")
    payload = json.dumps(asdict(key), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True).encode("ascii")
    return int.from_bytes(sha256(payload).digest(), "big")


def derive_streams(*, cohort: str, master_seed: int, scm_id: str,
                   topology_template: str, node_count: int,
                   topology_attempt: int = 0) -> dict[str, int]:
    """Return one context-keyed seed for every declared stream."""
    return {
        name: derive_seed(RNGKey(RNG_PROTOCOL_VERSION, cohort, master_seed, scm_id,
                                 topology_template, node_count, topology_attempt, name))
        for name in STREAMS
    }


def numpy_seed_sequence(key: RNGKey):
    """Build a NumPy SeedSequence lazily, without importing NumPy for audits."""
    import numpy as np
    seed = derive_seed(key)
    words = [(seed >> (32 * i)) & 0xFFFFFFFF for i in range(8)]
    return np.random.SeedSequence(words)
