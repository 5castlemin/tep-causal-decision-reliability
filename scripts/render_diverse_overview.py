"""Readable scientific overview; scientific reference matrices remain unchanged."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import networkx as nx
    base=ROOT/'research_runs/diverse_structure_pilot';plan=json.loads((base/'PLAN_v1.json').read_text(encoding='utf-8'))
    out=base/'figures_v1'
    if out.exists():raise ValueError('FIGURE_DIRECTORY_EXISTS')
    out.mkdir();fig,axes=plt.subplots(4,2,figsize=(14,15))
    for spec,ax in zip(plan['structures'],axes.flat):
        graph=nx.DiGraph();graph.add_nodes_from(spec['nodes']);graph.add_edges_from((e['source'],e['target']) for e in spec['edges'])
        if spec['structure_id'] in ['S2','S6']:positions=nx.circular_layout(graph)
        else:
            positions={}
            for i,group in enumerate(nx.topological_generations(graph)):
                group=sorted(group)
                for j,n in enumerate(group):positions[n]=(i,j-(len(group)-1)/2)
        actions={t['action'] for t in spec['tasks'] if t['task_kind']!='negative_control'};targets={t['target'] for t in spec['tasks']}
        colors=['#d57c3b' if n in targets else '#1877b9' if n in actions else '#64748b' for n in graph]
        connection='arc3,rad=0.12'
        nx.draw_networkx(graph,pos=positions,ax=ax,node_color=colors,font_color='white',node_size=850,font_size=11,
            edge_color='#8395a4',arrowsize=15,width=1.,connectionstyle=connection)
        nx.draw_networkx_edge_labels(graph,pos=positions,ax=ax,edge_labels={(e['source'],e['target']):str(e['coefficient']) for e in spec['edges']},
            font_size=8,connectionstyle=connection,bbox=dict(alpha=.8,facecolor='white',edgecolor='none'))
        ax.set_title(f"{spec['structure_id']}: {len(graph)} observed variables, {len(graph.edges)} direct edges",fontsize=12)
        ax.margins(.18);ax.axis('off')
    fig.suptitle('Eight declared synthetic DAGs (all acyclic; layout does not encode time)\nBlue: positive-task actions; orange: targets; grey: other observed variables',fontsize=14)
    fig.tight_layout(rect=(0,0,1,.96));fig.savefig(out/'eight_structures.svg');fig.savefig(out/'eight_structures.png',dpi=150);plt.close(fig)
    record=dict(renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),plan_sha256=hashlib.sha256((base/'PLAN_v1.json').read_bytes()).hexdigest(),
        scientific_reference_changes=False,reason='curved/circular layout prevents dense-edge overlap in initial overview')
    (out/'FIGURE_PROVENANCE.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    (out/'SHA256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256.json'},indent=2)+'\n',encoding='utf-8')
    print('PASS readable overview rendered; reference matrices unchanged')
if __name__=='__main__':main()
