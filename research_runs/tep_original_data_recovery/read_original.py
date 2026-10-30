import zipfile,openpyxl,io,pathlib,numpy as np,json,hashlib,sys
out=pathlib.Path('data/local/tep_original_data_recovery');out.mkdir(exist_ok=True)
records={}
with zipfile.ZipFile(sys.argv[1]) as z:
 for run in (1,2,3):
  arrays={}
  for typ in ('SIMOUT','XMV','TOUT'):
   name=f'3_Normal Steady-State/{run}/1_Original/{typ}.xlsx';blob=z.read(name);s=openpyxl.load_workbook(io.BytesIO(blob),read_only=True,data_only=True).active;arrays[typ]=np.array(list(s.iter_rows(values_only=True)),dtype=float);print(run,typ,arrays[typ].shape,flush=True)
  np.savez_compressed(out/f'normal_{run}.npz',**arrays)
  records[str(run)]={'seed':z.read(f'3_Normal Steady-State/{run}/random_seed.txt').decode(),'shapes':{k:list(v.shape) for k,v in arrays.items()}}
pathlib.Path('research_runs/tep_original_data_recovery/RAW_MANIFEST.json').write_text(json.dumps({'zip_sha256':hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest(),'runs':records},indent=2),encoding='utf8')
