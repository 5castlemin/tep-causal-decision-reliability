# S5 artifact recovery audit

Status: `BLOCKED_UNAVAILABLE_PRIVATE_UNIT_ARTIFACTS`; no broad disk search, download, DRF refit or intervention sampling was performed.

The approved local Research D artifact root contained only `final-reaudit-20261126.json`, SHA-256 `6fa458199ea814a61248a1088bbe5a3b96a586916516c02a1dd6b54c0331292b`. The report records a historical PASS from Research D's earlier audit, not a fresh access to unit-level records.

The public manifest identifies the prior run `rd-external-final-20261125-01`, execution commit `a6d751e3f157fca63a93931d62b9f7a9318c6cb5`, run-lock hash `8cc953098352ae8ff97ffc6618cd5353ee6565a9d8300b3143b0b45d08acdda2`, recommendation raw hash `20453dc69698ce21fb7aa0d32eac242301bc816486540e13ca677a6df63cc738`, fixed training numeric hash `bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39`, and training CSV hash `dfc77931debb528db05defaf8302198048a04337d2d20a95ab51e5b1685a7094`.

| Artifact | Expected source/identity | Availability in approved root |
|---|---|---|
| G0 unit records | final G0 IDs and graph hashes bound by private execution/recommendation manifests | absent |
| Recommendation records | expected external `recommendations.json`; raw SHA `20453dc69698ce21fb7aa0d32eac242301bc816486540e13ca677a6df63cc738` | absent |
| Fixed training frame | contract-relative `research-d-semisen-reproduction-02/training.csv`; numeric SHA `bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39`; CSV SHA `dfc77931debb528db05defaf8302198048a04337d2d20a95ab51e5b1685a7094` | absent |
| DRF/DGP native objects | evaluator-only fitted generator; fit diagnostic SHA `11f3a13511bfcf405c8ab167aced154a01fd068711a1fee06fca89e6362856f1` (not a native object hash or full DGP identity proof) | absent |
| Response vectors | expected under `response_vectors/`; exact filenames are only in the unavailable evaluation manifest. Action hashes: `0.000155911358968`=`b3e70ae4e429799b2effe8c3b3640d9bfb5db47e9fc5bca8f8fa1ccd90075244`; `0.0001724093665238`=`276f7cc293679ae81efe318751d83a0d014ccb5de8697a061a31352f04c3ce32`; `0.00018679686613765`=`e632bfa01ad4309e43de62780ee379d10df11551cae9c3c5db0d0fa73dfceb2b`; `0.00020263502221978`=`20240cd94d29f6e02008c4f2b653de18c454a97369c7471e4e38acda38fb319c`; `0.00022589388613683002`=`4215f00f68ca66ec9f1d7ee27ac482785c75a19113d04cfc9df1d260928ba8665` | absent |
| Execution lock | expected external `final_run_lock.json`; SHA above | absent |
| Private artifact manifest | expected external `evaluation_manifest.json`; SHA `136c5d97bfad66ecf3e95f0afd1023d730df33841ab6997f6ec18c4b0f50291f` | absent |

These expected hashes are provenance references, not verification of currently accessible bytes. The prior report’s actual audit remains historical evidence. Restoring byte-identical private files could enable read-only replay. Any new Station1 refit or sampling would be a new reconstruction and needs a separate contract and approval; it is not an exact reproduction by default.
