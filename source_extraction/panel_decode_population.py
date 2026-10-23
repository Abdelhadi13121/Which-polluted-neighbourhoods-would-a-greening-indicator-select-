import pathlib,json,csv
w=pathlib.Path('work/panel/population');out=[]
codes={'FR001F':'Paris','ES001F':'Madrid','ES002F':'Barcelona','IT002F':'Milan','IT001F':'Rome','DE001F':'Berlin','AT001F':'Vienna','NL001F':'Amsterdam','PL001F':'Warsaw','PT001F':'Lisbon'}
for code,city in codes.items():
 path=w/(code+'.json');d=json.loads(path.read_text()) if path.exists() else None
 def val(ind,year):
  if d is None:return None,''
  ii=d['dimension']['indic_ur']['category']['index'];tt=d['dimension']['time']['category']['index']
  if ind not in ii or str(year) not in tt:return None,''
  ix=str(ii[ind]*len(tt)+tt[str(year)])
  return d['value'].get(ix),d.get('status',{}).get(ix,'')
 def total(inds,year):
  vs=[val(i,year) for i in inds]
  return (sum(x[0] for x in vs) if all(x[0] is not None for x in vs) else None),''.join(sorted(set(''.join(x[1] for x in vs))))
 for year in range(2010,2026):
  pop,flag=val('DE1001V',year);male,mflag=val('DE1002V',year);female,fflag=val('DE1003V',year)
  young,yflag=total(['DE1040V','DE1074V','DE1077V'],year)
  old,oflag=total(['DE1028V','DE1055V'],year)
  if old is None:old,oflag=total(['DE1125V','DE1128V','DE1131V','DE1134V','DE1137V'],year)
  out.append({'city':city,'fua_code':code,'year':year,'fua_population_annual':pop,'fua_population_male_annual':male,'fua_population_female_annual':female,'fua_population_under15_annual':young,'fua_population_65plus_annual':old,'fua_share_under15_annual':young/pop if pop and young is not None else None,'fua_share_65plus_annual':old/pop if pop and old is not None else None,'fua_population_source_flag':flag,'fua_age_source_flags':''.join(sorted(set(yflag+oflag))),'fua_population_status':'reported' if pop is not None else 'not_reported','fua_population_source':'Eurostat_urb_lpop1'})
pathlib.Path('work/panel/fua_population.json').write_text(json.dumps(out,indent=2))
for code,city in codes.items():
 a=[x for x in out if x['city']==city and x['fua_population_annual'] is not None];print(city,[(x['year'],x['fua_population_annual'],x['fua_population_source_flag']) for x in a],flush=True)
