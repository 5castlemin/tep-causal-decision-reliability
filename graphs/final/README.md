# TEP Final Graphs v1 — 동결된 최종 그래프 7종

목적: 전체 그래프 평가(evaluator)와 핵심 경로 Task 평가가 **동일한 Final graph**를 보도록 원본을 공유한다. 알고리즘 재실행 없음.

- 출처: `FREEZE.json` (프로토콜 NEFF-TS-v1-A1, 동결 2026-10-05T10:30:46 UTC, FREEZE.json SHA-256 = `c519cd160f93d96ddd564eef7e58d616b4d5e177d352f523abbe2d6738f891cf`)
- 모든 파일은 동결 결과의 바이트 복사본이며, `MANIFEST.csv`의 `sha256` = `freeze_sha256` (39개 전부 일치)
- LPCMCI는 후속 동결 대상이라 포함하지 않음

## 1. 공통 규약

| 항목 | 내용 |
|---|---|
| 방향 행렬 | `A_dir[i,j] = 1 ⟺ X_i → X_j` (행 = 부모, 열 = 자식), 31×31, 확정 방향만 |
| 미확정 행렬 | `A_unres` 대칭 31×31. 연결은 있으나 방향 미확정인 쌍 |
| 성질 | 대각 0, `A_dir`에 양방향 쌍 없음, `A_dir`·`A_unres` 지지(support)는 서로소 |
| 변수 순서 | `variables.csv` (X1~X26, X28, X29, X30, X32, X33). X27·X31은 영분산으로 제외. 모든 CSV의 행·열 레이블이 이 순서와 일치함을 검증함 |
| 데이터 척도 | 계수 파일은 z-score 표준화 데이터 기준 |
| 제어 루프 U규칙 | 그래프에는 반영되지 않음 (평가기 쪽 채점 규칙) |

## 2. 파일 (graphs/<algo>/)

| 파일 | 내용 | 해당 알고리즘 |
|---|---|---|
| `A_dir.csv`, `A_unres.csv` | 최종 정적 그래프 (평가에 쓴 그대로) | 7개 전부 |
| `edges.csv` | 간선 목록 (`-->` 확정, `---(unresolved)` 미확정) | 7개 전부 |
| `config.json` | 최종 설정, 간선 수, 선택 규칙 | 7개 전부 |
| `lag_graph.npy` | 원 시차 그래프 (31,31,τmax+1), dtype `<U4` | PCMCI+, VarLiNGAM, DYNOTEARS |
| `lag_graph_edges.csv` | 시차 그래프 간선 목록 (source, target, lag, mark) | 위 3개 |
| `B_rowchild.npy` | DirectLiNGAM 계수, `B[i,j]≠0 ⟺ X_j→X_i` (행 = 자식), 임계값 적용 전 | DirectLiNGAM |
| `W_rowparent.npy` | DAGMA 가중치 (행 = 부모), 최종 그래프 = `|W| ≥ 0.25` | DAGMA |
| `adjacency_matrices_rowchild.npy` | VarLiNGAM (lags+1,31,31), `[τ][i,j]≠0 ⟺ X_j(t−τ)→X_i(t)` (행 = 자식), 임계값 0 | VarLiNGAM |
| `W0_rowparent.npy`, `WL_rowparent.npy` | DYNOTEARS 동시점 (31,31)·시차 (p,31,31) 가중치 (행 = 부모), 최종 그래프 = `|w| > 0.05` | DYNOTEARS |

## 3. 시차 그래프 표기 (tigramite 규약)

`lag_graph[i, j, τ] = '-->'` ⟺ X_i(t−τ) → X_j(t). τ=0은 대칭 표기(`[i,j,0]='-->'`이면 `[j,i,0]='<--'`). 그 밖의 표기 `o-o`, `x-x`, `o->`, `<-o`, `<->`는 방향 미정·충돌·잠재교란. 빈 문자열은 연결 없음.

## 4. 시차 → 정적 엄격 변환 규칙 (`conversion/lagconv.py`, mode="strict")

1. τ ≥ 1의 `-->`는 X_i → X_j (시간 순서가 방향을 정함)
2. τ = 0은 알고리즘이 정한 방향을 따름
3. 모든 시차를 OR로 결합, 자기 자신으로 가는 시차 연결은 제외
4. 결합 후 i→j와 j→i가 모두 있으면 방향 충돌 → 미확정
5. `o-o`, `x-x`, `o->`, `<-o`, `<->` 표기(τ 무관)는 미확정 표기
6. **엄격(주 분석):** 한 쌍에 미확정 표기가 하나라도 있으면, 확정 방향 표기가 함께 있어도 그 쌍은 미확정

시계열 3개 모두 `lag_to_static(lag_graph, "strict")` 결과가 동결된 `A_dir`/`A_unres`와 정확히 일치함을 확인함 (`summary.csv`의 `lag_to_static_strict_reproduces`).

## 5. Task 연결 시 주의

1. **시계열 3개의 정적 `A_dir`에는 방향 순환이 있음** (`summary.csv`의 `dir_acyclic = False`). 여러 시차를 하나로 합치면서 생긴 순환이다. 조정 집합·do-연산 등 DAG를 가정하는 Task는 (a) 시간 전개 그래프(`lag_graph.npy`, 비순환)를 쓰거나 (b) 순환 처리 규칙을 사전에 정해야 한다. 어느 쪽이든 GT 열람과 무관하게 정하고 기록할 것.
2. **미확정 쌍**은 "연결 있음, 방향 모름"이다. Task에서 미확정 쌍을 어떻게 다룰지(무시 / 양방향 / 모든 방향 조합 평균 등)도 사전에 정해야 한다. 전체 그래프 평가는 미확정을 방향 오답으로 채점했다.
3. **PC-stable은 22쌍 중 13쌍이 미확정**이라, 방향이 필요한 Task에서는 정보가 매우 적다.
4. PCMCI+ Final은 Track A 설정(τmax=3, pc_alpha=0.01)을 재실행한 결과 (원 파일 유실). 로컬 Mac에서도 동일 그래프 재현을 확인함.

## 6. 검증과 로딩

```bash
python verify_and_load.py          # 해시·변수 순서·시차 재변환 검증
```
```python
from verify_and_load import load_graphs
G = load_graphs()                  # {"pc": {"A_dir": ndarray, "A_unres": ndarray, "lag_graph": ndarray|None, "config": dict}, ...}
```
필요 패키지: numpy, pandas, networkx(시차 재변환 검증 시).

포함하지 않은 것: Initial 그래프, 관대 변환본, 민감도 그래프, 탐색 후보 그래프. 필요하면 같은 형식으로 추가 제공 가능.
