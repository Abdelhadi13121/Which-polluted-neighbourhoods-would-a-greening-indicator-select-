from pip._vendor import truststore
truststore.inject_into_ssl()
import pathlib,json,re,urllib.request,concurrent.futures,zipfile,shutil,hashlib,time,sys
w=pathlib.Path('work/panel');records=json.loads((w/'records.json').read_text());selected={}
for uid,d in records.items():
 title=d.get('resourceTitleObject',{}).get('default',d.get('title',''));m=re.search(r'for (20\d{2})',title)
 if not m:continue
 year=int(m[1]);pol=title.split(',')[0].lower().replace('.','')
 if not 2010<=year<=2025 or pol not in ['pm25','pm10','no2','o3']:continue
 if len(sys.argv)>1 and pol!=sys.argv[1]:continue
 key=(pol,year);interim='interim' in title.lower()
 if key not in selected or (selected[key]['interim'] and not interim):selected[key]={'pollutant':pol,'year':year,'uuid':uid,'title':title,'interim':interim,'identifier':d.get('resourceIdentifier',[])}
def fetch(rec):
 pol,year=rec['pollutant'],rec['year'];folder=w/f'{pol}_{year}';folder.mkdir(exist_ok=True);manifest=folder/'manifest.json'
 if manifest.exists():return json.loads(manifest.read_text())
 try:
  u='https://sdi.eea.europa.eu/data/'+rec['uuid'];s=urllib.request.urlopen(u,timeout=90).read().decode();(folder/'download_page.html').write_text(s,encoding='utf8')
  match=re.search(r'https://sdi\.eea\.europa\.eu/datashare/s/[^"<>]+/download',s)
  if not match:raise ValueError('No public download link')
  url=match[0];p=folder/'source.zip'
  with urllib.request.urlopen(url,timeout=120) as src,p.open('wb') as dst:shutil.copyfileobj(src,dst)
  z=zipfile.ZipFile(p);names=z.namelist();tifs=[]
  for n in names:
   if n.lower().endswith(('.tif','.tiff')):
    dest=folder/pathlib.PurePosixPath(n).name
    with z.open(n) as src,dest.open('wb') as dst:shutil.copyfileobj(src,dst)
    tifs.append(str(dest))
   elif n.lower().endswith(('readme.md','read.me','.xml')) and len(n)<250:
    (folder/pathlib.PurePosixPath(n).name).write_bytes(z.read(n))
  rec.update(download_url=url,archive_bytes=p.stat().st_size,tifs=tifs,archive_sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),status='downloaded')
  manifest.write_text(json.dumps(rec,indent=2));print(pol,year,p.stat().st_size,[pathlib.Path(t).name for t in tifs],flush=True);return rec
 except Exception as e:
  rec.update(status='failed',error=str(e));print('FAILED',pol,year,str(e),flush=True);return rec
print('Selected',len(selected),'datasets',flush=True)
def retry(rec):
 for attempt in range(3):
  result=fetch(dict(rec))
  if result['status']=='downloaded':return result
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2 if len(sys.argv)>1 else 4) as p:result=list(p.map(retry,selected.values()))
(w/('download_manifest_'+sys.argv[1]+'.json' if len(sys.argv)>1 else 'download_manifest.json')).write_text(json.dumps(result,indent=2))
print('Finished',sum(r['status']=='downloaded' for r in result),'of',len(result),flush=True)
