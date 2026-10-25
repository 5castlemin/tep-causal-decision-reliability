"""Render measured results into a Korean report; does not choose metrics or models."""
import gzip,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'research_runs/independent_confirmation'
def read(p):return json.loads((p.read_bytes() if p.exists() else gzip.decompress(Path(str(p)+'.gz').read_bytes())).decode('utf-8-sig'))
def number(v):return '비교 불가' if v is None else f'{v:.6f}'
def main():
    run=BASE/'run_v1';out=BASE/'analysis_v1';summary=read(out/'SUMMARY.json');result=read(out/'CONFIRMATION_RESULT.json');plan=read(BASE/'PLAN_v1.json')
    replay=read(BASE/'REPLAY_COMPARISON.json');freeze=read(BASE/'FREEZE.json');diag=read(out/'diagnostics.json');old=read(BASE/'exploratory_diagnostics_v1/diagnostics.json')
    failures=read(run/'failures.json')
    rows=read(run/'comparison.json');primary=[r for r in rows if r['row_status']=='EVALUATED' and r['policy']=='confirmed_only' and '__' not in r['task_id']]
    judgment={'INDEPENDENT_SUPPORT':'독립 확인에서 사전 기준을 충족하는 지지','COUNTER_EVIDENCE':'사전 기준상 반대 증거','INCONCLUSIVE':'차이 불명확','NOT_EVALUABLE':'검증 불가'}[result['judgment']]
    lines=['# 방법론적 불확실성 진단과 독립 확인 실험','',f'2026-10-25. **일차 판정: {judgment}.** 기존 144회 전체 실험은 재실행 비교를 통과했다. 새 규칙으로 생성한 12개 구조에서 '+str(summary['attempts'])+'회 실제 학습을 시도했고 '+str(summary['learned'])+'개 그래프 기록을 생성했으나2개는 SCM 학습이 거부됐다. 제조공정 복구·안전 성능 검증은 수행하지 않았다.','',
    '## 1. 무엇이 불확실했고 어떤 질문을 확인했는가','',
    '연구 질문은 “불완전한 인과그래프에서 어떤 구조적 품질 지표가 실제 개입 추천 성능을 가장 잘 설명하는가?”이다. 기존 PR #13의 8개 수작업 구조에서는 경로 점수가 유망했지만 추천의 경로 부재 대체 규칙, 알고리즘 차이, 지표 중복, 특정 구조·조작 격자에 대한 의존성이 함께 남았다. 이번에는 재현 검사 → 기존 자료 진단 → 계획·예측모형 고정 → 새 구조 학습과 실제 개입 → 독립 확인 순서를 지켰다. 지표와 성능의 예측적 연관을 지표 자체의 인과효과와 구분한다.','',
    '## 2. 기존 144회 실험은 재현됐는가','',
    f'PR #12와 #13은 시작 시 OPEN이었다. PR #13의 a4ae769 위에 feature/independent-causal-confirmation을 만들었으며 자동 병합하지 않았다. 원래 소스·외부 라이브러리 버전·seed·학습 조건·정책을 유지하고 같은 격리 환경의 별도 프로세스와 출력 디렉터리에서 전체 학습·추천·독립 개입·구조 통째 제외 분석을 다시 실행했다. 새 운영체제 또는 새 설치 환경까지 검증한 것은 아니다.','',
    f"144회 학습 성공, 918추천 평가행과 별도120통제행, 실제 개입 78,336표본을 재실행했다. {replay['checked_records']}개 파일/구조화 기록 비교에서 불일치 {len(replay['mismatches'])}건, 제외 대상이 아닌 핵심 수치의 최대 차이는 {replay['max_numeric_difference']}였다. 간선·미확정 관계·선택 조작은 정확히 비교하고 회귀계수·통계에는 사전 절대/상대 허용오차1e-9를 정했다. 실행 시간과 UTC 등 비의미적 메타데이터는 구분했다. 원시 재실행은 지정 로컬 아카이브에, 비교별 해시·실행 ledger·버전은 이 실험 폴더에 보존했다. 동일 seed의 재실행을 독립 표본으로 더하지 않는다.",'',
    '## 3. 기존 네 가지 불안 요소를 어떻게 검사했는가','',
    '추천 결과를 경로 부재에 따른 기준 조작 대체, 계산된 기준 조작, 계산된 다른 조작, 불확실성 보류로 분리했다. 모든 그래프에는 별도로 고정 조작 do(0.5)와 do(0)의 평균 효과를 예측하게 했으며 최적 조작 선택은 시키지 않았다. 확정 경로가 있는 그래프만의 비교, 알고리즘 내부·구조/과제 내부 비교, 같은 학습 데이터의 알고리즘 쌍, 방향 확정 비율 층과 지표 중복도 기록했다.','',
    '기존 자료에서 고정 조작의 경로 점수–효과 오차 상관은 −0.813707, 경로가 있는 그래프만에서는 −0.455358이었다. 따라서 추천 선택만으로 모든 연관을 설명하지는 못한다. 하지만 경로가 없으면 선형 구조방정식의 예측 효과도0이 되는 구조적 제약과 선택 편향은 남는다. 이것을 독립적인 인과적 효과나 모든 기계적 연결의 해소로 해석하지 않는다. DirectLiNGAM의 기존 경로 점수는 알고리즘 내부에서 상수였으므로 효과 없음이 아니라 비교 불가다.','',
    '기존 구조 통째 제외 검증에서 기본 조건+연결 F1의 MAE는0.147939, 여기에 경로 점수까지 더한 MAE는0.150834로 추가 개선이 없었다. 방향 F1–경로의 상관 약0.901, 방향 F1–정규화 구조 오류량 약−0.978의 기존 중복성도 유지한다. 개별 회귀계수를 독립 설명 효과로 해석하지 않았다. 치명적인 구현 오류는 발견되지 않아 기존 결과를 바꾸지 않고 독립 확인으로 진행했다.','',
    '## 4. 새로운 구조는 어떻게 생성하고 고정했는가','',
    f"계획 SHA-256은 `{freeze['plan_sha256']}`이다. 새 데이터를 만들기 전에 생성 규칙, 계수, 모든 seed·과제·설정·분석 코드·옛 자료로 적합한 예측모형을 함께 고정했다. 6~10개 변수 범위의 규칙에서 실제 채택 구조는 다음과 같다. 숨은 공통 원인·시차·순환은 없으며 독립 Uniform 오차와 선형 가산 식을 사용했다.",'',
    '| 구조 | 구조군 | 변수 | 직접 간선 | 주요 경로 수 | 경로 보존 오류 쌍 |','|---|---|---:|---:|---:|---|']
    from diverse_structure_pilot import all_paths,reference_edges
    for s in plan['structures']:
        t=next(t for t in s['tasks'] if t['task_id']=='path')
        lines.append(f"| {s['structure_id']} | {s['group']} | {len(s['nodes'])} | {len(s['edges'])} | {len(all_paths(reference_edges(s),t['action'],t['target']))} | "+('가능' if 'remove_key_path_retained' in s['controlled_variants'] else '부적합')+' |')
    rejected=sum(not r['accepted'] for r in read(BASE/'generation_acceptance_records.json'))
    lines += ['',f'A군은 희소/긴 경로, B군은 조밀/복수 경로, C군은 부호 혼합과 직접/간접 상쇄 가능성을 갖도록 규칙을 정했다. 모든 구조에 독립 주변 가지 P→Q가 있다. 크기·간선 확률·계수 규칙·생성 seed를 미리 정했고 기존 또는 이미 채택된 구조와 이름만 다른 동형 그래프 및 간선 하나씩 제거하면 동형이 되는 근접 후보를 기각했다. 총 {rejected}개 기각 후보의 seed와 이유를 남겼다. 품질 점수·학습 결과·추천 성능으로 채택하지 않았다.',
    '', '가족별4개 할당과 중복 기각은 구조 표본의 교환가능성을 제한한다. 12개 구조가 제조공정 모집단의 무작위 표본이라는 뜻은 아니다. 완전한 모든 구조 다양성을 검증한 것도 아니다. 각 구조의 직접 간선·계수·식은 PLAN_v1과 run_v1/declared_structures에 있으며 새로운 전체 TEP GT로 승격하지 않는다.','',
    '기존 구조는5~8변수였고 새 구조 중9~10변수 조건은 예측모형에도 범위 밖 외삽이다. 계수·목표·최적 후보 분포도 달라질 수 있으므로 예측모형의 전이 실패와 경로 정보 자체의 무용성을 동일시하지 않는다. 현재 고정한 기본 조건에는 실제 총효과 크기나 목표 난이도의 모든 차이가 들어 있지 않다.','',
    '## 5. 실제 학습과 개입을 얼마나 실행했는가','',
    '처음2개 구조, 이어 나머지10개에서 원본 고정 causalAssembly의 정답 인과구조(GT)·수식·실제 잡음 재구성·해당 조작 식만 대체·나머지 식 보존·새 seed 차이·같은 seed 반복·hook 없는 통제를 검사했다. 전부 통과한 다음에만 학습을 시작했다. 원본 라이브러리는 수정하지 않았다.','',
    f"관측 데이터 {summary['datasets']}개(256/512표본×각3회×12구조), PC-stable·BOSS·DirectLiNGAM {summary['attempts']}회 시도 중 {summary['learned']}개 학습. 기본 양성24과제와 4개 후보/비용 설정, 3정책의 추천 {summary['discovery_rows']}행 중 {summary['discovery_evaluated']}행을 실제 평가했다. 보조 정책이 제한된 그래프는 {summary['auxiliary_blocks']}개다. 인위적 오류는 별도 {summary['controlled_rows']}평가행이다.",'',
    f"실행 실패/적합 거부 기록은 {len(failures)}건이다. C12의 PC-stable 256/512표본 각3번째 반복에서 확정 방향 간선에 순환이 있어 SCM을 적합하지 않았다. 그래프 생성 자체와 SCM 학습 가능 여부를 구분한다. 해당 그래프의 간선을 삭제·정답으로 보정하거나 추천 손실을 임의 대입하지 않았다. 실패 그래프의 모든 추천 시도 행을 보존했고, 아래 성능 분석은 평가 가능한 그래프에 조건부다. 이 선택 편향은 해결되지 않았다. 자세한 순환은 FIT_FAILURE_DETAILS.json에 있다.",'',
    f"추천 전체를 해시로 고정한 뒤 24조작변수-구조 조합의 9후보+독립 기준값, 각3배치×256개로 실제 개입 {summary['do_samples']:,}표본을 생성했다. 같은 조작 결과는 그래프·정책·비용·과제 간 공유한다. 관측·개입의 같은 seed가 행별 같은 잡음이라는 가정은 하지 않는다. 세 알고리즘은 별도 자식 프로세스로 같은 데이터에서 병렬 실행하고 결과 수집 순서는 고정했다.",'',
    'PC-stable은 KCI/alpha0.01, BOSS는 기존 Gaussian BIC 준점수, DirectLiNGAM은 비정규 선형 오차 가정과 표준화 계수 절댓값0.05 조건을 유지했다. 열 순서는 무작위 순열이며 정답 그래프를 학습 worker에 전달하지 않는다. 공통 Ridge 회귀(규제 선형 회귀)는 train-only 표준화와 관측 검증 alpha 선택을 사용하며 실제 개입 결과를 학습·추천에 제공하지 않았다. 정규 잡음 별도 진단은 실행하지 않았다.','',
    '## 6. 새 구조에서 예측력은 어떻게 비교됐는가','',
    'M0는 알고리즘·표본 수·변수 수·예측 그래프 밀도·방향 미확정 비율, M1은 M0+연결 F1, M2는 M0+핵심 경로 복원율, M3는 M0+엄격한 방향 F1이다. M4는 M1+경로의 보조 추가 정보 검사다. 이 절의 Ridge는 구조 지표로 추천 손실을 예측하는 2차 모형이며, 앞 절의 관측 자료 기반 SCM용 Ridge와 다르다. 이 손실 예측모형의 회귀계수·결측 대체·표준화·규제 강도는 모두 기존 S1~S8만으로 고정했다. 새12구조의 실제 추천 손실로 다시 적합하지 않았다. 손실은 음수가 될 수 없지만 무제약 선형 예측은 음수를 낼 수 있으며, 이를 사후에 잘라내거나 모형을 교체하지 않았다. 후보 지표들은 이미 과거 탐색 결과를 본 뒤 선택된 것임을 명시한다. 구조 점수는 이 인공 환경의 평가용 정보이며 현장의 항상 관측 가능한 입력이 아니다.','',
    '일차 결과는 확정 간선 정책·5후보·비용0.2의 과제 크기 정규화 추가 손실이다. 구조 내부의 예측 오차를 평균한 뒤12구조에 동일 가중치를 준 평균절대오차(MAE)를 계산했다. 개별 표본의 제곱오차 평균과 목표 평균의 손실은 구분한다.','',
    '| 고정 예측모형 | 새12구조 macro MAE | 음수 손실 예측 행(진단) |','|---|---:|---:|']
    for m,v in result['macro_mae'].items():lines.append(f'| {m} | {number(v)} | '+str(sum(r['model']==m and r['predicted_loss']<0 for r in result['predictions']))+' |')
    d=result['paired'][0]
    additive=result['paired'][4];baseline=result['paired'][2]
    lines += ['',f"중요한 제한은 **기본 조건만의 M0에 경로를 추가한 개선이 {number(baseline['delta'])}, 구간 [{number(baseline['ci_low'])}, {number(baseline['ci_high'])}]로 불명확**하다는 것이다. **M1에 경로를 추가한 M4의 개선도 {number(additive['delta'])}, 구간 [{number(additive['ci_low'])}, {number(additive['ci_high'])}]로 불명확**했다. M1 자체가 M0보다 수치상 나빴기 때문에 M2가 M1보다 낫다는 결과만으로 알고리즘·기본 정보 및 연결 F1 이후의 안정적인 추가 정보가 입증됐다고 말하지 않는다."]
    lines += ['',f"사전 주요 차이 ΔMAE=MAE(M1)−MAE(M2)는 **{number(d['delta'])}**, 구조 단위10,000회 재표본추출의95% 백분위 구간은 **[{number(d['ci_low'])}, {number(d['ci_high'])}]**였다. M2가 나은 구조 {d['right_better']}개, M1이 나은 구조 {d['left_better']}개, 동률 {d['ties']}개다. 한 구조씩 제외한 차이는 [{number(d['leave_one_structure_out_min'])}, {number(d['leave_one_structure_out_max'])}]다.",'',
    f'일차 판정은 **{judgment}**이다. 실질적 최소 개선0.01은 사전 설계 기준이지 통계적 정답이나 물리 임계값이 아니다. 구간은 같은 구조의 모든 그래프·데이터·과제를 함께 묶어 계산했고 옛8구조에서 적합한 예측모형의 불확실성이나 제조공정 모집단을 포함하지 않는다. p-value는 계산하지 않았다.','',
    '| 구조 | M0 MAE | M1 MAE | M2 MAE | M3 MAE | M1−M2 |','|---|---:|---:|---:|---:|---:|']
    scores={(r['structure_id'],r['model']):r['mae'] for r in result['structure_scores']}
    for sid in sorted({r['structure_id'] for r in result['structure_scores']}):
        vals=[scores[sid,m] for m in ['M0','M1','M2','M3']];lines.append('| '+sid+' | '+' | '.join(number(v) for v in vals+[vals[1]-vals[2]])+' |')
    lines += ['', '## 7. 알고리즘과 추천 정책 영향을 분리했는가','',
    '일차 비교는 모든 그래프에 확정 간선 정책을 고정했다. 같은 그래프에서 동치류(관측 구조와 양립하는 방향 후보) 최악 손실 최소화와 후보 간 추천 불일치 시 보류를 별도로 적용했다. 원래 그래프 점수는 정책별로 바꾸지 않았다.','',
    '| 보조 정책 | 비교 셀 | 기본보다 개선 | 악화 | 같은 손실 | 조작 변경 |','|---|---:|---:|---:|---:|---:|']
    for r in read(out/'policy_paired_changes.json'):lines.append('| '+r['policy']+' | '+' | '.join(str(r[k]) for k in ['matched','improved','worsened','unchanged','changed_action'])+' |')
    lines += ['', '| 알고리즘 내부 경로 점수–손실 | 상관(기술통계) | 상태 |','|---|---:|---|']
    for r in diag['associations']:
        if r['scope']=='within_algorithm' and r['metric']=='key_path_edge_recall':lines.append(f"| {r['group']} | {number(r['rho'])} | {r['status']} |")
    lines += ['', '모든 알고리즘을 합친 연관, 알고리즘 내부, 같은 데이터의 알고리즘 쌍, 방향 확정 비율 층, 구조/과제 내부 결과를 diagnostics에 각각 보존했다. 알고리즘 내부 지표가 상수인 경우 비교 불가로 표시한다. DirectLiNGAM에 유리한 독립 비정규 선형 설정과 BOSS 점수의 분포 가정 차이는 제거되지 않았다. 상관된 추천 행을 독립 구조 표본으로 세지 않는다.','',
    '## 8. 경로 부재 대체 규칙을 넘어서는가','',
    '| 검사 | 새 구조의 경로 점수–오차/손실 상관 |','|---|---:|']
    for scope,label in [('path_present','확정 경로가 있는 그래프의 추천 손실'),('fixed_action_effect','고정 조작값 효과 오차'),('fixed_action_path_present','경로가 있는 그래프의 고정 조작 효과 오차')]:
        r=next(x for x in diag['associations'] if x['scope']==scope and x['metric']=='key_path_edge_recall' and x['group'] in ['all','confirmed_path_only'])
        lines.append(f"| {label} | {number(r['rho'])} |")
    reasons=Counter(r['recommendation_status'] for r in primary)
    lines += ['', '일차 추천 사유별 건수: '+', '.join(f'{k}={v}' for k,v in reasons.items())+'.', '',
    '고정 조작 검사는 조작 선택 규칙을 제거하지만, 추정 그래프에 경로가 없으면 구조방정식의 평균 효과가0이라는 특성까지 제거하지는 않는다. 경로 존재 조건으로 골라 비교하는 검사에는 선택 편향이 있다. 사유를 통제한 회귀 하나로 이 문제를 해결했다고 하지 않고 아래 경로 보존 오류 대조와 함께 해석한다.','',
    '## 9. 통제 오류 실험은 무엇을 보여주는가','',
    '이 결과는 정답 구조를 규칙에 따라 손상시킨 보조 실험이며 실제 인과발견 알고리즘 결과와 합치지 않는다. 핵심/주변 간선 제거·방향 변경·간선 추가를 사전 변수명 사전순 규칙으로 정하고, 가능하면 두 그래프 모두 경로를 유지하는 오류 쌍을 별도로 만들었다.','',
    '| 오류 쌍 / 과제 | 해당 구조 수 | 평균 손실 차이(핵심−주변) | 고정 조작 오차 차이 | 이론 기준 효과 오차 차이 |','|---|---:|---:|---:|---:|']
    groups=defaultdict(list)
    for r in read(out/'controlled_error_pairs.json'):groups[r['left'],r['task_id']].append(r)
    for (kind,task),items in sorted(groups.items()):
        by=defaultdict(list)
        for r in items:by[r['structure_id']].append(r)
        loss=statistics.mean(statistics.mean(x['loss_difference'] for x in v) for v in by.values());err=statistics.mean(statistics.mean(x['fixed_error_difference'] for x in v) for v in by.values())
        analytic_err=statistics.mean(statistics.mean(x['analytic_fixed_error_difference'] for x in v) for v in by.values())
        lines.append(f'| {kind} / {task} | {len(by)} | {number(loss)} | {number(err)} | {number(analytic_err)} |')
    na=read(out/'controlled_not_applicable.json')
    lines += ['', f'경로 보존 대조 부적합 등 선택 기록 {len(na)}건은 별도로 남겼다. 적용 불가를 조용히 삭제하거나 알고리즘 실패로 세지 않는다. 위 차이는 이 제한된 오류 위치 실험에 관한 것이며 F1을 높이는 일반적 인과효과가 아니다. 직접 과제와 경로 과제를 분리해 조작 이후와 무관한 상류 오류의 대조 역할도 확인한다.','',
    '## 10. 후보 간격·비용·유한 표본에 민감한가','',
    '| 설정 | M1 MAE | M2 MAE | ΔMAE | 일차와 같은 조작 셀 |','|---|---:|---:|---:|---:|']
    for s in read(out/'sensitivity.json'):lines.append(f"| {s['setting']} | {number(s['macro_mae']['M1'])} | {number(s['macro_mae']['M2'])} | {number(s['delta']['delta'])} | {s['same_action_as_primary']}/{s['rows']} |")
    theory=read(out/'ANALYTIC_OUTCOME_SENSITIVITY.json');td=theory['paired'][0]
    lines += ['', f"사전9후보·비용0.1/0.4 조건은 일차5후보·0.2와 분리한다. 목적함수 자체가 바뀌므로 서로 다른 비용 조건의 원손실을 같은 척도처럼 단순 순위화하지 않는다. 실제 평균을 이론 평균으로 바꾼 보조 결과의 ΔMAE는 {number(td['delta'])}, 구간 [{number(td['ci_low'])}, {number(td['ci_high'])}]였다. {summary['unique_task_settings']}개 고유 구조/과제/설정 중 유한 개입 표본과 이론 평균의 최선 후보가 달랐던 경우는 {summary['unique_task_optimum_diff']}개다. 중복 그래프 행으로 같은 최선 후보를 독립 검증 횟수처럼 부풀리지 않는다.",'',
    '이론 평균은 추천 해시 고정 후 검산·보조 해석에만 사용했다. 원시 잡음으로 실제 표본 수식을 재구성했고 이론 평균이 표본 평균과 정확히 같아야 한다고 요구하지 않았다. 평가 후보의 표본 최소 손실에도 유한 표본의 선택 오차가 있으므로 이론 결과를 별도로 남겼다. 새 결과를 보고 후보나 비용을 고치거나 예측모형을 다시 학습하지 않았다.','',
    '## 11. 이번에 해결한 것과 남은 것','',
    '해결한 실행 문제는 기존144회 전체 재현 여부, 새 구조에서 같은 수식의 GT·관측·do 연결, 사전 고정한 예측모형의 외부 구조 적용, 실제 정책·고정 조작·경로 보존 오류·격자/비용 대조의 수행이다. 이는 연구 가설이 참이라는 뜻과 다르다.','',
    '여전히 남는 문제는 구조군 할당과 중복 기각에 따른 표본 선택, 12구조의 정밀도, 지표 중복, 알고리즘 가정 차이, CPDAG 방향 미확정과 식별, 추천기의 그래프 경로 제약, 조건부 비교의 선택 편향, 옛8구조에 고정한 예측모형의 불확실성이다. 선형·완전 관측·독립 비정규·시간 없는 환경의 결론을 제조공정에 일반화하지 않는다. 이번에는 새216학습 전체의 두 번째 재실행, 정규 잡음 진단, 비선형/시차/잠재변수 확장, 제조 Recovery/Safety를 실행하지 않았다.','',
    '## 12. 연구 가설의 현재 판단과 다음 단계','',
    f'현재 일차 판단은 **{judgment}**이다. 그러나 **종합적으로는 경로 정보의 유용성을 시사하는 결과가 있지만, 알고리즘·전체 연결 F1 이후의 안정적인 추가 정보와 지표 우월성은 아직 불명확하다.** 이론 평균과 고비용 조건에서 주 비교의 실질적 개선 기준이 유지되지 않았고, M0 및 M1 이후의 추가 정보 구간도0을 포함했다. 순환 그래프와 양립 방향 후보가 없는 출력에 대한 선택 편향도 남았다. 특정 지표가 가장 우수하다거나 지표를 인위적으로 높이면 성능이 개선된다는 결론은 내리지 않는다.','',
    '다음은 (1) 이번에 고정한 결과를 바꾸지 않고 구조군별 차이·불확실성을 바탕으로 후속 확인의 정밀도와 표본 계약을 먼저 설계하고, (2) 알고리즘·미확정 표현·효과 크기와 경로 점수의 중복을 분리하는 후속 대조를 고정하며, (3) 제조공정으로 돌아가기 전 동일 생성환경의 참조 구조·제어기·개입 의미·독립 평가 계약을 확보하는 것이다. 제조 환경 변경과 PR 병합은 자동 수행하지 않는다.','',
    '## 근거와 재현 범위','',
    '- `research_runs/independent_confirmation/REPLAY_COMPARISON.json`: 실제144회 재실행의 파일별 비교·해시·허용오차.',
    '- `DIAGNOSTIC_GATE.json`, `exploratory_diagnostics_v1/`: 새 데이터 이전의 진단과 고정 예측모형.',
    '- `PLAN_v1.json`, `FREEZE.json`, `generation_acceptance_records.json`: 수식·seed·후보 기각·사전 분석 규칙.',
    '- `run_v1/`: 원시 관측/잡음/학습 그래프/적합/고정 추천/실제 do와 시간 ledger. gzip은 원본 바이트를 복원하는 무손실 저장이다.',
    '- `analysis_v1/`: 구조별 예측 오차, 구조 bootstrap, 알고리즘/정책/고정 조작/통제 오류/민감도와 이론 검산.',
    '- `scripts/validate_independent_confirmation.py`: 저장된 증거 검사이며216회 외부 학습 재실행과 다르다.',
    '- 외부 causalAssembly commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`, 모듈 SHA `c1f1b7f6b62c8916ebd23cb0002cdad1e9fcfb995b81cfae9558271987c4290e`; 기존 고정 source를 수정하지 않았다.','']
    destination=ROOT/'docs/research_design/INDEPENDENT_CONFIRMATION_REPORT.md';destination.write_text('\n'.join(lines),encoding='utf-8');print(destination.name)
if __name__=='__main__':
    import sys
    sys.path.insert(0,str(ROOT/'src'))
    main()
