"""Build public evidence from local read-only probes; omit private paths/tokens."""
import argparse
import hashlib
import json
from pathlib import Path

from track_a_gate import evaluate

ROOT=Path(__file__).resolve().parents[1]


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p,data):
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def collect(local,out):
    out.mkdir(exist_ok=False,parents=True)
    env=read(local/'MATLAB_환경탐색_원시기록.json')
    extra=read(local/'MATLAB_보완탐색.json')
    static=read(local/'공식모델_원본무결성과_정적설정.json')
    doi=read(local/'datacite_record.json')['data']['attributes']
    search=read(local/'신규파일명단서_로컬탐색.json')
    engine={k:False for k in ['matlab_invocable','simulink_available','license_available','model_load_verified','mex_compatible']}
    engine.update(boolean_semantics='false는 미검증을 뜻하며 설치/권리의 전역 부재를 뜻하지 않음',
        registry_roots_checked=len(env['registry']),registry_mathworks_matches=sum(x['exists'] for x in env['registry']),
        registered_products=len(env['registered_products']),installation_paths_checked=len(env['filesystem']),
        installation_path_matches=sum(x['exists'] for x in env['filesystem']),matlab_shortcut_matches=len(extra['matlab_shortcuts']),
        app_path_registry_matches=sum([extra['app_path_HKLM'],extra['app_path_HKCU']]),active_matlab_processes=len(env['running_matlab']),
        path_commands={x['name']:bool(x['path']) for x in env['commands']},license_test_status='NOT_RUN',
        simulink_ver_status='NOT_RUN',mdl_load_status='NOT_RUN',mex_build_status='NOT_RUN',
        search_scope='PATH, MathWorks registry, uninstall records, C/D 일반 설치경로, Start Menu, App Paths. 전체 디스크/원격 환경 전수 아님.')
    evidence=dict(protocol='TRACK-A-RECOVERY-GATE-v1',checked_at=env['checked_at'],
        base_main='7b166383d4a5d86cdf73dbbec3b060b0ee0e3a24',
        source_hashes={n:static[n]['sha256'] for n in ['temexd_mod.zip','tecode.zip']},
        official_archives_unchanged=all(static[n]['unchanged'] for n in ['temexd_mod.zip','tecode.zip']),
        dataset_listing=dict(status='VERIFIED_METADATA_ONLY',
            landing_url='https://ieee-dataport.org/open-access/tennessee-eastman-process-alarm-management-dataset',
            landing_http_status=200,landing_sha256=sha(local/'dataport_landing.html'),
            raw_package='3_Normal Steady-State.zip',displayed_size='61.88 MB',download_access='LOGIN_REQUIRED',
            raw_package_sha256=None,license_reported_by_datacite=doi['rightsList'],
            doi_metadata_url='https://api.datacite.org/dois/10.21227/326k-qr90',
            doi_metadata_sha256=sha(local/'datacite_record.json'),normal_package_inventory='UNKNOWN'),
        technical_report=dict(status='RETRIEVED_DOCUMENT_NOT_RAW_DATA',file_name='Technical_Report_V1_2.pdf',
            sha256=sha(local/'Technical_Report_V1_2.pdf'),bytes=(local/'Technical_Report_V1_2.pdf').stat().st_size,pages=55,
            source_page='https://ieee-dataport.org/open-access/tennessee-eastman-process-alarm-management-dataset',
            pdf_page_to_printed_page={'12':'10','13':'11','14':'12','42':'40'},
            documented_filenames=['SIMOUT.xlsx','XMV.xlsx','TOUT.xlsx','ALARMS.xlsx','random_seed.txt'],
            file_layout_scope='Table2.1/Figure6.2는 측정 명세 및 Tests 폴더이다. 정상 ZIP 내부 구성의 검증이 아님.',
            model_flag_bits_reported={'0':1,'1':0,'2':0,'3':0,'4':0,'5':1,'6':1,'7':1,'15':0},
            model_flag_decimal_inferred=225,report_queried_not_manca_runtime_verified=True),
        raw_data=dict(acquired=False,timestamp_acquired=False,seed_acquired=False,export_reproduced=False,
            configuration_matched=False,documented_time_file='TOUT.xlsx',documented_seed_file='random_seed.txt',
            actual_timestamp_status='UNKNOWN',actual_seed_status='UNKNOWN',median_stride_boundary_status='UNKNOWN',
            row_1500_1499_cause='UNKNOWN',targeted_local_file_search_count=search['names_examined'],
            targeted_local_exact_name_matches=len(search['matches'])),
        execution_environment=engine,static_model=static,normal_runs=[],repeatability_verified=False,
        intervention_interface_verified=False,
        levels={'L1':dict(status='VERIFIED',scope='문서·코드의 이름/선언 단위 대응만'),
                'L2':dict(status='PARTIAL',scope='공식 설정값·문서 운전점과 평균 근접; 공식 모델 실행 없음'),
                'L3':dict(status='PARTIAL',scope='수정 모델 계열/버전 확보; 실제 원자료 실행 바이너리 동일성 미확인'),
                'L4':dict(status='PARTIAL',scope='정적 controller wiring만; do/setpoint/override 의미 미검증'),
                'L5':dict(status='UNKNOWN',scope='실제 초기상태/seed/noise/export 연결 미확인'),
                'L6':dict(status='NOT_RUN',scope='A2 차단으로 정상 반복 실행 없음'),
                'L7':dict(status='BLOCKED',scope='개입 효과 정답 활용 NO-GO')},
        no_new_discovery_or_scm=True,research_design_changed=False,external_contact_sent=False)
    evidence['gate_decision']=evaluate(evidence)
    dump(out/'gate_evidence.json',evidence)
    dump(out/'source_access.json',dict(access_records=read(local/'원자료_접근기록.json'),
        pdf_document_access=read(local/'기술보고서_접근기록_v2.json'),
        note='정상 ZIP은 목록 확인뿐. 임시 서명 URL과 raw HTML 및 로컬 개인 경로는 Git 반입하지 않음.'))
    dump(out/'SHA256.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
    print(evidence['gate_decision'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--local-records',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'docs/research_design/track_a_evidence')
    args=p.parse_args();collect(args.local_records,args.output)
