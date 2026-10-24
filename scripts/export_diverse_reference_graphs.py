"""Export only declared, source-verified synthetic references; never TEP GT."""
import csv
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_diverse_structure_pilot import save


def main():
    base=ROOT/'research_runs/diverse_structure_pilot';plan=json.loads((base/'PLAN_v1.json').read_text(encoding='utf-8'))
    out=base/'reference_graphs_v1'
    if out.exists():raise ValueError('REFERENCE_EXPORT_ALREADY_EXISTS')
    out.mkdir()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import networkx as nx
    fig,axes=plt.subplots(4,2,figsize=(14,15))
    for spec,ax in zip(plan['structures'],axes.flat):
        sid=spec['structure_id'];record=json.loads((base/'run_v1/acceptance'/sid/'acceptance.json').read_text(encoding='utf-8'))
        assert record['status']=='PASS'
        edges={tuple(e) for e in record['records'][0]['metadata']['returned_edges']}
        assert edges=={(e['source'],e['target']) for e in spec['edges']}
        names=spec['nodes'];coeff={(e['source'],e['target']):e['coefficient'] for e in spec['edges']}
        for suffix,weight in [('A_dir',lambda a,b:int((a,b) in edges)),('coefficients',lambda a,b:coeff.get((a,b),0.))]:
            with (out/f'{sid}_{suffix}.csv').open('w',encoding='utf-8',newline='') as f:
                w=csv.writer(f);w.writerow(['source_to_target',*names])
                for a in names:w.writerow([a,*[weight(a,b) for b in names]])
        save(out/f'{sid}_equations_and_tasks.json',dict(structure_id=sid,nodes=names,
            equations=[dict(target=n,parents=[e for e in spec['edges'] if e['target']==n],noise='Uniform(-sqrt(3),sqrt(3))') for n in names],
            tasks=spec['tasks'],source_gt_checked=True,classification='DECLARED_SYNTHETIC_REFERENCE_ONLY'))
        graph=nx.DiGraph();graph.add_nodes_from(names);graph.add_edges_from(edges)
        positions={}
        for level,group in enumerate(nx.topological_generations(graph)):
            group=sorted(group)
            for j,node in enumerate(group):positions[node]=(level,j-(len(group)-1)/2)
        actions={t['action'] for t in spec['tasks'] if t['task_kind']!='negative_control'};targets={t['target'] for t in spec['tasks']}
        colors=['#d57c3b' if n in targets else '#1877b9' if n in actions else '#64748b' for n in graph]
        nx.draw_networkx(graph,pos=positions,ax=ax,node_color=colors,font_color='white',node_size=850,font_size=11,
            edge_color='#9aa9b5',arrowsize=15,width=1.1)
        nx.draw_networkx_edge_labels(graph,pos=positions,ax=ax,edge_labels={e:str(v) for e,v in coeff.items()},font_size=8,
            bbox=dict(alpha=.7,facecolor='white',edgecolor='none'))
        ax.set_title(f'{sid}: {len(names)} observed variables, {len(edges)} direct edges',fontsize=12)
        ax.margins(.22);ax.axis('off')
    fig.suptitle('Declared synthetic references: observed linear additive DAGs\nBlue: positive-task actions; orange: targets; grey: other observed variables',fontsize=14)
    fig.tight_layout(rect=(0,0,1,.96));fig.savefig(out/'eight_reference_structures.svg');fig.savefig(out/'eight_reference_structures.png',dpi=150);plt.close(fig)
    save(out/'CONTRACT.json',dict(classification='DECLARED_SYNTHETIC_ONLY_NOT_TEP_GT',matrix_convention='row=source,column=target',
        source_commit=plan['source_commit'],plan_sha256=hashlib.sha256((base/'PLAN_v1.json').read_bytes()).hexdigest(),
        exporter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    save(out/'SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256.json'})
    print('PASS 8 source-verified reference matrices/equations and overview figure exported')
if __name__=='__main__':main()
