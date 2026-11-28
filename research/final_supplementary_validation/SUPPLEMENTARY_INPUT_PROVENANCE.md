# Supplementary input provenance

## Scope

The analysis used the original Research C Development (64 SCM) and Held-out (200 SCM) cohort/proposal SQLite databases in read-only mode. It did not use Research D because the private unit-level response materials were not available in this checkout. No new SCM, G0, observation, intervention response, or expert response was generated. Research E/F outputs were not treated as new cohorts.

The C truth specifications and observational arrays were deterministically reconstructed in memory and admitted only after their full digests matched the original ledger bindings. The analysis reports source SHA-256 values from the execution record:

| Input | SHA-256 |
|---|---|
| C Development cohort DB | `dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716` |
| C Development proposal DB | `1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584` |
| C Held-out cohort DB | `37b3c265ecb65b09a97eda91d29411844c3a3851c9fbff6cfa06445f919a3eba` |
| C Held-out proposal DB | `59f1abcf5661a5b3d0658d0db0f7e6afe601ebd09997035228df0716800538d6` |

SQLite integrity checks returned `ok`; connections used query-only mode. Exact truth and observation digest checks passed for 64 Development and 200 Held-out SCMs. The database files were not modified. See `supplementary_integrity_manifest.json` for public output and source-code hashes; raw unit-level tables remain local and gitignored.

## Research D exclusion

Research D's stored aggregate results remain valid historical outputs, but its local evaluator response vectors and unit-level recommendation material were absent. No D-level supplementary estimate is reported. This is an access limitation, not an inference that the earlier D audit did not occur.
