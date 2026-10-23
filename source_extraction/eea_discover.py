from pip._vendor import truststore
truststore.inject_into_ssl()
import urllib.request,pathlib,json,base64
urls=[('direct','https://sdi.eea.europa.eu/data/c0ca09a4-d9fe-4772-bc48-90cf31639442'),('listing','https://sdi.eea.europa.eu/webdav/datastore/public/eea_r_3035_1_km_aq-interpolated-pm25_p_2021_v01_r00/')]
for k,u in urls:
 try:
  r=urllib.request.urlopen(u,timeout=45);b=r.read();pathlib.Path('work/'+k+'.html').write_bytes(b);print(k,r.url,r.status,len(b),flush=True)
 except Exception as e:print(k,e,flush=True)
f=json.loads(pathlib.Path('work/fua.txt').read_text())
names=['Paris','Madrid','Barcelona','Milano','Roma','Berlin','Wien','Amsterdam','Warszawa','Lisboa']
for x in f['features']:
 if any(n.lower() in str(x['properties']).lower() for n in names):print(x['properties'],flush=True)
