"""Bounded pinned-source acceptance. No discovery, regression fitting, or F1 scoring.

Use --workspace OUTSIDE_REPO. The workspace must already contain hash-verified
official source/micro objects, acquisition.json, a separate venv and setup receipts.
No upstream source bytes are changed. Raw samples stay outside the research repo.
"""
import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))
from src.causalman_micro_acceptance import (PIN, bounded_process, directory_bytes,
    verify_files, verify_manifest_tree, file_sha, admit, available_memory_bytes, hard_do_parent_edges)

A = "PF_M1_T1_Force"
Y = "Sec_C2_Machine1_ProcessResult"
WORKER_TRACE = None

def save(path, value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")

def worker(root, run_id, seed, force, import_only):
    if sys.stdin.readline().strip() != "START":
        raise RuntimeError("Parent resource admission missing")
    source = root/"source"
    manifest = json.loads((root/"acquisition.json").read_text())
    verify_manifest_tree(manifest,json.loads((root/"tree.json").read_text()))
    verify_files(source,manifest)
    screen=json.loads((root/"pickle_opcode_screen.json").read_text())
    if screen["parse_errors"] or screen["known_unsafe_GLOBAL"]:
        raise RuntimeError("Pickle screen rejected")
    sys.path.insert(0,str(source))
    out=root/"runs"/run_id
    out.mkdir(parents=True,exist_ok=False)
    trace={"loads":[],"paths":[],"conversions":[],"interventions":[],"evaluated_expressions":0}
    global WORKER_TRACE
    WORKER_TRACE = trace
    save(out/"progress.json",{"stage":"verified_before_external_import","commit":PIN})
    # This supplements verified provenance; it is not a general hostile-code sandbox.
    allowed_roots=[root.resolve(),Path(sys.base_prefix).resolve(),Path(sys.prefix).resolve(),
                   (REPO/"src").resolve(),(REPO/"scripts").resolve(),Path(os.environ.get("WINDIR",r"C:\Windows")).resolve()]
    def audit(event,args):
        if event.startswith("socket.") or event in ("subprocess.Popen","os.system","os.posix_spawn"):
            raise PermissionError("External worker networking/subprocess denied")
        if event=="open" and isinstance(args[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(args[0])).resolve()
            mode=args[1] or ""
            flags=args[2] if len(args)>2 else 0
            write=any(c in mode for c in "wax+") or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
            if write and not p.is_relative_to(root.resolve()):
                raise PermissionError("Write outside isolated workspace denied")
            if not write and not any(p.is_relative_to(q) for q in allowed_roots):
                raise PermissionError("Read outside declared worker roots denied: "+str(p))
        if event=="pickle.find_class":
            module,name=args
            prefixes=("causalman","line_structure","FCM_Definitions","utils","sympy","numpy","pandas","networkx","collections","copyreg","datetime","builtins")
            if not (module in ("node","fcm","_codecs") or module.startswith(prefixes)):
                raise PermissionError("Unreviewed pickle module: "+module+"."+name)
            if module=="builtins" and name in ("eval","exec","compile","open","__import__"):
                raise PermissionError("Dangerous pickle callable")
    sys.addaudithook(audit)
    from causalman.causalman import CausalMan
    versions={n:importlib.metadata.version(n) for n in ("numpy","pandas","networkx","sympy","matplotlib","pyvis","tqdm")}
    save(out/"progress.json",{"stage":"external_import_passed","versions":versions})
    sim=CausalMan(name="causalman_micro",seed=seed,parallelize=False,save_path=str(out/"generated"))
    if sim.intervention_dict != {}:
        raise RuntimeError("Fresh object retained intervention state")
    if import_only:
        save(out/"result.json",{"status":"PASS_IMPORT_AND_CONSTRUCTOR","versions":versions,"pickle_loads":0,
                                "source_file":str(Path(importlib.import_module("causalman.causalman").__file__).relative_to(root))})
        return
    import pandas as pd
    import numpy as np
    import networkx as nx
    from sympy.stats.rv import RandomSymbol
    sb=importlib.import_module("causalman.sample_batch")
    ug=importlib.import_module("causalman.utils.graph")
    cm=importlib.import_module("causalman.causalman")
    fmod=importlib.import_module("causalman.fcm")
    def graph(g):
        nodes={str(n):{str(k):str(v) for k,v in d.items()} for n,d in g.nodes(data=True)}
        edges=sorted((str(u),str(v),str(k),{str(a):str(b) for a,b in d.items()}) for u,v,k,d in
                     (g.edges(keys=True,data=True) if g.is_multigraph() else ((u,v,"",d) for u,v,d in g.edges(data=True))))
        payload={"type":type(g).__name__,"nodes":nodes,"edges":edges}
        payload["sha256"]=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
        return payload
    current={}
    original_load=sb.load_pickle
    def load_observer(f):
        obj=original_load(f)
        path=Path(f.name).relative_to(source).as_posix()
        trace["loads"].append({"path":path,"sha256":file_sha(f.name),"type":type(obj).__name__})
        if "dag_level_2_" in path:
            current.clear();current.update({"level2":obj.copy(),"level2_path":path})
        elif "dag_level_1_" in path:
            current.update({"level1":obj.copy(),"level1_path":path})
        return obj
    sb.load_pickle=load_observer
    original_convert=ug.dag2fcm
    def convert_observer(*args,**kwargs):
        fcm=original_convert(*args,**kwargs)
        current["active"]=fcm.graph.copy()
        trace["conversions"].append({"seed":kwargs.get("seed"),"active":graph(fcm.graph)})
        return fcm
    ug.dag2fcm=convert_observer
    original_intervene=fmod.FCM.intervene_on
    def intervene_observer(self,intervened_set):
        before=graph(self.graph)
        value=original_intervene(self,intervened_set)
        after={k:graph(g) for k,g in self.mutilated_dags.items()}
        current["applied"]=next(iter(self.mutilated_dags.values())).copy()
        trace["interventions"].append({"before":before,"after":after,"specified":intervened_set})
        return value
    fmod.FCM.intervene_on=intervene_observer
    original_eval=fmod.FCM._FCM__eval_expression
    def eval_observer(self,*args,**kwargs):
        trace["evaluated_expressions"]+=1
        return original_eval(self,*args,**kwargs)
    fmod.FCM._FCM__eval_expression=eval_observer
    original_sample=sb.sample_CausalGraph
    def sample_observer(*args,**kwargs):
        value=original_sample(*args,**kwargs)
        l1=current["level1"];l2=current["level2"];active=current["active"]
        equation_graph=current.get("applied",active)
        def edge_set(g):return {(str(u),str(v)) for u,v in g.edges()}
        active_edges=edge_set(active);ref_edges=edge_set(l2)
        equation_checks=[]
        for node,attrs in equation_graph.nodes(data=True):
            term=attrs.get("term")
            if term is None or term.atoms(RandomSymbol):
                continue
            symbols=list(term.free_symbols)
            if str(node) not in value or not all(str(s) in value for s in symbols):
                continue
            for i in range(min(3,len(value))):
                expected=term.subs({s:value[str(s)].iloc[i] for s in symbols})
                try:
                    expected=float(expected)
                    actual=float(value[str(node)].iloc[i])
                except (TypeError,ValueError):
                    continue
                equation_checks.append({"node":str(node),"row":i,"match":bool(np.isclose(actual,expected,rtol=1e-9,atol=1e-8))})
        rec={"level1_path":current["level1_path"],"level2_path":current["level2_path"],
             "seed":kwargs.get("random_state"),"sample_rows":len(value),
             "level1":graph(l1),"level2":graph(l2),"active":graph(active),
             "active_only_edges":sorted(active_edges-ref_edges),"reference_only_edges":sorted(ref_edges-active_edges),
             "generated_columns":list(value.columns),"deterministic_equation_checks":equation_checks}
        trace["paths"].append(rec)
        save(out/"progress.json",{"stage":"sampled_path","completed_paths":len(trace["paths"]),"internal_rows_so_far":sum(x["sample_rows"] for x in trace["paths"])})
        return value
    sb.sample_CausalGraph=sample_observer
    original_clean=cm.clean_df
    internal={}
    def clean_observer(df,*args,**kwargs):
        val=original_clean(df,*args,**kwargs)
        internal["rows"]=len(val)
        internal["columns"]=list(val.columns)
        internal["stats"]={n:{"dtype":str(val[n].dtype),"unique":int(val[n].nunique(dropna=False)),
                              "min":str(val[n].min()),"max":str(val[n].max())} for n in (A,Y) if n in val}
        return val
    cm.clean_df=clean_observer
    if force is not None:
        sim.intervention_dict={A:force}
    returned=sim.sample(n_samples=32)
    if not isinstance(returned,tuple) or len(returned)!=6:
        raise RuntimeError("SIX_RETURN_API_MISMATCH")
    observed,mag,admg,full,dag,table=returned
    files={}
    for name,df in (("observed",observed),("full",full),("intervention_table",table)):
        path=out/(name+".csv.gz")
        df.to_csv(path,index=False,compression={"method":"gzip","mtime":0})
        files[path.name]={"sha256":file_sha(path),"bytes":path.stat().st_size}
    save(out/"trace.json",trace)
    stats={}
    for name,df in (("observed",observed),("full",full),("intervention_table",table)):
        numeric=df.select_dtypes(include=[np.number])
        stats[name]={"shape":list(df.shape),"columns":list(df.columns),"dtypes":{n:str(t) for n,t in df.dtypes.items()},
                     "nulls":int(df.isna().sum().sum()),"numeric_nonfinite":int((~np.isfinite(numeric.to_numpy(dtype=float))).sum()),
                     "constants":[str(n) for n in df if df[n].nunique(dropna=False)<=1]}
    result={"status":"PASS_SAMPLE_API_ONLY_NOT_SCIENTIFIC_ACCEPTANCE","seed":seed,"force":force,"versions":versions,
            "return_types":[type(x).__name__ for x in returned],"stats":stats,"internal":internal,
            "observed_full_alignment":observed.equals(full.loc[:,list(observed.columns)]),
            "table_rows_aligned":len(table)==len(full)==len(observed),
            "table_active_columns":[str(n) for n in table if table[n].any()],
            "force_values":[str(x) for x in full[A].unique()] if A in full else None,
            "outcome_counts":{str(k):int(v) for k,v in full[Y].value_counts(dropna=False).items()} if Y in full else None,
            "graphs":{n:graph(g) for n,g in (("dag",dag),("admg",admg),("mag",mag))},
            "active_paths":len(trace["paths"]),"effective_seeds":[x["seed"] for x in trace["paths"]],
            "source_files_unchanged_after_run":verify_files(source,manifest),
            "trace_sha256":file_sha(out/"trace.json"),"raw_files":files}
    save(out/"result.json",result)
    if force is not None:
        defects=[z for z in trace["interventions"] if any(
            hard_do_parent_edges(g,A) for g in z["after"].values())]
        if defects:
            result["status"]="FAIL_HARD_DO_GRAPH_CONTRACT"
            result["unremoved_parent_graphs"]=len(defects)
            save(out/"result.json",result)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True,type=Path)
    ap.add_argument("--worker",action="store_true")
    ap.add_argument("--run-id",default="import")
    ap.add_argument("--seed",type=int,default=42)
    ap.add_argument("--force",type=int,choices=(16000,30000))
    ap.add_argument("--import-only",action="store_true")
    args=ap.parse_args()
    root=args.workspace.resolve()
    if root.is_relative_to(REPO):
        raise ValueError("External software and samples must be outside research repo")
    if args.worker:
        try:
            worker(root,args.run_id,args.seed,args.force,args.import_only)
        except Exception as exc:
            failure={"status":"EXTERNAL_RUNTIME_ERROR","type":type(exc).__name__,"error":str(exc),"traceback":traceback.format_exc()}
            out=root/"runs"/args.run_id
            out.mkdir(parents=True,exist_ok=True)
            save(out/"ERROR.json",failure)
            if WORKER_TRACE is not None:
                save(out/"error_trace.json",WORKER_TRACE)
            print(failure["traceback"],flush=True)
            raise
        return
    acquisition=json.loads((root/"acquisition.json").read_text())
    setup=json.loads((root/"setup_receipt.json").read_text())
    elapsed=acquisition["seconds"]+sum(x["wall_seconds"] for x in setup)
    receipts=[]
    contract=json.loads((REPO/"research_runs/causalman_micro_acceptance/CONTRACT.json").read_text())
    for spec in [dict(id="import",seed=42,force=None)]+contract["sampling_schedule"]:
        wheel_bytes=directory_bytes(root/"wheels")
        if admit(acquisition["download_bytes"]+wheel_bytes,directory_bytes(root),
                 shutil.disk_usage(root).free,available_memory_bytes(),elapsed):
            receipts.append({"id":spec["id"],"status":"RESOURCE_BLOCKED_NOT_RUN"});break
        cmd=[str(root/"venv/Scripts/python.exe"),"-I",str(Path(__file__).resolve()),"--workspace",str(root),
             "--worker","--run-id",spec["id"],"--seed",str(spec["seed"])]
        if spec["id"]=="import":cmd+=["--import-only"]
        if spec["force"] is not None:cmd+=["--force",str(spec["force"])]
        receipt=bounded_process(cmd,str(root),str(root),root/(spec["id"]+".log"),1800-elapsed)
        elapsed+=receipt["wall_seconds"]
        receipt.update(id=spec["id"],elapsed_external_seconds=elapsed)
        receipts.append(receipt);save(root/"execution_receipts.json",receipts)
        print(json.dumps(receipt),flush=True)
        if receipt["exit_code"] or receipt["resource_stop"]:
            break
        observed_result=json.loads((root/"runs"/spec["id"]/"result.json").read_text())
        if observed_result["status"].startswith("FAIL_"):
            break
        # Enough remaining time for at least the measured previous sampling cost.
        if spec["id"]!="import" and 1800-elapsed < 1.2*receipt["wall_seconds"]:
            break
    print("Finished bounded schedule; inspect every scientific gate separately.",flush=True)

if __name__=="__main__":
    main()
