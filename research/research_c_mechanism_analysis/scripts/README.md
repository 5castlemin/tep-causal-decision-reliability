# Mechanism analysis utilities

These scripts read and summarize the committed mechanism-analysis tables or perform read-only checks against an explicitly supplied Research C source ledger. They are not an execution interface for generating Research C cohorts.

The historical `regenerate.py` entry point was removed from the active tree because it bypassed the approved runner validation boundary and could be mistaken for an authorized experiment path. Its commit and attribution remain in Git history. Do not restore or invoke it for routine analysis.

The original-ledger audit used read-only SQLite inputs outside this public repository. Raw ledgers are intentionally not distributed here.
