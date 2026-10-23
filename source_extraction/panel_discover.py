from pip._vendor import truststore
truststore.inject_into_ssl()
import urllib.request,pathlib,re,json,concurrent.futures
w=pathlib.Path('work/panel');w.mkdir(exist_ok=True)
urls={'series':'https://www.eea.europa.eu/en/datahub/datahubitem-view/938bea70-07fc-47e9-8559-8a09f7f92494','pm_series_meta':'https://sdi.eea.europa.eu/catalogue/datahub/api/records/938bea70-07fc-47e9-8559-8a09f7f92494','no2_series':'https://www.eea.europa.eu/en/datahub/datahubitem-view/34bd02bf-be87-4122-b9a2-1e846c27a786','pm10_series':'https://www.eea.europa.eu/en/datahub/datahubitem-view/abc66a42-b595-4e0f-9772-b862dc454e9f'}
def get(kv):
 k,u=kv
 try:
  b=urllib.request.urlopen(u,timeout=60).read();(w/(k+'.txt')).write_bytes(b);print(k,len(b),flush=True)
 except Exception as e:print(k,e,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:list(p.map(get,urls.items()))
