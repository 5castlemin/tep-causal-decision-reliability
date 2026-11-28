"""Build manifest for S3 public reports, code and cohort-level tables."""
import hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
files=[]
for base in (HERE,HERE/'tables',HERE/'figures'):
 for p in sorted(base.rglob('*')):
  if not p.is_file() or any(part.startswith('outputs') for part in p.parts) or '__pycache__' in p.parts: continue
  if p.name=='s3_integrity_manifest.json': continue
  files.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size})
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip()
tests={p.relative_to(ROOT).as_posix():digest(p) for p in (ROOT/'tests').glob('test_s3_*.py')}
manifest={'classification':'POST_HOC_S3_EXPLORATORY','gate':'S3_CORRECTION_RECOMPUTED_WITH_LIMITATIONS','base_revision':head,'base_tree':tree,'correction_source_code_sha256':{p.name:digest(p) for p in (HERE/'s3_analysis.py',HERE/'write_correction_artifacts.py',HERE/'render_s3_correction_figures.py',HERE/'audit_corrections.py')},'test_code_sha256':tests,'files':files,'data_hashes':{'C_DEVELOPMENT:cohort':'dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716','C_DEVELOPMENT:proposal':'1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584','C_HELDOUT:cohort':'37b3c265ecb65b09a97eda91d29411844c3a3851c9fbff6cfa06445f919a3eba','C_HELDOUT:proposal':'59f1abcf5661a5b3d0658d0db0f7e6afe601ebd09997035228df0716800538d6'},'limitations':['The first exploratory calculation preceded a committed analysis revision; this cannot be represented as preregistered.','Private SCM-keyed intermediate diagnostics remain local and are ignored by Git.','No process memory monitor was active.','Ex-post two-edit interactions, gamma sensitivity, Holm adjustment, and Research D unit-level extension were not run.','No new independent cohort or Research D unit-level analysis.']}
(HERE/'s3_integrity_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(f"Manifest covers {len(files)} public files; base {head}")
