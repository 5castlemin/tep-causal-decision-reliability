# 이전 PR 보존 현황

기준 main `cdb2c7d6dc499937929ca496ca840b07fb500701`, 조사 시각 2026-11-10 (Asia/Seoul). 아래는 보존 대상이지 종료 승인 목록이 아니다.

| PR | base ← head | HEAD | 상태 |
|---|---|---|---|
| #36 | `main` ← `feature/budget-aware-causal-refinement` | `ba35db68c573fd35a21edb42b1bbde354bedf0d8` | 열림; 팀 사용 여부 검토 필요 |
| #26 | `main` ← `feature/causalman-causal-contract-resolution` | `43722777a0d65b57f0c41491a0deb3d321ebe4a1` | 열림; 팀 사용 여부 검토 필요 |
| #34 | `feature/tep-original-data-to-causal-intervention` ← `feature/tep-dynamics-alignment-and-intervention-probe` | `1a8bae9d330d54a9c107fc5de09bfd98bcbf653f` | 열림; 팀 사용 여부 검토 필요 |
| #35 | `feature/tep-dynamics-alignment-and-intervention-probe` ← `feature/tep-final-alignment-handoff` | `8a278fe15627361f86988050a8950e14a7d722b6` | 열림; 팀 사용 여부 검토 필요 |
| #31 | `feature/tep-simulator-comprehensive-search` ← `feature/tep-matlab-simulink-local-validation` | `c01e2c3bfc0dde192ed0ab73acff7d260f9e86c7` | 열림; 팀 사용 여부 검토 필요 |
| #32 | `feature/tep-matlab-simulink-local-validation` ← `feature/tep-official-simulator-research-pilot` | `ef4e60f09a20e0e7141b8062ab39d5ab1e4bfea4` | 열림; 팀 사용 여부 검토 필요 |
| #29 | `feature/tep-studio-execution-and-environment-validation` ← `feature/tep-operating-condition-reconstruction` | `0e26cc851c485e9a24f379ebfbef979adc4fc18f` | 열림; 팀 사용 여부 검토 필요 |
| #33 | `feature/tep-official-simulator-research-pilot` ← `feature/tep-original-data-to-causal-intervention` | `51c2c76a55750fb772337f79b51f5fc8ab686ecd` | 열림; 팀 사용 여부 검토 필요 |
| #27 | `main` ← `feature/tep-original-simulator-reconstruction` | `597d6554613a685354ba40dcb9ae896413145fa7` | 열림; 팀 사용 여부 검토 필요 |
| #30 | `feature/tep-operating-condition-reconstruction` ← `feature/tep-simulator-comprehensive-search` | `4098306b05a5e09dc362d4d0571908d427fd9350` | 열림; 팀 사용 여부 검토 필요 |
| #28 | `feature/tep-original-simulator-reconstruction` ← `feature/tep-studio-execution-and-environment-validation` | `e86b4917a957cfbd3cdeb6ed6a3610c5b33b4203` | 열림; 팀 사용 여부 검토 필요 |

PR #1–25는 병합 기록을 유지한다. #26은 CausalMan 계약의 독립 연구이며 #27–35는 TEP 누적 의존 체인이다. #36은 활성 연구다. PR별 원본을 수정하지 않는다.
