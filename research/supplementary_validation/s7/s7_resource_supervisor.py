"""Enforce the locked cumulative S7 wall-time and process-tree RSS limits."""
from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from pathlib import Path
import psutil

def rss_tree(pid):
 try:p=psutil.Process(pid)
 except psutil.Error:return 0
 procs=[p]
 try:procs.extend(p.children(recursive=True))
 except psutil.Error:pass
 total=0
 for x in procs:
  try:total+=x.memory_info().rss
  except psutil.Error:pass
 return total
def terminate_tree(proc):
 try:root=psutil.Process(proc.pid);children=root.children(recursive=True)
 except psutil.Error:children=[]
 for x in reversed(children):
  try:x.terminate()
  except psutil.Error:pass
 try:proc.terminate();proc.wait(timeout=4)
 except Exception:
  try:proc.kill()
  except OSError:pass
def run(cmd,start,wall,rss):
 p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL);peak=0
 while p.poll() is None:
  elapsed=time.monotonic()-start;now=rss_tree(os.getpid());peak=max(peak,now)
  if elapsed>wall or now>rss:
   why='wall_time' if elapsed>wall else 'process_tree_rss';terminate_tree(p)
   return {'returncode':p.poll(),'peak_rss_bytes':peak,'elapsed_seconds':time.monotonic()-start,'stopped_for':why}
  time.sleep(2)
 return {'returncode':p.returncode,'peak_rss_bytes':peak,'elapsed_seconds':time.monotonic()-start,'stopped_for':None}
def main():
 a=argparse.ArgumentParser();a.add_argument('--python',required=True);a.add_argument('--runner',required=True);a.add_argument('--lock-sha256',required=True);a.add_argument('--source-root',required=True);a.add_argument('--private-root',required=True);a.add_argument('--public-output',required=True);a.add_argument('--resource-report',required=True);x=a.parse_args()
 root=Path(x.private_root)
 if root.exists():raise FileExistsError('S7 private root exists; refusing overwrite')
 Path(x.resource_report).parent.mkdir(parents=True,exist_ok=True)
 start=time.monotonic();caps={'wall_seconds':14400,'process_tree_rss_bytes':4*1024**3};stages=[]
 base=[x.python,x.runner,'--lock-sha256',x.lock_sha256,'--source-root',x.source_root,'--private-root',x.private_root,'--public-output',x.public_output]
 for stage in ('recommendation','evaluation'):
  result=run(base+['--stage',stage],start,caps['wall_seconds'],caps['process_tree_rss_bytes']);stages.append({'stage':stage,**result})
  if result['returncode']!=0 or result['stopped_for']:break
 report={'schema':'S7_RESOURCE_REPORT_V1','status':'PASS' if len(stages)==2 and stages[-1]['returncode']==0 and not stages[-1]['stopped_for'] else 'INCOMPLETE','limits':caps,'wall_seconds':time.monotonic()-start,'peak_process_tree_rss_bytes':max((s['peak_rss_bytes'] for s in stages),default=0),'sampling_parallelism':1,'monitor':'psutil process-tree RSS sampled every 2 seconds; monitor is not an OS sandbox','stages':stages}
 Path(x.resource_report).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps(report,sort_keys=True))
 if report['status']!='PASS':raise SystemExit(stages[-1]['returncode'] or 124)
if __name__=='__main__':main()
