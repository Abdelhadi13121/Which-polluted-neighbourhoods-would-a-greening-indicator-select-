import sys
sys.path.insert(0,'work/geolibs')
import json,pathlib,zipfile,rasterio
w=pathlib.Path('work')
for archive in ['pm','census']:
 z=zipfile.ZipFile(w/(archive+'.zip'))
 for name in z.namelist():
  if archive=='pm' and (name.endswith('.tif') or name.endswith('README.md')): (w/('pm.tif' if name.endswith('.tif') else 'pm_readme.md')).write_bytes(z.read(name))
  if archive=='census' and (name.endswith('_V3.csv') or name.endswith('read.me')):
   out=w/('census.csv' if name.endswith('.csv') else 'census_readme.txt')
   with z.open(name) as s,out.open('wb') as f:
    import shutil;shutil.copyfileobj(s,f)
print((w/'census_readme.txt').read_text(),flush=True)
with (w/'census.csv').open() as f:print([next(f) for _ in range(3)],flush=True)
with rasterio.open(w/'pm.tif') as r:print(r.profile,flush=True)
print([(x['properties']['URAU_CODE'],x['properties']['URAU_NAME']) for x in json.loads((w/'fua.txt').read_bytes())['features'] if x['properties']['URAU_CODE']=='PL001F'])
for n in ['ua','lst']:
 d=json.loads((w/(n+'_api.json')).read_bytes());print(n,{k:v for k,v in d.items() if k in ['downloadable_files','download_other_ways_access_dataset','dataset_download_information','mapviewer_viewservice','metadata_rest_api_url','downloadable_full_dataset']},flush=True)
