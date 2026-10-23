from pip._vendor import truststore
truststore.inject_into_ssl()
import pathlib,json,urllib.request,urllib.parse,concurrent.futures
w=pathlib.Path('work/panel/population');w.mkdir(exist_ok=True)
codes=['FR001F','ES001F','ES002F','IT002F','IT001F','DE001F','AT001F','NL001F','PL001F','PT001F']
def fetch(code):
 u='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/urb_lpop1?'+urllib.parse.urlencode({'lang':'en','cities':code,'sinceTimePeriod':'2010'})
 try:
  b=urllib.request.urlopen(u,timeout=90).read();d=json.loads(b);(w/(code+'.json')).write_bytes(b);print(code,d.get('size'),d.get('updated'),flush=True)
 except Exception as e:print(code,e,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:list(p.map(fetch,codes))
