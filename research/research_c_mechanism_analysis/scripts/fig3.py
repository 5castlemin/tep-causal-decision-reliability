import sys
OUT=sys.argv[1]
W=980; bx=[110,345,580]; bw=[220,220,385]
css="""<style>.t{font:13px system-ui,-apple-system,'Noto Sans KR',sans-serif;fill:#191919}.s{font:12px system-ui,sans-serif;fill:#666}.b{fill:#f5f5f5;stroke:#ccc}.task{fill:#e6f7f2;stroke:#00b894}.off{fill:#fdeee6;stroke:#f47230}.ar{stroke:#999;stroke-width:1.5;fill:none}
@media (prefers-color-scheme:dark){.t{fill:#efefef}.s{fill:#9c9c9c}.b{fill:#262626;stroke:#444}.task{fill:#0f3a31}.off{fill:#4a2616}.bg{fill:#191919}}</style>"""
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 410" width="{W}" height="410">',css,f'<rect class="bg" width="{W}" height="410" fill="#fff"/>',
'<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#999"/></marker></defs>',
'<text class="t" x="16" y="22" font-weight="600">그림 3. B=2 수정 순서 → 추천 행동 → Regret (Held-out 실제 SCM)</text>',
'<rect class="task" x="16" y="34" width="12" height="12" rx="2"/><text class="s" x="34" y="44">task-zone 수정(M4)</text>',
'<rect class="off" x="160" y="34" width="12" height="12" rx="2"/><text class="s" x="178" y="44">off-task 수정(M1–M3)</text>',
'<rect class="b" x="330" y="34" width="12" height="12" rx="2"/><text class="s" x="348" y="44">결과/정지</text>']
def row(y,label,boxes):
    o.append(f'<text class="t" x="16" y="{y+19}">{label}</text>')
    for i,(cls,txt) in enumerate(boxes):
        o.append(f'<rect class="{cls}" x="{bx[i]}" y="{y}" width="{bw[i]}" height="28" rx="4"/><text class="t" x="{bx[i]+bw[i]/2}" y="{y+19}" text-anchor="middle">{txt}</text>')
        if i<2: o.append(f'<path class="ar" d="M{bx[i]+bw[i]+2},{y+14} L{bx[i+1]-3},{y+14}" marker-end="url(#a)"/>')
o.append('<text class="t" x="16" y="80" font-weight="600">사례 A. rep-scm-confirmation-proposal-000053 (chain, 6노드, X=V04 → Y=V00; G0: task FN 2, off-task REV 1)</text>')
o.append('<text class="s" x="16" y="100">S0: 수정 그래프에 X→Y 경로 없음 → k=0, Regret 0.458 (GT 최적 k=+1)</text>')
row(112,"Full Greedy",[("off","① M3 REV V00/V02 (0.125)"),("task","② M4 FN V01/V05 (0.083)"),("b","FN V04/V05 남음 → 경로 없음 → k=0, R=0.458")])
row(156,"M4 단독",[("task","① M4 FN V01/V05 (0.333)"),("task","② M4 FN V04/V05 (0.333)"),("b","X→Y 경로 복원 → k=+1, R=0")])
o.append('<text class="t" x="16" y="234" font-weight="600">사례 B (반례). rep-scm-confirmation-proposal-000076 (chain, 9노드, X=V04 → Y=V02; G0: task FN 1·REV 1, off-task FP 1)</text>')
o.append('<text class="s" x="16" y="254">S0: 경로 없음 → k=0, Regret 0.094 (GT 최적 k=−1)</text>')
row(266,"Full Greedy",[("off","① M2 FP V01/V06 삭제 (0.036)"),("task","② M4 REV V00/V04 (0.031)"),("b","방향 수정으로 경로 생김 → k=−1, R=0")])
row(310,"M4 단독",[("task","① M4 FN V02/V03 (0.100)"),("b","② REV 수정 시 순환 → 거부"),("b","경로 없음 → k=0, R=0.094 (B=4도 동일)")])
o.append('<text class="s" x="16" y="370">괄호 안 숫자: Greedy가 기록한 P_S 감소량/비용. 어떤 정책도 X→Y 경로 복원 여부를 점수에 쓰지 않는다.</text>')
o.append('<text class="s" x="16" y="390">사례 B: off-task FP V01→V06이 남아 있으면 V04→V00 수정이 V04→V00→V01→V06→V08→V04 순환을 만든다 (stop_reason = dag_invalid_candidate).</text>')
o.append('</svg>'); open(f"{OUT}/figures/fig3_case_edit_sequences.svg","w").write("\n".join(o))
