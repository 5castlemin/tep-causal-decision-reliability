# S5 artifact recovery audit

Status: `BLOCKED_UNAVAILABLE_PRIVATE_UNIT_ARTIFACTS`; no broad disk search, download, DRF refit or intervention sampling was performed.

The approved root approved local Research D artifact root contained only `final-reaudit-20261126.json`, SHA-256 `6fa458199ea814a61248a1088bbe5a3b96a586916516c02a1dd6b54c0331292b`. The report records a historical PASS from Research D's earlier audit, not a fresh access to unit-level records.

The public manifest identifies the prior run `rd-external-final-20261125-01`, execution commit `a6d751e3f157fca63a93931d62b9f7a9318c6cb5`, run-lock hash `8cc953098352ae8ff97ffc6618cd5353ee6565a9d8300b3143b0b45d08acdda2`, recommendation raw hash `20453dc69698ce21fb7aa0d32eac242301bc816486540e13ca677a6df63cc738`, fixed training numeric hash `bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39`, and training CSV hash `dfc77931debb528db05defaf8302198048a04337d2d20a95ab51e5b1685a7094`.

| Artifact | Expected source/identity | Availability in approved root |
|---|---|---|
| G0 unit records | final G0 IDs and graph hashes bound by private execution/recommendation manifests | absent |
| Recommendation records | run `rd-external-final-20261125-01`; raw SHA above | absent |
| Fixed training frame | numeric and CSV hashes above | absent |
| DRF/DGP native objects | evaluator-only fitted generator; no public artifact hash establishes the object bytes | absent |
| Response vectors | five action vector hashes recorded in prior audit: `b3e70a…`, `276f7c…`, `e632bf…`, `20240c…`, `4215f0…` | absent |
| Execution lock | SHA above | absent |
| Private artifact manifest | prior response manifest SHA `136c5d97bfad66ecf3e95f0afd1023d730df33841ab6997f6ec18c4b0f50291f` | absent |

These expected hashes are provenance references, not verification of currently accessible bytes. The prior report’s actual audit remains historical evidence. Restoring byte-identical private files could enable read-only replay. Any new Station1 refit or sampling would be a new reconstruction and needs a separate contract and approval; it is not an exact reproduction by default.
