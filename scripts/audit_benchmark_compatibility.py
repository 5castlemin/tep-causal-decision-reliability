"""Read-only identity, static wiring and retained-asset audit. No simulator run."""
import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BENCHMARK='72b0f5e3d14192478186ee0dc4338b7448087789'
PR4='71c5448ed9a82548d86f40f60be842020f69538d'
BASE='172e84bcafb82dd5074f097fcabfb94f28ff96e3'


def git(repo,*args):
    return subprocess.check_output(['git','-c','core.longpaths=true','-C',str(repo),*args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blocks(text,kind):
    out=[]
    for match in re.finditer(r'Block\s*\{\s*BlockType\s+'+kind+r'\b(.*?)^\s*\}',text,re.S|re.M):
        fields=dict(re.findall(r'^\s*(Name|Value|Port)\s+"([^"\n]*)"',match.group(1),re.M))
        out.append(fields)
    return out


def trace_setpoint(text,name):
    """Use input-port wiring; misleading xmv* block names are not MV indices."""
    matches=[b for b in blocks(text,'Inport') if b.get('Name')==name]
    if len(matches)!=1:
        raise ValueError('입력 port 이름이 유일하지 않음: '+name)
    port=int(matches[0]['Port'])
    sources=re.findall(r'SrcBlock\s+"([^"\n]+)"\s+SrcPort\s+1\s+DstBlock\s+"TE Plant"\s+DstPort\s+'+str(port)+r'\b',text)
    if len(sources)!=1:
        raise ValueError('외부 설정값 배선이 유일하지 않음: '+name)
    constants=[b for b in blocks(text,'Constant') if b.get('Name')==sources[0]]
    if len(constants)!=1:
        raise ValueError('설정값 Constant가 유일하지 않음')
    return dict(input_name=name,port=port,constant_block=sources[0],value=float(constants[0]['Value']))


def asset_review():
    changed=git(ROOT,'diff','--name-status',BASE,PR4).decode().splitlines()
    files=[];groups=defaultdict(list)
    for line in changed:
        status,path=line.split('\t')
        data=git(ROOT,'show',PR4+':'+path)
        files.append(dict(change=status,path=path,bytes=len(data),sha256=sha(data)))
        groups[sha(data)].append(path)
    return dict(base=BASE,head=PR4,changed_files=len(files),added_files=sum(x['change']=='A' for x in files),
                total_changed_content_bytes=sum(x['bytes'] for x in files),largest=sorted(files,key=lambda x:x['bytes'],reverse=True)[:5],
                duplicate_groups=[v for v in groups.values() if len(v)>1],files=files,
                policy='파일 삭제·이동·압축 보존정책 변경 없음. Git는 동일 blob을 공유하며, 원시 재실행 이력과 파생 분석은 구분하여 유지한다.')


def audit(benchmark,archive,original_archive,candidate):
    prefix=BENCHMARK+':TenneseeEastman/'
    csv_bytes=git(benchmark,'show',prefix+'datasetTE.csv')
    gt_bytes=git(benchmark,'show',prefix+'TEGroundTruth.txt')
    numpy_bytes=git(benchmark,'show',prefix+'datasetTENumpy.txt')
    local=(ROOT/'data/local/datasetTE.csv').read_bytes()
    gt=(ROOT/'data/local/TEGroundTruth.txt').read_bytes()
    assert local==csv_bytes and gt==gt_bytes
    rows=list(csv.reader(io.StringIO(csv_bytes.decode('utf-8-sig'))))
    matrix=np.asarray([[float(x) for x in row[1:]] for row in rows[1:]])
    other=np.loadtxt(io.BytesIO(numpy_bytes),delimiter=',')
    with zipfile.ZipFile(archive) as z:
        selected={name:z.read('temexd_mod/'+name) for name in ['MultiLoop_mode1.mdl','Mode_1_Init.m','Mode1xInitial.mat','temexd_mod.c','teprob_mod.h','README.txt']}
    text=selected['MultiLoop_mode1.mdl'].decode('latin1')
    init=selected['Mode_1_Init.m'].decode('latin1')
    setpoints=[trace_setpoint(text,n) for n in ['Reactor Level Setpoint','Reactor Press Setpoint','Reactor Temp Setpoint']]
    tree=git(benchmark,'ls-tree','-r','--name-only',BENCHMARK).decode().splitlines()
    plan=json.loads((ROOT/'experiments/simulator/diagnostics/run_20261023_aligned/plan.json').read_text(encoding='utf-8'))
    controller=(candidate/'src/tep/controllers.py').read_bytes()
    return dict(protocol='BENCHMARK-COMPATIBILITY-READONLY-v1',benchmark_commit=BENCHMARK,
                input_hashes=dict(dataset_csv=sha(csv_bytes),gt_txt=sha(gt_bytes),numpy_export=sha(numpy_bytes)),
                dataset=dict(shape=list(matrix.shape),index_is_0_to_1498=[int(r[0]) for r in rows[1:]]==list(range(1499)),variables=rows[0][1:],
                             numpy_shape=list(other.shape),numpy_csv_exact=bool(np.array_equal(matrix,other)),finite=bool(np.isfinite(matrix).all()),
                             absent=['X27','X31'],original_33_variable_zero_variance_not_independently_testable=True),
                pinned_repository_tree=tree,preprocessing_code_in_pinned_tree=any(p.endswith(('.py','.ipynb','.m','.r','.R')) for p in tree),
                dataset_commits=git(benchmark,'log','--format=%H %s',BENCHMARK,'--','TenneseeEastman/datasetTE.csv').decode().splitlines(),
                official_archive=dict(url='https://depts.washington.edu/control/LARRY/TE/temexd_mod.zip',bytes=archive.stat().st_size,sha256=sha(archive.read_bytes()),
                    member_sha256={k:sha(v) for k,v in selected.items()},setpoints=setpoints,
                    solver=re.search(r'\bSolver\s+"([^"]+)"',text).group(1),
                    mdl_computed_version=re.search(r'ComputedModelVersion\s+"([^"]+)"',text).group(1),
                    c_declares_version_1_3_3=bool(re.search(r'Version\s+1\.3\.3',selected['temexd_mod.c'].decode('latin1'))),
                    Ts_base_hours=float(re.search(r'Ts_base\s*=\s*([0-9.]+)',init).group(1)),
                    Ts_save_hours=float(re.search(r'Ts_save\s*=\s*([0-9.]+)',init).group(1)),
                    initial_mat_overrides_literal_u0='load Mode1xInitial' in init,execution='NOT_RUN',
                    exact_manca_archive_byte_identity='UNKNOWN',redistribution='UNKNOWN; 원본 ZIP과 source는 Git에 반입하지 않음'),
                original_fortran_archive=dict(url='https://depts.washington.edu/control/LARRY/TE/tecode.zip',bytes=original_archive.stat().st_size,sha256=sha(original_archive.read_bytes()),execution='NOT_RUN'),
                candidate=dict(commit=git(candidate,'rev-parse','HEAD').decode().strip(),source_clean=not git(candidate,'status','--porcelain').strip(),controller_sha256=sha(controller),
                               previous_run_plan=plan,normal_initial=dict(list(csv.DictReader(io.StringIO((ROOT/'experiments/simulator/diagnostics/run_20261023_aligned/closed_normal_7200.csv').read_text())))[0])),
                matlab_command_on_path=shutil.which('matlab'),new_simulator_experiment='NOT_RUN')


def dump(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--benchmark-git',type=Path,required=True);p.add_argument('--modified-archive',type=Path,required=True);p.add_argument('--original-archive',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.mkdir(exist_ok=False,parents=True)
    dump(args.output/'local_audit.json',audit(args.benchmark_git,args.modified_archive,args.original_archive,args.candidate))
    dump(args.output/'pr4_asset_review.json',asset_review())
    dump(args.output/'SHA256.json',{p.name:sha(p.read_bytes()) for p in args.output.iterdir() if p.is_file()})
    print('[PASS] 고정 CSV/GT·NumPy identity·공식 모델 정적 배선·PR4 자산 크기/중복 감사; 신규 실험 없음')


if __name__=='__main__':main()
