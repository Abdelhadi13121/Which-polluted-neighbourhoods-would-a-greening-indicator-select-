"""European urban green-indicator and pollution screening paper.
Requires Python 3.10+ and NumPy (tested with 2.3.5).
Run: python paper_analysis.py
Optional: python paper_analysis.py --output PATH
Reads data/paper_dataset.csv from the repository root. Creates results on execution.
Dataset: fixed 2021 FUA grid, EPSG:3035; population 2021; environment 2018.
All 79,988 source grid rows retained to preserve exclusions and aggregation.
The main common inhabited sample is 7,833 cells. Missing fields are not zeros.
Population is contextual; associations and resampling are not causal effects.
Sources: Eurostat Census/GISCO; EEA 2018 annual pollution maps;
Copernicus HRL Tree Cover Density 2018 and Urban Atlas 2018 class 14100.
Exploratory analysis; no preregistration or guaranteed publication claim.
"""
from pathlib import Path
import argparse
import numpy as np
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'outputs'/'original_script')
args=parser.parse_args()
DATASET=Path(__file__).resolve().parents[1]/'data'/'paper_dataset.csv'
RESULTS=args.output.resolve()
RESULTS.mkdir(parents=True,exist_ok=True)

def estimate_main():
    """Exploratory spatial decision analysis; run from project root. NumPy only."""
    import csv, json, hashlib, sys
    from pathlib import Path
    from collections import defaultdict
    import numpy as np
    
    OUT=RESULTS
    SEED=20260930; B=1000
    rows=list(csv.DictReader(open(DATASET,encoding='utf8')))
    def col(k): return np.array([float(r[k]) if r[k] else np.nan for r in rows])
    city=np.array([r['city'] for r in rows]); pop=col('population'); tree=col('tree_cover_share_2018'); green=col('urban_green_share_2018'); cover=col('tree_valid_area_fraction_2018'); x=col('x_3035'); y=col('y_3035')
    aq={p:col(p+'_annual_ug_m3_2018') for p in ['no2','pm25','pm10']}
    def save(name,rr):
        with (OUT/name).open('w',newline='',encoding='utf8') as f:
            w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rr for k in r))); w.writeheader(); w.writerows(rr)
    def alloc(v,k):
        cut=np.sort(v)[k-1]; forced=v<cut; tied=v==cut; remaining=k-int(forced.sum())
        a=forced.astype(float)+tied*remaining/tied.sum()
        assert abs(a.sum()-k)<1e-8
        return a,forced,tied,remaining
    def bounds(v,k,z):
        a,f,t,r=alloc(v,k); zz=np.sort(z[t]); fixed=z[f].sum()
        return float(fixed+zz[:r].sum()),float(fixed+zz[-r:].sum())
    def estimate(T,G,P,Q,q=.75,b=.2,slots=None):
        idx=np.flatnonzero(Q>=np.quantile(Q,q)); k=int(len(idx)*b) if slots is None else slots
        if k<5: return None,None
        T,G,P,Q=[v[idx] for v in [T,G,P,Q]]
        a,_,_,_=alloc(T,k); c,_,_,_=alloc(G,k)
        overlap=float(a@c/k); base=k/len(idx)
        out=dict(eligible=len(idx),slots=k,overlap=overlap,replacement=1-overlap,chance_adjusted_overlap=(overlap-base)/(1-base),canopy_population=float(a@P),green_population=float(c@P),population_difference=float((a-c)@P),canopy_mean_pollution=float(a@Q/k),green_mean_pollution=float(c@Q/k),pollution_difference=float((a-c)@Q/k))
        lo,hi=bounds(G,k,P); out.update(green_population_tie_min=lo,green_population_tie_max=hi)
        if np.all((a==0)|(a==1)):
            lo,hi=bounds(G,k,a);out.update(overlap_tie_min=lo/k,overlap_tie_max=hi/k)
        return out,(idx,a,c)
    
    primary=[]; boot=[]; detail=[]; matched=[]; deletion=[]; associations=[]
    for ci,ct in enumerate(dict.fromkeys(city)):
        mask=(city==ct)&(pop>0)&np.isfinite(tree)&np.isfinite(green)&(cover>=.95)
        mask &= np.logical_and.reduce([np.isfinite(v) for v in aq.values()])
        ids=np.flatnonzero(mask); T,G,P=tree[ids],green[ids],pop[ids]
        for pol in aq:
            Q=aq[pol][ids]; est,sel=estimate(T,G,P,Q);primary.append(dict(city=ct,pollutant=pol,**est))
            idx,a,c=sel
            for j,u in enumerate(idx):detail.append(dict(city=ct,pollutant=pol,grid_id=rows[ids[u]]['grid_id'],x_3035=x[ids[u]],y_3035=y[ids[u]],population_2021=P[u],pollution_2018=Q[u],tree_share_2018=T[u],ua_green_share_2018=G[u],canopy_selection_probability=a[j],green_selection_probability=c[j]))
            # Paired spatial block bootstrap: empirical geographic resampling, not source-error CIs.
            for km in [5,10]:
                keys=np.column_stack((np.floor(x[ids]/(km*1000)),np.floor(y[ids]/(km*1000))))
                _,inv=np.unique(keys,axis=0,return_inverse=True); blocks=[np.flatnonzero(inv==j) for j in range(inv.max()+1)]
                rng=np.random.default_rng(SEED+ci*100+km+list(aq).index(pol)*10000); draws=[]
                for rep in range(B):
                    ii=np.concatenate([blocks[j] for j in rng.integers(0,len(blocks),len(blocks))]); e,_=estimate(T[ii],G[ii],P[ii],Q[ii])
                    if e:draws.append([e[k] for k in ['replacement','chance_adjusted_overlap','population_difference','pollution_difference']])
                z=np.array(draws)
                for j,metric in enumerate(['replacement','chance_adjusted_overlap','population_difference','pollution_difference']):
                    lo,hi=np.quantile(z[:,j],[.025,.975]);boot.append(dict(city=ct,pollutant=pol,block_km=km,blocks=len(blocks),draws=len(z),metric=metric,estimate=est[metric],spatial_resampling_p025=lo,spatial_resampling_p975=hi,adequate_blocks=int(len(blocks)>=20)))
                # Leave one entire spatial block out; thresholds re-estimated.
                vals=[]
                for j in range(len(blocks)):
                    ii=inv!=j;e,_=estimate(T[ii],G[ii],P[ii],Q[ii])
                    if e:vals.append(e['replacement'])
                deletion.append(dict(city=ct,pollutant=pol,block_km=km,blocks=len(blocks),replacement_min=min(vals),replacement_max=max(vals)))
        # Matched footprint and identical area budget: all four children inhabited/valid.
        for ox,oy in [(0,0),(1,0),(0,1),(1,1)]:
            groups=defaultdict(list)
            for i in ids:groups[(int((x[i]-ox*1000)//2000),int((y[i]-oy*1000)//2000))].append(i)
            groups=[v for v in groups.values() if len(v)==4]
            flat=np.array(groups).ravel()
            for pol in aq:
                if not groups:continue
                block_q=np.array([aq[pol][g].mean() for g in groups])
                k2=int(np.sum(block_q>=np.quantile(block_q,.75))*.2)
                if k2<5:continue
                for resolution in [1,2]:
                    if resolution==1:tt,gg,pp,qq=tree[flat],green[flat],pop[flat],aq[pol][flat]
                    else:tt,gg,pp,qq=[np.array([v[g].sum() if k==2 else v[g].mean() for g in groups]) for k,v in enumerate([tree,green,pop,aq[pol]])]
                    e,_=estimate(tt,gg,pp,qq,slots=k2*4 if resolution==1 else k2)
                    if e:matched.append(dict(city=ct,pollutant=pol,offset_x_km=ox,offset_y_km=oy,resolution_km=resolution,footprint_km2=len(flat),population_2021=float(pop[flat].sum()),**e))
        print(ct,'complete',flush=True)
    save('primary_estimates.csv',primary);save('spatial_resampling.csv',boot);save('selected_cell_audit.csv',detail);save('matched_footprint.csv',matched);save('leave_block_out.csv',deletion)
    summary={'seed':SEED,'bootstrap_draws_per_setting':B,'primary_models':len(primary),'bootstrap_rows':len(boot),'matched_footprint_rows':len(matched),'numpy_version':np.__version__}
    summary['no2_equal_city_mean_replacement']=float(np.mean([r['replacement'] for r in primary if r['pollutant']=='no2']))
    summary['no2_leave_city_out_mean_range']=[float(min(np.mean([r['replacement'] for r in primary if r['pollutant']=='no2' and r['city']!=ct]) for ct in dict.fromkeys(city))),float(max(np.mean([r['replacement'] for r in primary if r['pollutant']=='no2' and r['city']!=ct]) for ct in dict.fromkeys(city)))]
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary),flush=True)


def estimate_associations():
    """Supplementary descriptive associations, not causal effects."""
    import csv,json
    from pathlib import Path
    import numpy as np
    OUT=RESULTS
    rs=list(csv.DictReader(open(DATASET,encoding='utf8')))
    def col(k):return np.array([float(r[k]) if r[k] else np.nan for r in rs])
    c=np.array([r['city'] for r in rs]);p=col('population');t=col('tree_cover_share_2018');g=col('urban_green_share_2018');x=col('x_3035');y=col('y_3035');v=col('tree_valid_area_fraction_2018')
    aq={pol:np.array([float(r[pol+'_annual_ug_m3_2018']) if r[pol+'_annual_ug_m3_2018'] else np.nan for r in rs]) for pol in ['no2','pm25','pm10']}
    m=(p>0)&np.isfinite(t)&np.isfinite(g)&(v>=.95)&np.logical_and.reduce([np.isfinite(z) for z in aq.values()]);c,p,t,g,x,y=[z[m] for z in [c,p,t,g,x,y]]
    cities=list(dict.fromkeys(c));D=np.column_stack([c==ct for ct in cities]).astype(float)
    X0=np.column_stack([t/.1,g/.1,np.log(p),D]);sp=[]
    for ct in cities:
     k=c==ct;xx=(x-x[k].mean())/10000;yy=(y-y[k].mean())/10000
     sp.extend([k*xx,k*yy,k*xx*xx,k*yy*yy,k*xx*yy])
    out=[]
    for pol,z in aq.items():
     Y=z[m]
     for name,X in [('city_FE',X0),('city_FE_city_quadratic_spatial_trends',np.column_stack([X0,*sp]))]:
      coef=np.linalg.lstsq(X,Y,rcond=None)[0];res=Y-X@coef;bread=np.linalg.pinv(X.T@X);n,k=X.shape
      for km in [5,10]:
       keys=[(ct,int(xx//(km*1000)),int(yy//(km*1000))) for ct,xx,yy in zip(c,x,y)];lookup={z:i for i,z in enumerate(dict.fromkeys(keys))};inv=np.array([lookup[z] for z in keys]);ng=len(lookup)
       score=np.zeros((ng,k));np.add.at(score,inv,X*res[:,None]);cov=bread@(score.T@score)@bread*(ng/(ng-1))*((n-1)/(n-k));se=np.sqrt(np.maximum(np.diag(cov),0))
       for j,term in enumerate(['canopy_per_10_percentage_points','ua_green_per_10_percentage_points','log_population_2021']):out.append(dict(pollutant=pol,model=name,term=term,coefficient_ug_m3=coef[j],spatial_cluster_se=se[j],block_km=km,clusters=ng,n=n,design_rank=int(np.linalg.matrix_rank(X)),design_columns=k,r_squared=1-res@res/np.sum((Y-Y.mean())**2)))
    with (OUT/'adjusted_associations.csv').open('w',newline='') as f:
     w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print(json.dumps([r for r in out if r['pollutant']=='no2' and r['block_km']==10]))


def estimate_robustness():
    import sys
    
    import numpy as np,csv,pathlib,json,math
    p=RESULTS
    rs=list(csv.DictReader(open(DATASET,encoding='utf8')))
    pop=np.array([float(r['population']) if r['population'] else np.nan for r in rs]);tree=np.array([float(r['tree_cover_share_2018']) if r['tree_cover_share_2018'] else np.nan for r in rs]);green=np.array([float(r['urban_green_share_2018']) if r['urban_green_share_2018'] else np.nan for r in rs]);coverage=np.array([float(r['tree_valid_area_fraction_2018']) if r['tree_valid_area_fraction_2018'] else np.nan for r in rs]);city=np.array([r['city'] for r in rs])
    aq={pol:np.array([float(r[pol+'_annual_ug_m3_2018']) if r[pol+'_annual_ug_m3_2018'] else np.nan for r in rs]) for pol in ['no2','pm25','pm10']}
    
    from collections import defaultdict
    x=np.array([float(r['x_3035']) for r in rs]);y=np.array([float(r['y_3035']) for r in rs])
    def allocation(a,k):
     v=np.sort(a)[k-1];f=a<v;t=a==v;r=k-int(f.sum())
     return f.astype(float)+t*r/t.sum(),f,t,r
    results=[];samples=[]
    for ct in dict.fromkeys(city):
     valid=(city==ct)&np.isfinite(tree)&np.isfinite(green)&(coverage>=.95)&np.isfinite(pop)
     ii=np.flatnonzero(valid)
     for scale,ox,oy in [(1,0,0),(2,0,0),(2,1,0),(2,0,1),(2,1,1)]:
      groups=defaultdict(list)
      for i in ii: groups[(int(np.floor((x[i]-ox*1000)/(scale*1000))),int(np.floor((y[i]-oy*1000)/(scale*1000))))].append(i)
      groups=[v for v in groups.values() if len(v)==scale*scale and pop[v].sum()>0]
      if not groups:continue
      T=np.array([tree[v].mean() for v in groups]);G=np.array([green[v].mean() for v in groups]);P=np.array([pop[v].sum() for v in groups])
      samples.append(dict(city=ct,scale_km=scale,offset_x_km=ox,offset_y_km=oy,cells=len(groups),population_2021=float(P.sum())))
      for pol in aq:
       Q=np.array([aq[pol][v].mean() for v in groups])
       for q in [.5,.75,.9]:
        threshold=np.quantile(Q[np.isfinite(Q)],q);idx=np.flatnonzero(np.isfinite(Q)&(Q>=threshold))
        for b in [.1,.2,.3]:
         k=int(np.floor(len(idx)*b))
         if k<5:
          results.append(dict(city=ct,scale_km=scale,offset_x_km=ox,offset_y_km=oy,pollutant=pol,high_pollution_quantile=q,budget_fraction=b,eligible_cells=len(idx),slots=k,status='fewer_than_5_slots'))
          continue
         pt,ft,tt,rt=allocation(T[idx],k);pg,fg,tg,rg=allocation(G[idx],k)
         fixed=np.all((pt==0)|(pt==1));lo=hi=None
         if fixed:
          A=pt==1;z=int((A&fg).sum());lo=(z+max(0,rg-int((tg&~A).sum())))/k;hi=(z+min(rg,int((tg&A).sum())))/k
         results.append(dict(city=ct,scale_km=scale,offset_x_km=ox,offset_y_km=oy,pollutant=pol,high_pollution_quantile=q,budget_fraction=b,eligible_cells=len(idx),slots=k,status='ok',expected_overlap=float(pt@pg/k),minimum_overlap=lo,maximum_overlap=hi,canopy_population_2021=float(pt@P[idx]),green_population_2021=float(pg@P[idx]),canopy_mean_no2=float(pt@np.array([aq['no2'][v].mean() for v in groups])[idx]/k),green_mean_no2=float(pg@np.array([aq['no2'][v].mean() for v in groups])[idx]/k)))
    def write(name,rr):
     keys=list(dict.fromkeys(k for r in rr for k in r))
     with (p/name).open('w',newline='',encoding='utf8') as f:
      w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rr)
    write('robustness_all.csv',results);write('scale_coverage.csv',samples)
    ok=[r for r in results if r['status']=='ok']
    summary={'specifications':len(results),'usable':len(ok),'skipped':len(results)-len(ok),'common_1km_cells':sum(r['cells'] for r in samples if r['scale_km']==1),'common_population':sum(r['population_2021'] for r in samples if r['scale_km']==1)}
    for s in [1,2]:
     z=[r['expected_overlap'] for r in ok if r['scale_km']==s]
     summary[str(s)+'km']={'n':len(z),'median_overlap':float(np.median(z)),'min':min(z),'max':max(z),'share_overlap_below_half':float(np.mean(np.array(z)<.5))}
    (p/'robustness_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary))
    print(json.dumps([r for r in ok if r['scale_km']==2 and r['pollutant']=='no2' and r['high_pollution_quantile']==.75 and r['budget_fraction']==.2]))


if __name__=='__main__':
    estimate_main()
    estimate_associations()
    estimate_robustness()
    print('Results saved to',RESULTS)
