import sys
sys.path.insert(0,'work/geolibs')
import pathlib,json,pickle,numpy as np,rasterio
from rasterio.transform import rowcol
w=pathlib.Path('work/panel');core=pickle.load(open('work/core.pkl','rb'));xs=np.array([r['x_3035'] for r in core]);ys=np.array([r['y_3035'] for r in core]);summaries=[]
def metric_name(pol,name):
 n=name.lower()
 if pol=='no2' and ('_avg_b.' in n or '_avg_ut.' in n):return None
 if '_3y' in n or '_5y' in n:return None
 if pol in ['pm25','pm10','no2'] and ('avg' in n or 'mean' in n):return pol+'_annual_ug_m3'
 if pol=='pm10' and ('p904' in n or 'p90' in n):return 'pm10_daily_p904_ug_m3'
 if pol=='pm10' and '36hd' in n:return 'pm10_daily_36th_highest_ug_m3'
 if pol=='o3':
  if 'somo35' in n or '_s35_' in n:return 'o3_somo35_ug_m3_days'
  if 'somo10' in n or '_s10_' in n:return 'o3_somo10_ug_m3_days'
  if 'p932' in n:return 'o3_mda8_p932_ug_m3'
  if '26hd' in n:return 'o3_mda8_26th_highest_ug_m3'
  if 'peak' in n:return 'o3_peak_season_ug_m3'
 return None
for mf in sorted(w.glob('*/manifest.json')):
 rec=json.loads(mf.read_text());dest=mf.parent/'sampled.npz';infofile=mf.parent/'sample_info.json'
 if dest.exists():summaries.extend(json.loads(infofile.read_text()));continue
 values={};infos=[]
 for filename in rec['tifs']:
  name=metric_name(rec['pollutant'],pathlib.Path(filename).name)
  if name is None:continue
  assert name not in values,(mf,name)
  with rasterio.open(filename) as ds:
   crs=ds.crs.to_dict();assert all(crs.get(k)==v for k,v in {'proj':'laea','lat_0':52,'lon_0':10,'x_0':4321000,'y_0':3210000,'ellps':'GRS80','units':'m'}.items()),(filename,crs)
   assert ds.count==1
   rr,cc=rowcol(ds.transform,xs,ys);rr=np.asarray(rr);cc=np.asarray(cc);inside=(rr>=0)&(rr<ds.height)&(cc>=0)&(cc<ds.width)
   arr=ds.read(1,masked=True);out=np.full(len(core),np.nan);out[inside]=arr[rr[inside],cc[inside]].filled(np.nan);out=out*ds.scales[0]+ds.offsets[0];out[(~np.isfinite(out))|(out<0)]=np.nan
   # Reject unexplained non-kilometre alignment rather than silently reassign cells.
   aligned=all(abs(v-round(v/1000)*1000)<0.01 for v in [ds.transform.c,ds.transform.f])
   assert aligned and abs(ds.res[0]-1000)<0.01 and abs(ds.res[1]-1000)<0.01,(filename,ds.transform,ds.res)
   values[name]=out
   info={'metric':name,'pollutant':rec['pollutant'],'year':rec['year'],'uuid':rec['uuid'],'source_key':f"{rec['pollutant']}_{rec['year']}",'interim':rec['interim'],'filename':pathlib.Path(filename).name,'native_resolution_m':ds.res[0],'valid_cells':int(np.isfinite(out).sum()),'min':float(np.nanmin(out)),'max':float(np.nanmax(out)),'scale':ds.scales[0],'offset':ds.offsets[0]};infos.append(info)
 np.savez_compressed(dest,**values);infofile.write_text(json.dumps(infos,indent=2));summaries.extend(infos);print(rec['pollutant'],rec['year'],[(i['metric'],i['valid_cells'],round(i['min'],2),round(i['max'],2)) for i in infos],flush=True)
(w/'sample_manifest.json').write_text(json.dumps(summaries,indent=2))
