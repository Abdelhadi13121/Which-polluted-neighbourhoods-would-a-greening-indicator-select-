import sys
sys.path.insert(0,'work/geolibs')
import csv,json,pickle,pathlib,hashlib,zipfile,collections,math
import numpy as np
w=pathlib.Path('work/panel');out=pathlib.Path('outputs');core=pickle.load(open('work/core.pkl','rb'))
baseline=list(csv.DictReader(open(out/'european_urban_environment_health_1km.csv',encoding='utf8',newline='')))
assert len(core)==len(baseline)==79988
reference=np.array([r['pm25_status']=='available' for r in core]);pop=np.array([r.get('population') or 0 for r in core],dtype=float)
years=list(range(2010,2026));pols=['pm25','pm10','no2','o3'];N=len(core)
metric_order=['pm25_annual_ug_m3','pm10_annual_ug_m3','no2_annual_ug_m3','pm10_daily_p904_ug_m3','pm10_daily_36th_highest_ug_m3','o3_mda8_p932_ug_m3','o3_mda8_26th_highest_ug_m3','o3_somo35_ug_m3_days','o3_somo10_ug_m3_days','o3_peak_season_ug_m3']
data={};manifest=[]
for year in years:
 for pol in pols:
  folder=w/f'{pol}_{year}';assert (folder/'manifest.json').exists(),f'Missing {folder}'
  rec=json.loads((folder/'manifest.json').read_text());assert (folder/'sampled.npz').exists(),folder
  infos=json.loads((folder/'sample_info.json').read_text());rec['metrics']=infos;rec['source_key']=f'{pol}_{year}';manifest.append(rec)
  z=np.load(folder/'sampled.npz')
  for name in z.files:
   arr=z[name].copy();arr[~reference]=np.nan;data[(name,year)]=arr
metrics=[m for m in metric_order if any((m,y) in data for y in years)]
for m in ['pm25_annual_ug_m3','pm10_annual_ug_m3','no2_annual_ug_m3']:
 assert all((m,y) in data for y in years)
assert np.allclose(data[('pm25_annual_ug_m3',2021)][reference],[r['pm25_annual_ug_m3'] for r in core if r['pm25_status']=='available'])
fua=json.loads((w/'fua_population.json').read_text());fua_map={(r['fua_code'],r['year']):r for r in fua}
fua_cols=[k for k in fua[0] if k not in ['city','fua_code','year']]
ignore={'year','pm25_annual_ug_m3','pm25_status','pm25_year','tree_cover_share_2021','tree_status_2021','urban_green_share_2021','urban_atlas_status_2021','summer_lst_c_2021','lst_status_2021'}
stable={'city','fua_code','grid_id','epsg','x_3035','y_3035','cell_area_km2','fua_cell_fraction'}
rename={k:k if k in stable or k.endswith('_2018') else k+'_2021' for k in baseline[0] if k not in ignore}
base_cols=list(rename.values());annual_cols=['year','fua_boundary_year','census_reference_year','copernicus_baseline_year','within_reference_aq_coverage','aq_release_status']+metrics
annual_cols += [p+'_source_key' for p in pols]+[p+'_available' for p in pols]
delta_cols=[p+'_change_from_2021_ug_m3' for p in ['pm25','pm10','no2']]
fields=base_cols+annual_cols+delta_cols+fua_cols
assert len(fields)==len(set(fields))
dest=out/'european_urban_panel_2010_2025.csv';summary=[];coverage=[]
with dest.open('w',encoding='utf8',newline='') as file:
 writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader()
 for year in years:
  arrays={m:data.get((m,year),np.full(N,np.nan)) for m in metrics}
  for i,b in enumerate(baseline):
   r={rename[k]:b[k] for k in rename};r.update(year=year,fua_boundary_year=2021,census_reference_year=2021,copernicus_baseline_year=2018,within_reference_aq_coverage=int(reference[i]),aq_release_status='interim' if year==2025 else 'non_interim')
   for m,a in arrays.items():r[m]='' if not np.isfinite(a[i]) else format(float(a[i]),'.8g')
   for p in pols:
    r[p+'_source_key']=f'{p}_{year}';pm=[m for m in metrics if m.startswith(p+'_') and (m,year) in data];r[p+'_available']=int(any(np.isfinite(data[(m,year)][i]) for m in pm))
   for p in ['pm25','pm10','no2']:
    a=arrays[p+'_annual_ug_m3'][i];b21=data[(p+'_annual_ug_m3',2021)][i];r[p+'_change_from_2021_ug_m3']='' if not(np.isfinite(a) and np.isfinite(b21)) else format(float(a-b21),'.8g')
   r.update({k:fua_map[(r['fua_code'],year)][k] for k in fua_cols});writer.writerow(r)
  cov={'year':year,'rows':N,'release_status':'interim' if year==2025 else 'non_interim'};cov.update({m:int(np.isfinite(a).sum()) for m,a in arrays.items()});coverage.append(cov)
  for city in dict.fromkeys(r['city'] for r in core):
   cm=np.array([r['city']==city for r in core]);row={'city':city,'year':year,'grid_cells':int(cm.sum()),'reference_population_2021':int(pop[cm].sum()),'aq_release_status':cov['release_status']}
   for m,a in arrays.items():
    valid=cm&np.isfinite(a);wt=pop[valid];row[m+'_cells']=int(valid.sum());row[m+'_area_mean']=float(np.mean(a[valid])) if valid.any() else None;row[m+'_population_standardized_2021']=float(np.average(a[valid],weights=wt)) if wt.sum()>0 else None;row[m+'_population_coverage_fraction_2021']=float(wt.sum()/pop[cm].sum())
   code=next(r['fua_code'] for r in core if r['city']==city);row.update({k:fua_map[(code,year)][k] for k in fua_cols});summary.append(row)
  print('Wrote',year,flush=True)
def writecsv(path,rs):
 keys=list(dict.fromkeys(k for r in rs for k in r))
 with path.open('w',encoding='utf8',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=keys);wr.writeheader();wr.writerows(rs)
writecsv(out/'city_year_environment_summary.csv',summary);writecsv(out/'panel_coverage_by_year.csv',coverage)
public_manifest=[]
for rec in manifest:
 rec['metadata_url']='https://sdi.eea.europa.eu/catalogue/srv/api/records/'+rec['uuid']
 rec['retrieved_date']='2026-09-28'
 public_manifest.append({k:v for k,v in rec.items() if k not in ['tifs']})
(out/'panel_source_manifest.json').write_text(json.dumps(public_manifest,indent=2),encoding='utf8')
stats={'rows':N*len(years),'cells':N,'years':years,'columns':len(fields),'metrics':metrics,'coverage':coverage,'city_year_population_reported':sum(r['fua_population_annual'] is not None for r in fua),'sha256':hashlib.file_digest(dest.open('rb'),'sha256').hexdigest(),'bytes':dest.stat().st_size,'fields':fields}
(w/'build_stats.json').write_text(json.dumps(stats,indent=2))
print('BUILT',stats['rows'],stats['columns'],stats['bytes'],flush=True)
