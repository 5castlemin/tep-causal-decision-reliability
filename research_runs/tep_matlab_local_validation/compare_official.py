"""Descriptive comparison; does not validate simulator or mapping equivalence."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

EXPECTED='52ae445b4355201db9591822282381c8de861afe49bdbc9452db08b01e7d3711'

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--benchmark',type=Path,required=True)
    p.add_argument('--simulation',type=Path,required=True,help='CSV with time_hours and original X columns; mapping must be documented separately')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if hashlib.sha256(a.benchmark.read_bytes()).hexdigest()!=EXPECTED:
        raise ValueError('benchmark hash mismatch')
    if a.output.exists():
        raise FileExistsError('output must be new')
    ref=pd.read_csv(a.benchmark,index_col=0);sim=pd.read_csv(a.simulation)
    if ref.shape!=(1499,31) or 'time_hours' not in sim.columns or not set(ref.columns).issubset(sim.columns):
        raise ValueError('expected 1499x31 reference and simulation time_hours plus all X columns')
    if len(sim)<2 or not np.isfinite(sim[['time_hours',*ref.columns]].to_numpy(dtype=float)).all() or not (sim.time_hours.diff().dropna()>0).all():
        raise ValueError('need finite chronological output with at least two rows')
    rows=[]
    for col in ref.columns:
        row={'variable':col}
        for label,x in (('benchmark',ref[col]),('simulation',sim[col])):
            row.update({label+'_mean':x.mean(),label+'_sd':x.std(),label+'_median':x.median(),label+'_q05':x.quantile(.05),label+'_q95':x.quantile(.95),label+'_first':x.iloc[0],label+'_last':x.iloc[-1],label+'_lag1':x.autocorr()})
        rows.append(row)
    a.output.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(a.output/'COMPARISON_31.csv',index=False)
    for label,frame in (('benchmark',ref),('simulation',sim[ref.columns])):
        frame.corr().to_csv(a.output/(label+'_correlation.csv'))
    (a.output/'LIMITATIONS.json').write_text(json.dumps({'status':'DESCRIPTIVE_ONLY','simulation_sha256':hashlib.sha256(a.simulation.read_bytes()).hexdigest(),'scientific_mapping':'NOT_VERIFIED','time_and_preprocessing':'NOT_VERIFIED','independent_repeats':'NOT_VERIFIED','matched_environment':'NOT_ESTABLISHED'},indent=2),encoding='utf8')
    print('Descriptive statistics saved; matching has NOT been established.')

if __name__=='__main__':main()
