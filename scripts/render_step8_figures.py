"""Render documentation SVG figures from frozen Step 5/6 SCM summary CSVs.

This script is analysis-display only: it reads repository summaries and does
not read or generate SCMs, observations, interventions, or new outcomes.
"""
from __future__ import annotations

import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research" / "budget_aware_refinement"
FIG = BASE / "figures"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def esc(value: object) -> str:
    return html.escape(str(value))


def svg_start(width: int, height: int, title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#17212b}.small{font-size:12px}.axis{stroke:#637381;stroke-width:1}.grid{stroke:#dbe2e8;stroke-width:1}.muted{fill:#52616b}.title{font-size:22px;font-weight:700}.subtitle{font-size:13px}.label{font-size:14px;font-weight:600}</style>',
        f'<text x="40" y="38" class="title">{esc(title)}</text>',
        f'<text x="40" y="62" class="subtitle muted">{esc(subtitle)}</text>',
    ]


def save(name: str, lines: list[str]) -> None:
    lines.append("</svg>")
    (FIG / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def distribution(s5: list[dict[str, str]], s6: list[dict[str, str]]) -> None:
    w, h = 960, 590
    out = svg_start(w, h, "SCM별 대응 regret 차이", "Dᵢ = mean(FN, FP, REV) of Global regret − Task-Focused regret; one dot per SCM")
    left, right, top, bottom = 115, 890, 105, 475
    ymin, ymax = -0.18, 0.66
    ymap = lambda v: bottom - (v - ymin) * (bottom - top) / (ymax - ymin)
    for tick in [-0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
        y = ymap(tick)
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" class="{"axis" if tick == 0 else "grid"}"/>')
        out.append(f'<text x="{left-12}" y="{y+4:.1f}" text-anchor="end" class="small">{tick:.1f}</text>')
    out += [f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" class="axis"/>', f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" class="axis"/>']
    out.append(f'<text x="25" y="{(top+bottom)//2}" transform="rotate(-90 25 {(top+bottom)//2})" class="label">Dᵢ (standardized loss scale)</text>')
    for x, rows, name, color, mean in [(330, s5, "Step 5 development (n=64)", "#64748b", 0.014660484921723964), (675, s6, "Step 6 held-out cohort (n=200)", "#0f766e", 0.020072511261796423)]:
        n = len(rows)
        for i, row in enumerate(rows):
            value = float(row["D_i"])
            jitter = (((i * 37) % 101) / 100 - 0.5) * (118 if value == 0 else 84)
            cx, cy = x + jitter, ymap(value)
            fill = "#9aa6b2" if value == 0 else ("#c2410c" if value > 0 else "#2563eb")
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.2" fill="{fill}" fill-opacity="0.72"/>')
        my = ymap(mean)
        out.append(f'<path d="M{x} {my-9:.1f} L{x+9} {my:.1f} L{x} {my+9:.1f} L{x-9} {my:.1f} Z" fill="#111827"/>')
        out.append(f'<text x="{x}" y="{bottom+28}" text-anchor="middle" class="label">{esc(name)}</text>')
        pos, neg, zero = sum(float(r["D_i"]) > 0 for r in rows), sum(float(r["D_i"]) < 0 for r in rows), sum(float(r["D_i"]) == 0 for r in rows)
        out.append(f'<text x="{x}" y="{bottom+49}" text-anchor="middle" class="small">mean {mean:.4f} · +/−/0 = {pos}/{neg}/{zero}</text>')
    out.append('<circle cx="135" cy="535" r="4" fill="#c2410c"/><text x="146" y="539" class="small">D&gt;0</text><circle cx="215" cy="535" r="4" fill="#2563eb"/><text x="226" y="539" class="small">D&lt;0</text><circle cx="295" cy="535" r="4" fill="#9aa6b2"/><text x="306" y="539" class="small">D=0</text><path d="M390 526 L399 535 L390 544 L381 535 Z" fill="#111827"/><text x="407" y="539" class="small">arithmetic mean</text>')
    out.append('<text x="40" y="575" class="small muted">Points are SCMs, not error-type rows. The x-jitter is display-only; zero values are retained.</text>')
    save("step8_scm_difference_distribution.svg", out)


def type_means(s5: list[dict[str, str]], s6: list[dict[str, str]]) -> None:
    w, h = 900, 470
    out = svg_start(w, h, "오류 유형별 SCM 내 평균 차이", "Each SCM contributes one paired difference per type; types are repeated within SCM, not independent samples")
    left, right, top, bottom = 100, 850, 105, 375
    scale = (right-left)/0.04
    for tick in [0, .01, .02, .03, .04]:
        x=left+tick*scale
        out.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" class="{"axis" if tick==0 else "grid"}"/>')
        out.append(f'<text x="{x:.1f}" y="{bottom+22}" text-anchor="middle" class="small">{tick:.2f}</text>')
    means={typ:(sum(float(row[f"{typ}_D"]) for row in rows)/len(rows) for rows in (s5,s6)) for typ in ("FN","FP","REV")}
    means={typ:tuple(vals) for typ,vals in means.items()}
    ys={"FN":160,"FP":250,"REV":340}
    for typ,(a,b) in means.items():
        y=ys[typ]
        out.append(f'<text x="55" y="{y+7}" class="label">{typ}</text>')
        for yy,val,color,label in [(y-15,a,"#64748b","Step 5"),(y+15,b,"#0f766e","Step 6")]:
            x=left+val*scale
            out.append(f'<rect x="{left}" y="{yy-7}" width="{max(1,x-left):.1f}" height="14" fill="{color}"/>')
            out.append(f'<text x="{x+8:.1f}" y="{yy+4}" class="small">{val:.4f}</text>')
    out.append('<rect x="560" y="420" width="12" height="12" fill="#64748b"/><text x="578" y="431" class="small">Step 5 development</text><rect x="730" y="420" width="12" height="12" fill="#0f766e"/><text x="748" y="431" class="small">Step 6 replication</text>')
    out.append('<text x="100" y="455" class="small muted">Mean Dtype = Global regret − Task-Focused regret. No inferential type ranking is made.</text>')
    save("step8_error_type_means.svg",out)


def transitions() -> None:
    w,h=980,475
    out=svg_start(w,h,"그래프 차이에서 regret 차이까지","Step 6 confirmation cohort · counts out of 200 SCMs for each error type")
    left, right, top, bottom=180,900,110,390
    maxv=120; scale=(right-left)/maxv
    rows=[("FN",76,14,14),("FP",109,3,3),("REV",93,25,25)]
    labels=[("Different final graph","#64748b"),("Different selected k","#0f766e"),("Different GT regret","#c2410c")]
    for i,(typ,g,k,r) in enumerate(rows):
        y=145+i*88
        out.append(f'<text x="70" y="{y+7}" class="label">{typ}</text>')
        for j,(val,(label,color)) in enumerate(zip([g,k,r],labels)):
            yy=y+(j-1)*20
            ww=val*scale
            out.append(f'<rect x="{left}" y="{yy-7}" width="{ww:.1f}" height="14" fill="{color}"/>')
            out.append(f'<text x="{left+ww+8:.1f}" y="{yy+4}" class="small">{val}/200</text>')
    for i,(lab,col) in enumerate(labels):
        x=210+i*235
        out.append(f'<rect x="{x}" y="420" width="12" height="12" fill="{col}"/><text x="{x+18}" y="431" class="small">{esc(lab)}</text>')
    out.append('<text x="40" y="462" class="small muted">Observed different-k and regret counts match here because same action, same GT loss grid; this is an observed property, not a general implication of any different graph.</text>')
    save("step8_graph_k_regret_transition.svg",out)


def sensitivity() -> None:
    w,h=900,430
    out=svg_start(w,h,"극단값 민감도: SCM 평균 D","Pre-specified descriptive summaries; full-cohort mean remains primary; all bars start at zero")
    left,right,top,bottom=105,850,115,340
    ymax=.022; scale=(bottom-top)/ymax
    for tick in [0,.005,.010,.015,.020]:
        y=bottom-tick*scale
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" class="{"axis" if tick==0 else "grid"}"/>')
        out.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="small">{tick:.3f}</text>')
    data=[("Step 5",[.0146604849,.0082335,.0046345],"#64748b"),("Step 6",[.0200725113,.0171093,.0143115],"#0f766e")]
    xs=[260,485,710]
    captions=["Full sample","Remove top 1","Remove top 2"]
    for name,vals,color in data:
        for x,val,cap in zip(xs,vals,captions):
            y=bottom-val*scale
            out.append(f'<rect x="{x-31}" y="{y:.1f}" width="62" height="{bottom-y:.1f}" fill="{color}"/>')
            out.append(f'<text x="{x}" y="{y-8:.1f}" text-anchor="middle" class="small">{val:.4f}</text>')
            out.append(f'<text x="{x}" y="{bottom+20}" text-anchor="middle" class="small">{cap}</text>')
    out.append('<rect x="610" y="68" width="12" height="12" fill="#64748b"/><text x="628" y="79" class="small">Step 5</text><rect x="710" y="68" width="12" height="12" fill="#0f766e"/><text x="728" y="79" class="small">Step 6</text>')
    out.append('<text x="40" y="405" class="small muted">Removing cases is a sensitivity display only; no cases are removed from the reported cohort mean. D is on the frozen standardized-loss scale.</text>')
    save("step8_extreme_sensitivity.svg",out)


def cases() -> None:
    w,h=1120,660
    out=svg_start(w,h,"대표 SCM에서 편집 순서와 조작 결정","Illustrative cases from Step 6 raw ledgers; task-path schematic omits non-task edges and is not a full DAG")
    out += ['<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#334155"/></marker><marker id="orange" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#c2410c"/></marker></defs>']
    # two case cards
    for y,title,detail,paths,actions in [
      (105,"238 · Task-Focused 사례, FN","V04 → V02 · two indirect routes",[(170,230,250,310),(250,310,330,230),(170,230,250,150),(250,150,330,230)],[("Global restores V03→V01 (off task)","k=+1 · GT regret 0.914621","#64748b"),("Task-Focused restores V04→V03 (task route)","k=−1 · GT regret 0","#0f766e")]),
      (390,"606 · Global 사례, REV","V03 → V02 · two indirect routes",[(170,515,250,465),(250,465,330,515),(170,515,250,565),(250,565,330,515)],[("Global reverses V01→V04", "k=+1 · GT regret 0","#64748b"),("Task-Focused reverses V06→V03 → V03→V06", "k=−1 · GT regret 0.434361","#0f766e")])]:
        out.append(f'<rect x="35" y="{y}" width="1050" height="245" rx="14" fill="#f8fafc" stroke="#cbd5e1"/>')
        out.append(f'<text x="58" y="{y+31}" class="label">{esc(title)}</text><text x="58" y="{y+52}" class="small muted">{esc(detail)}</text>')
        # GT route edges
        for idx,(x1,y1,x2,y2) in enumerate(paths):
            out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#334155" stroke-width="2.5" marker-end="url(#arrow)"/>')
        if y==105:
            nodes=[(170,230,"V04 · X"),(250,310,"V03"),(330,230,"V02 · Y"),(250,150,"V06")]
        else:
            nodes=[(170,515,"V03 · X"),(250,465,"V04"),(330,515,"V02 · Y"),(250,565,"V06")]
        for x,yy,label in nodes:
            out.append(f'<circle cx="{x}" cy="{yy}" r="24" fill="#ffffff" stroke="#0f766e" stroke-width="2"/><text x="{x}" y="{yy+4}" text-anchor="middle" class="small">{esc(label)}</text>')
        for idx,(line1,line2,color) in enumerate(actions):
            yy=y+108+idx*57
            out.append(f'<rect x="420" y="{yy-24}" width="625" height="45" rx="8" fill="#ffffff" stroke="{color}" stroke-width="2"/>')
            out.append(f'<text x="438" y="{yy-4}" class="small">{esc(line1)}</text><text x="438" y="{yy+13}" class="small" fill="{color}">{esc(line2)}</text>')
    out.append('<text x="40" y="650" class="small muted">Selected k is the same action variable with a different standardized level. Regret is relative to the fixed candidate grid; cases are explanatory, not representative.</text>')
    save("step8_case_mechanism.svg",out)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    s5=read_csv(BASE/"step5_development_v1"/"STEP5_DEVELOPMENT_SCM_SUMMARY.csv")
    s6=read_csv(BASE/"step6_confirmation_v1"/"STEP6_CONFIRMATION_SCM_SUMMARY.csv")
    if len(s5)!=64 or len(s6)!=200:
        raise SystemExit(f"Unexpected frozen summary sizes: step5={len(s5)}, step6={len(s6)}")
    distribution(s5,s6); type_means(s5,s6); transitions(); sensitivity(); cases()
    print(f"Wrote 5 static SVGs to {FIG}")


if __name__ == "__main__":
    main()
