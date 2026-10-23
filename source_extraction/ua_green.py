from pip._vendor import truststore
truststore.inject_into_ssl()
import urllib.request,urllib.parse,json,pathlib,concurrent.futures,time
w=pathlib.Path('work');out=w/'ua_green';out.mkdir(exist_ok=True);bounds=json.loads((w/'bounds.json').read_text())
base='https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/UrbanAtlas/UA_UrbanAtlas_2018/MapServer/'
def task(city):
 bbox=','.join(map(str,bounds[city]))
 for layer in [0,1,2]:
  target=out/f'{city}_{layer}.json'
  if target.exists():continue
  features=[];offset=0
  while True:
   params={'f':'geojson','where':"code_2018 = '14100'" if layer==2 else '1=1','geometry':bbox,'geometryType':'esriGeometryEnvelope','inSR':3035,'outSR':3035,'spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'true','resultOffset':offset,'resultRecordCount':1000,'orderByFields':'OBJECTID'}
   for retry in range(2):
    try:
     d=json.loads(urllib.request.urlopen(base+str(layer)+'/query?'+urllib.parse.urlencode(params),timeout=90).read())
     if 'features' not in d:raise ValueError(str(d)[:250])
     break
    except Exception as e:
     print('retry',city,layer,str(e)[:150],flush=True)
     if retry==1:return False
   batch=d['features'];features.extend(batch);offset+=len(batch)
   if not batch or (len(batch)<1000 and not d.get('exceededTransferLimit',False)):break
  target.write_text(json.dumps({'type':'FeatureCollection','features':features}),encoding='utf8');print('UA',city,layer,len(features),flush=True)
 return True
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(task,bounds))
