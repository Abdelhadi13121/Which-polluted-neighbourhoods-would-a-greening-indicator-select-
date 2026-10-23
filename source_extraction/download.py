from pip._vendor import truststore
truststore.inject_into_ssl()
import urllib.request,pathlib,time
u='https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip'
p=pathlib.Path('work/census.zip')
with urllib.request.urlopen(u,timeout=120) as r,p.open('wb') as f:
 n=0;t=time.time()
 while b:=r.read(1024*1024):
  f.write(b);n+=len(b)
  if time.time()-t>15: print(round(n/1e6),'MB',flush=True);t=time.time()
print('downloaded',n,flush=True)
import zipfile
z=zipfile.ZipFile(p)
print([(i.filename,i.file_size) for i in z.infolist()],flush=True)
