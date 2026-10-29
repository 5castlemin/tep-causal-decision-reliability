import subprocess,csv,sys,json,math,pathlib
out=pathlib.Path(sys.argv[2]);out.mkdir(exist_ok=True)
cmd=[sys.argv[1],'run','--hours','0.16666666666666666','--seed','465120799','--every','1']
with (out/'stderr.txt').open('w',encoding='utf8') as err,(out/'rust_10min.csv').open('w',newline='',encoding='utf8') as f:
 p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1); reader=csv.reader(p.stdout);writer=csv.writer(f);headers=next(reader);writer.writerow(headers);n=0;reason=None
 for row in reader:
  vals=[float(x) for x in row];n+=1;writer.writerow(row)
  def v(i):return vals[next(j for j,k in enumerate(headers) if k.startswith('XMEAS_'+str(i)+'_'))]
  if not all(math.isfinite(x) for x in vals) or v(7)>=3000 or v(9)>=175 or any(not 0<v(i)<100 for i in (8,12,15)):
   reason='received sample violates measured threshold or is nonfinite';p.terminate();break
 code=p.wait(timeout=10)
 (out/'gate.json').write_text(json.dumps({'rows':n,'stop_reason':reason,'exit_code':code,'caveat':'stdout buffering may delay observation; not a per-step safety guarantee'},indent=2),encoding='utf8')
 if reason:sys.exit(1)
 sys.exit(code)
