from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AUDIT=ROOT/'research/final_integration/research_e_audit'
EOUT=ROOT/'research/budget_adaptive_repair/outputs'
EBASE=ROOT/'research/budget_adaptive_repair'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 e=json.loads((AUDIT/'final_audit_summary.json').read_text(encoding='utf-8-sig'))
 files=[
  'research/final_integration/research_e_audit/final_audit_summary.json',
  'research/final_integration/research_e_audit/expanded_pareto_frontiers.csv',
  'research/final_integration/research_e_audit/expanded_lambda_lower_envelope.csv',
  'research/final_integration/research_e_audit/expanded_lambda_breakpoints.csv',
  'research/final_integration/research_e_audit/expanded_pareto_bootstrap_stability.csv',
  'research/final_integration/research_e_audit/reference_learner_summary.csv',
  'research/final_integration/research_e_audit/corrected_saturation_rates.csv',
  'research/final_integration/research_e_audit/adaptive_blocker_counts.csv',
  'research/final_integration/research_e_audit/figures/E9_expanded_pareto.svg',
  'research/final_integration/research_e_audit/figures/E10_lambda_lower_envelope.svg',
  'research/final_integration/RESEARCH_E_FINAL_AUDIT.md',
  'research/budget_adaptive_repair/final_audit.py',
  'research/budget_adaptive_repair/render_closeout_figures.py',
  'tests/test_research_e_final_audit.py',
  'research/budget_adaptive_repair/RESEARCH_E2_SATURATION_RESULTS.md',
  'research/budget_adaptive_repair/RESEARCH_E3_ADAPTIVE_POLICY_RESULTS.md',
  'research/budget_adaptive_repair/RESEARCH_E_FINAL_RESULTS.md',
  'research/budget_adaptive_repair/RESEARCH_E1_PARETO_AND_COST_ANALYSIS.md',
  'research/budget_adaptive_repair/RESEARCH_E_PRESENTATION_EVIDENCE_GUIDE.md',
  'README.md','RESEARCH_JOURNEY_AND_TEAM_HANDOFF.md',
  'research/final_integration/FINAL_RESEARCH_REPORT.md',
  'research/final_integration/FINAL_RESULTS_TABLES.md',
  'research/final_integration/FINAL_CLAIMS_EVIDENCE_MATRIX.md',
  'research/final_integration/FINAL_PRESENTATION_EVIDENCE_GUIDE.md',
  'research/final_integration/TEAM_CONTRIBUTION_AND_HANDOFF.md']
 payload={'schema':'research-e-final-closeout-manifest-v1','status':e['status'],'research_e_gate':e['research_e_gate'],'research_data_samples_generated':0,'protected_c_d_assets_modified':False,'original_e_integrity_manifest_sha256':sha(EBASE/'research_e_integrity_manifest.json'),'closeout_analysis_source_sha256':sha(EBASE/'final_audit.py'),'input_hash_match':e['input_sha256_match'],'original_e_source_hashes_all_match':all(e['source_sha256_checks'].values()),'original_e_public_aggregate_hashes_all_match':all(e['public_aggregate_sha256_checks'].values()),'original_e_figure_hashes_all_match':all(e['public_figure_sha256_checks'].values()),'local_only_unit_rows':{'c_extended':e['extended_unit_rows'],'adaptive_m4':e['adaptive_unit_rows'],'reference_learner':264,'target_sensitivity':19800},'paired_frontier_bootstrap':e['pareto'],'d_raw_response_reaudit':'NOT_RUN_RAW_ARTIFACTS_UNAVAILABLE; prior 27-check audit summary located and hash matched','files_sha256':{p:sha(ROOT/p) for p in files}}
 out=AUDIT/'research_e_final_audit_manifest.json'
 if out.exists():raise FileExistsError(f'refusing overwrite {out}')
 out.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps(payload,indent=2))
if __name__=='__main__':main()
