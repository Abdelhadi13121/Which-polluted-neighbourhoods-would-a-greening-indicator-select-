import pathlib,re,json
w=pathlib.Path('work/panel');allrecords={}
for file in ['series','no2_series','pm10_series','o3_series']:
 s=(w/(file+'.txt')).read_text(encoding='utf8');data=[]
 for m in re.finditer(r'"_source"\s*:\s*',s):
  try:data.append(json.JSONDecoder().raw_decode(s[m.end():])[0])
  except json.JSONDecodeError:pass
 def walk(o):
  if isinstance(o,dict):
   if 'resourceTitleObject' in o or ('uuid' in o and any('title' in k.lower() for k in o)):
    key=str(o.get('uuid',o.get('id','')))
    if key:allrecords[key]=o
   for v in o.values():walk(v)
  elif isinstance(o,list):
   for v in o:walk(v)
 walk(data)
(w/'records.json').write_text(json.dumps(allrecords),encoding='utf8')
print('records',len(allrecords))
for k,d in allrecords.items():
 t=d.get('resourceTitleObject',{}).get('default',d.get('title',''))
 if '2024' in t or '2025' in t:print(k,t)
