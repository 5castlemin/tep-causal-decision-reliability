# Specification Gate V2 — 소형 fixture 손계산 감사

모든 그래프는 명시적인 설명 fixture이며 연구 표본·SCM·정책 성능 데이터가 아니다.

## Fixture A — open backdoor와 boundary FP

Task `(X,Y)`, nodes `{X,M,Y,Z,W}`, GT edges:

`X→M, M→Y, Z→X, Z→Y, W→M`.

Predicted graph는 GT에서 FP `W→X` 하나를 추가한다고 둔다. 기존 causal path는 `X→M→Y`. 정답 backdoor `X←Z→Y`는 두 arrow가 Z에서 나가므로 collider가 없는 open fork path다. 새 FP를 넣으면 `X←W→M→Y`도 열린 backdoor가 된다. Z/W는 구분되며 `W→X`는 GT-absent FP고 참 adjacency의 FN/REV/unresolved가 아니다.

- A, zone-internal pair only: `W`를 zone node set 밖으로 두므로 `W→X`를 non-task FP로 분류한다.
- B, boundary route test: inserting `W→X` creates an open backdoor route, so candidate task FP.
- 결과: B는 A에서 놓칠 수 있는 경계 FP를 포착하지만 assignment denominators/population이 바뀐다. 이 fixture는 A/B 중 어느 것이 실제 outcome을 더 잘 예측하는지 보여주지 않는다.

## Fixture B — collider-blocked path

Nodes `{X,M,Y,C,W}`, GT `{X→M,M→Y,Y→C,W→C}`. Add the GT-absent FP `X→C`.

GT의 `X–Y` causal path는 `X→M→Y`. FP 뒤 `X→C←Y`는 C에서 두 화살표가 들어오는 collider path다. conditioning set을 비우고 collider descendant를 condition하지 않으면 이 path는 blocked다. 방향 없는 path 존재만 검사하는 B는 이를 task-relevant open backdoor로 오분류할 수 있다. 반대로 C 또는 descendant를 conditioning하면 d-connection이 바뀔 수 있어 adjustment/conditioning 계약이 필요하다.

## Fixture C — M3 unresolved 회피 반례

GT edges `{A→B,C→D}`; 두 pair 모두 non-task. Estimate 1: `B→A`(reversed), `C→D`(correct).

- Estimate 1: `correct=1, reversed=1`; `M3_acc=1/(1+1)=0.5`; unresolved count=0.
- Estimate 2: replace `B→A` with `A—B` unresolved; `correct=1, reversed=0, unresolved=1`; `M3_acc=1/(1+0)=1.0`, `M3_unresolved=1/(1+0+1)=0.5` under candidate denominator.

Accuracy alone appears to improve from 0.5 to 1.0 though no new direction was correctly learned. Joint reporting makes the trade-off visible. If unresolved is omitted from residual penalty, the estimate can receive a spurious reward.

## Fixture D — pair-event partition exact-once

Use task zone pairs `{X,M,Y}` and a fixed FP assignment. For one graph×task:

| Pair kind | Example | Assignment |
|---|---|---|
| true edge missing | GT `X→M`, estimate absent | M4-FN if zone; otherwise M1 |
| true edge reversed | GT `M→Y`, estimate `Y→M` | M4-REV if zone; otherwise M3 reversed |
| true edge unresolved | GT `X→M`, estimate unresolved | M4-UNRES if zone; otherwise M3 unresolved |
| predicted edge where GT absent | GT absent `{R,S}`, estimate `R→S` | A/B decides exactly one: M4-FP or M2 |
| correct true edge | GT and estimate `M→Y` | no error event |
| both absent | GT absent, estimate absent | no error event |

Every **error event** is placed in one exclusive bucket; a correct edge is not counted as an error. Rate denominators overlap conceptually with correct edges by design but that does not double-count error events. Across multiple tasks, same graph error may appear in task-specific outputs more than once; task rows are repeated measures, not independent sample additions.

## Fixture E — B=1…4 allocation and S15 collapse

GT edges:

`X→A, A→Y, X→B, B→Y, T→U, P→Q`.

Initial estimate:

`A→Y, X→B, B→Y, Q→P, R→S`.

Candidates:

1. add `X→A`: task FN / M4;
2. add `T→U`: off-task FN / M1;
3. delete `R→S`: off-task FP / M2;
4. orient `Q→P` to `P→Q`: off-task REV / M3.

Each correction alone preserves DAG. Base unit costs are all 1. Quota A uses `N_ref=floor(B/1)` edit-count slots, equally allocated across S15 in order M1→M2→M3→M4; actual C≤B remains separately enforced.

| B | S1={M1} | S15 under A | Same final graph? |
|---:|---|---|---|
| 1 | add `T→U` | first remainder goes M1; add `T→U` | Yes; demonstrates S15 can collapse to S1. |
| 2 | add `T→U`, then M1 candidate exhausted | M1 add `T→U`; M2 delete `R→S` | No. |
| 3 | M1-only; then exhausted | add `T→U`, delete `R→S`, orient `Q→P` | No. |
| 4 | M1-only; then exhausted | one slot each; also add `X→A` | No; S15 corrects all four fixture errors. |

This checks quota availability, not empirical metric superiority. It also illustrates why 16 labels do not imply 16 distinct outputs.

## Fixture F — shared cost-greedy B

On the same fixture, for illustration only, suppose predeclared normalized gains for the four edits are M1=.5, M2=.5, M3=1.0, M4=.25; these numbers are assigned pedagogically, not estimated. Under equal-weight utility over selected metrics, shared greedy with stable tie M1 then M2 picks M3 at B=1 (cost 1), versus quota A/S1 picking M1. B=2 can spend M3 and then one of M1/M2; B=3 can spend M3+M1+M2; B=4 can spend all four. Thus greedy and quota can differ at small budget, but no Regret conclusion follows.

With `c_ori=2`, B=1 cannot orient; B=2 can. With `c_ori=3`, B=1/2 cannot orient; B=3 can if at least 3 cost units remain. A may strand its M3 slot; B may choose other affordable operations first and strand the same orientation later. Cost-aware tie order and `ΔU/cost` utility must be frozen before any study.

## Integrity summary

- Fixture A corrects V1’s false FP labeling and uses an actually open backdoor after FP insertion.
- Fixture B distinguishes a path with a collider from an open backdoor under explicit empty conditioning.
- Fixture C shows unresolved can inflate conditional direction accuracy alone.
- Fixture D partitions FN, FP, REV, UNRES and no-error pairs exactly once.
- Fixture E verifies S15=B1 can equal S1; B=2/3/4 can diverge.
- Fixture F compares scheduling rules using only an illustrative normalized gain, not study outcome.
