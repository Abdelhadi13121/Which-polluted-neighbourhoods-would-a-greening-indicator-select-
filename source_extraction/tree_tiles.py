from pip._vendor import truststore
truststore.inject_into_ssl()
import sys
sys.path.insert(0,'work/geolibs')
import urllib.request,urllib.parse,json,pathlib,concurrent.futures,time,pickle
import rasterio,numpy as np
from rasterio.io import MemoryFile
w=pathlib.Path('work');out=w/'tree_tiles';out.mkdir(exist_ok=True)
bounds=json.loads((w/'bounds.json').read_text());rows=pickle.load((w/'core.pkl').open('rb'))
tiles=set((r['x_3035']//40000*40000,r['y_3035']//40000*40000) for r in rows)
base='https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer/exportImage'
def task(t):
 x,y=t;p=out/f'{x}_{y}.npz'
 if p.exists():return True
 q={'f':'json','bbox':f'{x},{y},{x+40000},{y+40000}','bboxSR':3035,'imageSR':3035,'size':'4000,4000','format':'tiff','compression':'LZ77','pixelType':'U8','renderingRule':json.dumps({'rasterFunction':'None'}),'interpolation':'RSP_NearestNeighbor'}
 for attempt in range(3):
  try:
   u=base+'?'+urllib.parse.urlencode(q);d=json.loads(urllib.request.urlopen(u,timeout=90).read())
   if 'href' not in d:raise ValueError(d)
   b=urllib.request.urlopen(d['href'],timeout=90).read()
   with MemoryFile(b) as mem,mem.open() as ds:
    assert ds.count==1 and ds.shape==(4000,4000) and ds.res==(10,10)
    a=ds.read(1);valid=(a<=100)&(ds.read_masks(1)>0)
    sums=np.where(valid,a,0).reshape(40,100,40,100).sum(axis=(1,3),dtype='float64');counts=valid.reshape(40,100,40,100).sum(axis=(1,3))
    means=np.divide(sums,counts,out=np.full((40,40),np.nan),where=counts>0)/100
    np.savez_compressed(p,mean=means,valid_fraction=counts/10000)
   print('tree tile',x,y,len(b),'bytes',flush=True);return True
  except Exception as e:
   print('tree retry',x,y,attempt,str(e)[:200],flush=True)
 print('FAILED',t,flush=True);return False
print('Tiles',len(tiles),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(task,sorted(tiles)))
print('Completed',sum(results),'of',len(tiles),flush=True)
