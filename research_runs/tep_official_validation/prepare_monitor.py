import pathlib,hashlib,json,difflib,shutil
root=pathlib.Path('data/local/tep_matlab_local_validation/staged_20261029'); dest=pathlib.Path('data/local/tep_official_validation/run_v1');dest.mkdir(parents=True,exist_ok=False)
for p in root.iterdir():
 if p.is_file():shutil.copy2(p,dest/p.name)
p=dest/'temexd_mod.c'; original=p.read_text(encoding='latin1'); anchor='  // Shut down the simulation if ISD is non-zero.'
assert original.count(anchor)==1
code=r'''
  /* Research diagnostic monitor: no process or controller equations changed. */
  {
    int reason=0, j; FILE *fp; const char *path=getenv("TEP_GUARD_LOG");
    const char *test=getenv("TEP_GUARD_TEST");
    for(j=0;j<50;j++) if(!mxIsFinite(rx[j])) reason=1;
    for(j=0;j<41;j++) if(!mxIsFinite(ModelData->pv_.xmeas[j])) reason=2;
    for(j=0;j<12;j++) if(!mxIsFinite(ModelData->pv_.xmv[j]) || ModelData->pv_.xmv[j]<0 || ModelData->pv_.xmv[j]>100) reason=3;
    if(ModelData->pv_.xmeas[6]>=3000 || ModelData->pv_.xmeas[8]>=175) reason=4;
    if(ModelData->pv_.xmeas[7]<=0 || ModelData->pv_.xmeas[7]>=100 || ModelData->pv_.xmeas[11]<=0 || ModelData->pv_.xmeas[11]>=100 || ModelData->pv_.xmeas[14]<=0 || ModelData->pv_.xmeas[14]>=100) reason=5;
    if(ModelData->dvec_.idv[28]!=0) reason=6;
    if(test && test[0]=='1' && rt>=0.0005) reason=99;
    if(path && (ssIsMajorTimeStep(S)||reason)) {
      fp=fopen(path,"a");
      if(!fp){ssSetErrorStatus(S,"Research monitor log unavailable");return;}
      fprintf(fp,"%.17g",rt);
      for(j=0;j<41;j++) fprintf(fp,",%.17g",ModelData->pv_.xmeas[j]);
      for(j=0;j<12;j++) fprintf(fp,",%.17g",ModelData->pv_.xmv[j]);
      for(j=0;j<50;j++) fprintf(fp,",%.17g",rx[j]);
      fprintf(fp,",%d\n",reason);fclose(fp);
    }
    if(reason){ssSetStopRequested(S,1);return;}
  }
'''
patched=original.replace(anchor,code+'\n'+anchor);p.write_text(patched,encoding='latin1')
(dest/'monitor.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),patched.splitlines(True))),encoding='utf8')
manifest={'upstream_c_sha256':hashlib.sha256((root/'temexd_mod.c').read_bytes()).hexdigest(),'patched_c_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'patch':'extra logging and stop checks only','checks':'all 50 states finite;41 sensors finite and selected measured limits;12 cached commands 0..100;native shutdown','limitations':'no physical-state bounds beyond finiteness; sample-and-hold sensors distinct from physical state; checks at mdlOutputs not every derivative','phase_B':'only if matched environment','order':['injected stop A0','normal short A0','10min A1','2h A2 if prior succeeds'],'match_gate':'requires source/controller/provenance/time/preprocessing and independent comparable data; no similarity-only pass'}
pathlib.Path('research_runs/tep_official_validation/EXECUTION_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
