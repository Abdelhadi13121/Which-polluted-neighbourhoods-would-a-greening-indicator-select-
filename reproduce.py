"""Restore data, run both analyses, regenerate figures and check reference tables."""
from pathlib import Path
import argparse,subprocess,sys,os,time,json,platform
ROOT=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-only',action='store_true',help='Restore and verify the two original CSVs only')
    args=p.parse_args();start=time.time()
    env=os.environ.copy();env['PYTHONUTF8']='1';env['OPENBLAS_NUM_THREADS']='2';env['OMP_NUM_THREADS']='2'
    def run(script):
        print('\nRunning',script,flush=True);subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,env=env,check=True)
    run('scripts/prepare_data.py')
    if args.data_only:return
    for script in ['src/paper_analysis.py','src/panel_extension.py','src/make_figures.py','scripts/verify_results.py']:run(script)
    import numpy,pandas,scipy,matplotlib
    result={'status':'passed','duration_seconds':round(time.time()-start,1),'python':platform.python_version(),'platform':platform.platform(),'packages':{m.__name__:m.__version__ for m in [numpy,pandas,scipy,matplotlib]},'bootstrap_draws':1000,'seed':20260930,'mode':'full','notes':'CSV numerical tables compared against archived references; figure files regenerated.'}
    (ROOT/'outputs/run_summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
