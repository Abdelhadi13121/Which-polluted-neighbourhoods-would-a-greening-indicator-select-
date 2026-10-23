from pip._vendor import truststore
truststore.inject_into_ssl()
import urllib.request,urllib.parse,json,pathlib,concurrent.futures
w=pathlib.Path('work');bounds=json.loads((w/'bounds.json').read_text());base='https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/UrbanAtlas/UA_UrbanAtlas_2018/MapServer/2/query'
def task(city):
 b=bounds[city];params={'f':'json','where':'1=1','geometry':','.join(map(str,b)),'geometryType':'esriGeometryEnvelope','inSR':3035,'spatialRel':'esriSpatialRelIntersects','returnCountOnly':'true'}
 try:
  d=json.loads(urllib.request.urlopen(base+'?'+urllib.parse.urlencode(params),timeout=45).read());print(city,d,flush=True)
 except Exception as e:print(city,str(e),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:list(p.map(task,['Paris','Lisbon']))
