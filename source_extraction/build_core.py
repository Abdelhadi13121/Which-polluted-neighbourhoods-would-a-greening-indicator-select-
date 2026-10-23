import sys
sys.path.insert(0,'work/geolibs')
import pathlib,json,csv,math,pickle
import numpy as np,shapely,rasterio
from shapely.geometry import shape
w=pathlib.Path('work')
cities={'FR001F':'Paris','ES001F':'Madrid','ES002F':'Barcelona','IT002F':'Milan','IT001F':'Rome','DE001F':'Berlin','AT001F':'Vienna','NL001F':'Amsterdam','PL001F':'Warsaw','PT001F':'Lisbon'}
features={f['properties']['URAU_CODE']:f for f in json.loads((w/'fua.txt').read_bytes())['features'] if f['properties']['URAU_CODE'] in cities}
assert len(features)==10
rows=[];lookup={};bounds={};geoms={}
for code,city in cities.items():
 g=shape(features[code]['geometry']);assert g.is_valid
 geoms[city]=g
 a,b,c,d=g.bounds;a=math.floor(a/1000)*1000;b=math.floor(b/1000)*1000;c=math.ceil(c/1000)*1000;d=math.ceil(d/1000)*1000
 bounds[city]=[a,b,c,d]
 x,y=np.meshgrid(np.arange(a,c,1000),np.arange(b,d,1000));x=x.ravel();y=y.ravel();mask=shapely.contains_xy(g,x+500,y+500);x=x[mask];y=y[mask]
 overlap=shapely.area(shapely.intersection(shapely.box(x,y,x+1000,y+1000),g))/1e6
 for xx,yy,frac in zip(x,y,overlap):
  grid=f'CRS3035RES1000mN{yy}E{xx}'
  r={'city':city,'fua_code':code,'grid_id':grid,'year':2021,'epsg':3035,'x_3035':int(xx+500),'y_3035':int(yy+500),'cell_area_km2':1,'fua_cell_fraction':round(float(frac),6)}
  rows.append(r);lookup.setdefault(grid,[]).append(r)
 print(city,len(x),flush=True)
fields={'T':'population','M':'population_male','F':'population_female','Y_LT15':'population_under15','Y_1564':'population_15to64','Y_GE65':'population_65plus','EMP':'employed_persons','NAT':'birth_reporting_country','EU_OTH':'birth_other_eu_country','OTH':'birth_elsewhere','SAME':'residence_unchanged','CHG_IN':'residence_moved_within_country','CHG_OUT':'residence_moved_from_abroad'}
matched=set();unallocated={}
with (w/'census.csv').open(encoding='utf8',newline='') as f:
 for r in csv.DictReader(f):
  gid=r['GRD_ID']
  if gid.endswith('_unallocated'):unallocated[gid]=r
  if gid not in lookup:continue
  assert gid not in matched;matched.add(gid)
  for out in lookup[gid]:
   out['census_cell_status']='reported';out['census_countries']=r['CNTR_ID'];out['land_surface_km2']=float(r['LAND_SURFACE']) if float(r['LAND_SURFACE'])>=0 else None;out['populated_flag']=r['POPULATED']
   for source,dest in fields.items():
    val=int(r[source]);out[dest]=val if val>=0 else None;out[dest+'_status']='reported' if val>=0 else ('confidential' if val==-8888 else 'unavailable')
with rasterio.open(w/'pm.tif') as ds:
 crs=ds.crs.to_dict()
 assert all(crs.get(k)==v for k,v in {'proj':'laea','lat_0':52,'lon_0':10,'x_0':4321000,'y_0':3210000,'ellps':'GRS80','units':'m'}.items()) and ds.res==(1000,1000)
 assert abs(ds.transform.c-round(ds.transform.c/1000)*1000)<0.001
 assert abs(ds.transform.f-round(ds.transform.f/1000)*1000)<0.001
 vals=list(ds.sample([(r['x_3035'],r['y_3035']) for r in rows],masked=True))
 for r,v in zip(rows,vals):
  r['pm25_annual_ug_m3']=None if np.ma.is_masked(v[0]) else float(v[0]);r['pm25_status']='nodata' if r['pm25_annual_ug_m3'] is None else 'available';r['pm25_year']=2021
  if 'census_cell_status' not in r:r['census_cell_status']='absent_from_source'
  for num,out in [('population_under15','share_under15'),('population_65plus','share_65plus')]:
   r[out]=r.get(num)/r['population'] if r.get('population',0) and r.get(num) is not None else None
pickle.dump(rows,(w/'core.pkl').open('wb'));(w/'bounds.json').write_text(json.dumps(bounds));pickle.dump(geoms,(w/'geoms.pkl').open('wb'));(w/'unallocated.json').write_text(json.dumps(unallocated));(w/'selected_fua.geojson').write_text(json.dumps({'type':'FeatureCollection','features':list(features.values()),'crs':{'type':'name','properties':{'name':'EPSG:3035'}}}))
print('Rows',len(rows),'census matched',len(matched),'PM available',sum(r['pm25_status']=='available' for r in rows),flush=True)
