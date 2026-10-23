from pip._vendor import truststore
truststore.inject_into_ssl()
import urllib.request,json,pathlib,concurrent.futures
root=pathlib.Path('work');root.mkdir(exist_ok=True)
urls={
'fua':'https://gisco-services.ec.europa.eu/distribution/v2/urau/geojson/URAU_RG_100K_2021_3035_FUA.geojson',
'census':'https://gisco-services.ec.europa.eu/census/2021/',
'eea':'https://sdi.eea.europa.eu/catalogue/datahub/api/records/c0ca09a4-d9fe-4772-bc48-90cf31639442',
'pmfiles':'https://sdi.eea.europa.eu/data/c0ca09a4-d9fe-4772-bc48-90cf31639442/'
}
def fetch(item):
 k,u=item
 try:
  r=urllib.request.urlopen(u,timeout=60);b=r.read();(root/(k+'.txt')).write_bytes(b);print(k,r.status,len(b),b[:100],flush=True)
 except Exception as e:print(k,str(e),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(fetch,urls.items()))
