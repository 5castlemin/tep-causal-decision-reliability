"""Build the public SHA-256 inventory for the final integration change set."""
import hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'FINAL_RESEARCH_INTEGRATION_MANIFEST.json'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def main():
    tracked=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines()
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    paths=sorted(set(tracked+untracked+['research/budget_adaptive_repair/build_final_integration_manifest.py']))
    paths=[x for x in paths if x!='FINAL_RESEARCH_INTEGRATION_MANIFEST.json']
    files={p:sha(ROOT/p) for p in paths if (ROOT/p).is_file()}
    doc={
      'schema':'FINAL_RESEARCH_INTEGRATION_MANIFEST_V1',
      'as_of':'2026-11-28',
      'base_revision':'0c9236d7f8981d879d1fd47b517ef5dc0c19a7b1',
      'commit_binding':'This manifest is included in the same Git commit as the listed public files; the resulting commit SHA is the final revision binding.',
      'project_gate':'PROJECT_SCIENTIFIC_CORE_COMPLETED_WITH_LIMITATIONS',
      'research_e_extension':{'classification':'POST_HOC_DECISION_ECONOMIC_ANALYSIS','saved_unit_rows_reaggregated':16560,'new_scm':0,'new_g0':0,'new_observations':0,'new_drf_fits':0,'new_intervention_rows':0,'s4_s5_budgets_available':[0,1,2,3,4],'s4_s5_b5_to_b9':'NOT_RUN_NO_SEALED_UNIT_LEVEL_RESULTS','execution_lock':'research/budget_adaptive_repair/RESEARCH_E_EXTENSION_EXECUTION_LOCK.json','execution_manifest':'research/budget_adaptive_repair/outputs/final_extension_v1/execution_manifest.json'},
      'study_status':{'preliminary':'historical exploratory problem discovery, not manufacturing intervention validation','research_c':'frozen-contract confirmatory synthetic primary preserved','s1_s2':'post-hoc supplementary analyses','s3':'corrected exploratory historical analysis','s4':'80-SCM development and 160-SCM independent replication under stated Q-common population; limitations retained','research_d':'historical conditional semisynthetic; private unit-level artifacts unavailable to this extension','s5':'new conditional external semisynthetic reconstruction; one DGP and 200 G0 draws','research_e':'original C B0-9 extension retained; saved S4/S5 reaggregation B0-4'},
      'private_data_policy':'Raw ledgers, unit records, training data, recommendation rows, response vectors, fitted objects and private archives excluded from GitHub.',
      'backup_status':'S5 private archive is same-device only; no off-device backup is claimed.',
      'main_merge':'NOT_PERFORMED','pr_50':'UNCHANGED',
      'public_file_sha256':files
    }
    OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(files)} public files hashed; private paths excluded; manifest written.')
if __name__=='__main__': main()
