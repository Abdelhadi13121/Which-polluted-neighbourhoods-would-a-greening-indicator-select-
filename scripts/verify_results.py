"""Compare every archived numerical CSV with a new full reproduction."""
from pathlib import Path
import json,sys
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def verify():
    rows=[];failures=[]
    for expected in sorted((ROOT/'reference_results').rglob('*.csv')):
        rel=expected.relative_to(ROOT/'reference_results');actual=ROOT/'outputs'/rel
        if not actual.exists():failures.append(str(rel)+': missing');continue
        a=pd.read_csv(expected);b=pd.read_csv(actual)
        if list(a.columns)!=list(b.columns) or a.shape!=b.shape:failures.append(str(rel)+': schema or shape');continue
        bad=[];maxdiff=0.
        for col in a:
            if pd.api.types.is_numeric_dtype(a[col]) and pd.api.types.is_numeric_dtype(b[col]):
                aa=a[col].to_numpy(dtype=float);bb=b[col].to_numpy(dtype=float)
                if not np.allclose(aa,bb,rtol=1e-6,atol=1e-8,equal_nan=True):bad.append(col)
                finite=np.isfinite(aa)&np.isfinite(bb)
                if finite.any():maxdiff=max(maxdiff,float(np.max(abs(aa[finite]-bb[finite]))))
            elif not a[col].fillna('<NA>').astype(str).equals(b[col].fillna('<NA>').astype(str)):bad.append(col)
        rows.append(dict(file=str(rel).replace('\\','/'),rows=len(a),columns=len(a.columns),passed=not bad,max_abs_numeric_difference=maxdiff,failed_columns=bad))
        if bad:failures.append(str(rel)+': '+','.join(bad))
    result={'csv_files_checked':len(rows),'rtol':1e-6,'atol':1e-8,'passed':not failures,'failures':failures,'tables':rows}
    (ROOT/'outputs').mkdir(exist_ok=True);(ROOT/'outputs/reproduction_check.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='tables'},indent=2))
    if failures:raise RuntimeError('Reproduction comparison failed; see outputs/reproduction_check.json')
    return result
if __name__=='__main__':verify()
