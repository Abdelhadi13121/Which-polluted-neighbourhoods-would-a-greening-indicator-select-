from pip._vendor import truststore
truststore.inject_into_ssl()
import sys
sys.path.insert(0,'work/geolibs')
import urllib.request,urllib.parse,pathlib,json,concurrent.futures,numpy as np,rasterio
w=pathlib.Path('work');bounds=json.loads((w/'bounds.json').read_text())
def ua_check(city):
 results=[]
 for layer in [0,1,2]:
  data=json.loads((w/'ua_green'/f'{city}_{layer}.json').read_bytes());ids=[f['properties']['OBJECTID'] for f in data['features']];assert len(ids)==len(set(ids))
  q={'f':'json','where':"code_2018 = '14100'" if layer==2 else '1=1','geometry':','.join(map(str,bounds[city])),'geometryType':'esriGeometryEnvelope','inSR':3035,'outSR':3035,'spatialRel':'esriSpatialRelIntersects','returnCountOnly':'true'}
  url=f'https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/UrbanAtlas/UA_UrbanAtlas_2018/MapServer/{layer}/query?'+urllib.parse.urlencode(q)
  d=json.loads(urllib.request.urlopen(url,timeout=60).read());assert d['count']==len(ids),(city,layer,d,len(ids));results.append(d['count'])
 print('UA count verified',city,results,flush=True);return results
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:list(p.map(ua_check,bounds))
with rasterio.open(w/'tree_test.tif') as d:
 a=d.read(1);valid=(a<=100)&(d.read_masks(1)>0);direct=float(a[valid].mean()/100)
t=np.load(w/'tree_tiles'/'3720000_2840000.npz');tiled=float(t['mean'][9,30]);print('TREE single-cell',direct,'tiled',tiled,'difference',abs(direct-tiled),flush=True)
assert abs(direct-tiled)<1e-5
(w/'source_checks.json').write_text(json.dumps({'ua_all_counts_verified':True,'tree_direct':direct,'tree_tiled':tiled,'tree_difference':abs(direct-tiled)}))
