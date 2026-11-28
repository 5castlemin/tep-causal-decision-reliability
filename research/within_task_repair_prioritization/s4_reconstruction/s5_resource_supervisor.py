"""Enforce one cumulative wall and process-tree RSS ceiling over S5 stages."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
import psutil

def tree_rss(root_pid):
    try: root=psutil.Process(root_pid)
    except psutil.Error: return 0
    procs=[root]
    try: procs.extend(root.children(recursive=True))
    except psutil.Error: pass
    total=0
    for p in procs:
        try: total+=p.memory_info().rss
        except psutil.Error: continue
    return total
def stop_tree(proc):
    try: root=psutil.Process(proc.pid); descendants=root.children(recursive=True)
    except psutil.Error: descendants=[]
    for p in reversed(descendants):
        try: p.terminate()
        except psutil.Error: pass
    try: proc.terminate()
    except OSError: pass
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: proc.kill()
    for p in descendants:
        try:
            if p.is_running(): p.kill()
        except psutil.Error: pass
def run_stage(command, start, wall_cap, rss_cap):
    proc=subprocess.Popen(command,stdin=subprocess.DEVNULL)
    peak=0
    while proc.poll() is None:
        elapsed=time.monotonic()-start; rss=tree_rss(os.getpid()); peak=max(peak,rss)
        if elapsed>wall_cap or rss>rss_cap:
            reason='wall_cap' if elapsed>wall_cap else 'aggregate_process_tree_rss_cap'
            stop_tree(proc)
            return {'returncode':proc.poll(),'peak_rss_bytes':peak,'elapsed_seconds':time.monotonic()-start,'stopped_for':reason}
        time.sleep(2)
    return {'returncode':proc.returncode,'peak_rss_bytes':peak,'elapsed_seconds':time.monotonic()-start,'stopped_for':None}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--python',required=True); p.add_argument('--script',required=True); p.add_argument('--attempt-id',required=True); p.add_argument('--recommendation-lock',required=True); p.add_argument('--recommendation-lock-sha256',required=True); p.add_argument('--evaluation-lock',required=True); p.add_argument('--evaluation-lock-sha256',required=True); p.add_argument('--resume-training-csv'); p.add_argument('--resume-g0-records'); p.add_argument('--private-root',required=True); p.add_argument('--source-root',required=True); p.add_argument('--data-root',required=True); p.add_argument('--evaluator-output',required=True); p.add_argument('--public-summary',required=True); p.add_argument('--report',required=True); a=p.parse_args()
    root=Path(a.private_root); root.mkdir(parents=True,exist_ok=True); Path(a.report).parent.mkdir(parents=True,exist_ok=True)
    if Path(a.report).exists(): raise FileExistsError('resource report exists')
    started=time.monotonic(); stages=[]; wall=14400; rsscap=4*1024**3
    base=[a.python,a.script,'--private-root',a.private_root,'--source-root',a.source_root,'--data-root',a.data_root]
    env=os.environ.copy()
    rec_command=base+['--stage','recommendation','--run-lock',a.recommendation_lock,'--run-lock-sha256',a.recommendation_lock_sha256]
    if a.resume_training_csv: rec_command+=['--resume-training-csv',a.resume_training_csv]
    if a.resume_g0_records: rec_command+=['--resume-g0-records',a.resume_g0_records]
    rec=run_stage(rec_command,started,wall,rsscap); stages.append({'stage':'recommendation','attempt_id':a.attempt_id,'resumed_training_sample':bool(a.resume_training_csv),'resume_training_raw_sha256':hashlib.sha256(Path(a.resume_training_csv).read_bytes()).hexdigest() if a.resume_training_csv else None,'resumed_g0_checkpoint':bool(a.resume_g0_records),'resume_g0_sha256':hashlib.sha256(Path(a.resume_g0_records).read_bytes()).hexdigest() if a.resume_g0_records else None,**rec})
    if rec['returncode']!=0 or rec['stopped_for']:
        result={'schema':'S5_RESOURCE_SUPERVISION_V1','attempt_id':a.attempt_id,'status':'STOPPED_BEFORE_EVALUATION','stages':stages,'peak_process_tree_rss_bytes':max(x['peak_rss_bytes'] for x in stages),'wall_seconds':time.monotonic()-started,'limits':{'wall_seconds':wall,'aggregate_process_tree_rss_bytes':rsscap},'monitor':'psutil recursive process tree, sampled every 2 seconds; not an OS-enforced sandbox'}
        Path(a.report).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8'); raise SystemExit(rec['returncode'] or 124)
    ev=run_stage(base+['--stage','evaluation','--run-lock',a.evaluation_lock,'--run-lock-sha256',a.evaluation_lock_sha256,'--evaluator-output',a.evaluator_output,'--public-summary',a.public_summary],started,wall,rsscap); stages.append({'stage':'evaluation','attempt_id':a.attempt_id,**ev})
    result={'schema':'S5_RESOURCE_SUPERVISION_V1','attempt_id':a.attempt_id,'status':'PASS' if ev['returncode']==0 and not ev['stopped_for'] else 'INCOMPLETE','stages':stages,'peak_process_tree_rss_bytes':max(x['peak_rss_bytes'] for x in stages),'wall_seconds':time.monotonic()-started,'limits':{'wall_seconds':wall,'aggregate_process_tree_rss_bytes':rsscap},'monitor':'psutil recursive process tree, sampled every 2 seconds; not an OS-enforced sandbox'}
    Path(a.report).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    if result['status']!='PASS': raise SystemExit(ev['returncode'] or 124)
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
