from pip._vendor import truststore
truststore.inject_into_ssl()
import urllib.request,pathlib,json,concurrent.futures
urls={
'ua_api':'https://land.copernicus.eu/++api++/en/products/urban-atlas/urban-atlas-2021',
'tcd_api':'https://land.copernicus.eu/++api++/en/products/high-resolution-layer-forests-and-tree-cover/tree-cover-density-2021-raster-10-m-europe-yearly',
'lst_api':'https://land.copernicus.eu/++api++/en/products/temperature-and-reflectance/hourly-land-surface-temperature-global-v1-0-5km',
'ua_services':'https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/UrbanAtlas?f=pjson',
'gio_services':'https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic?f=pjson'}
def fetch(kv):
 k,u=kv
 try:
  r=urllib.request.urlopen(urllib.request.Request(u,headers={'Accept':'application/json'}),timeout=50);b=r.read();pathlib.Path('work/'+k+'.json').write_bytes(b);d=json.loads(b);print(k,str(d)[:10000] if 'services' in k else str(list(d)),flush=True)
 except Exception as e:print(k,e,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(fetch,urls.items()))
