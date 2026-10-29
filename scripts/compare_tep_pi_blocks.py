"""Compare published PI block attributes; no inference about execution equivalence."""
import sys,types,importlib,pathlib,zipfile,re,csv,math
root=pathlib.Path(sys.argv[2]).resolve()
for n,p in [('tep_studio',root),('tep_studio.control',root/'control')]:
 m=types.ModuleType(n);m.__path__=[str(p)];sys.modules[n]=m
reg=importlib.import_module('tep_studio.control.registry').RICKER_MODE1
with zipfile.ZipFile(sys.argv[1]) as f:
 n=next(x for x in f.namelist() if x.endswith('MultiLoop_mode1.mdl'));s=f.read(n).decode('latin1')
blocks=[]
for b in re.findall(r'Block\s*\{([^{}]*)\}',s):
 if 'TElib/Discrete PI' not in b: continue
 row={}
 for k in ('Name','SourceBlock','Kc','Ti','Ts','x0','Hi','Lo'):
  v=re.search(r'^\s*'+k+r'\s+"([^"]*)"',b,re.M);row[k]=v.group(1) if v else None
 blocks.append(row)
feed={'A feed':'xmv3_0','C feed':'xmv4_0','D feed':'xmv1_0','E feed':'xmv2_0','Purge':'xmv6_0','Sep flow':'xmv7_0','Strip flow':'xmv8_0'}
loops=list(reg.feed_loops)+[getattr(reg,n) for n in ('production','reactor_level','separator_level','separator_temperature','stripper_level','reactor_temperature','reactor_pressure','pct_g','ya','yac')]
def val(x):
 if x is None:return None
 if x=='Ts_base':return .0005
 if x in ('inf','-inf'):return float(x)
 if re.fullmatch(r'[\d.eE+\-/]+',x):return eval(x,{'__builtins__':{}},{})
 return None
rows=[]
for loop in loops:
 matched=[b for b in blocks if (b['x0']==feed[loop.name] if loop.name in feed else b['Name']==loop.name)]
 if len(matched)!=1:raise RuntimeError((loop.name,matched))
 b=matched[0]; pairs=[('Kc',loop.kc),('Ti',loop.ti_hours),('Ts',loop.ts_hours),('Hi',loop.hi),('Lo',loop.lo)]
 checks={k:('NOT_APPLICABLE' if b[k] is None else ('MATCH' if math.isclose(val(b[k]),v,rel_tol=1e-12,abs_tol=1e-12) else 'DIFF')) for k,v in pairs}
 rows.append({'loop':loop.name,'pv_studio':loop.pv,'drives_studio':getattr(loop,'mv',getattr(loop,'drives','')),'official_block':b['Name'],'official_Kc':b['Kc'],'studio_Kc':loop.kc,'official_Ti_h':b['Ti'],'studio_Ti_h':loop.ti_hours,'official_Ts_h':b['Ts'],'studio_Ts_h':loop.ts_hours,'official_limits':str((b['Lo'],b['Hi'])),'studio_limits':str((loop.lo,loop.hi)),'official_x0_expression':b['x0'],'studio_initial_output':loop.x0,'parameter_comparison':str(checks),'initial_memory_comparison':'UNKNOWN: official runtime workspace and internal PI memory unverified','target_and_runtime_semantics':'UNKNOWN: no official run/trace; Studio default from initial measurement','source':'MultiLoop_mode1.mdl PI block; Studio control/registry.py'})
with open('research_runs/tep_operating_condition/CONTROL_DIFFERENCES.csv','w',encoding='utf8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print('PI blocks:',len(rows),'mismatches:',[(x['loop'],x['parameter_comparison']) for x in rows if 'DIFF' in x['parameter_comparison']])
