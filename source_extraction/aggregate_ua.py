import sys
sys.path.insert(0,'work/geolibs')
import pathlib,json,pickle,numpy as np,shapely
from shapely.geometry import shape
w=pathlib.Path('work');rows=pickle.load((w/'core.pkl').open('rb'));out={}
for city in dict.fromkeys(r['city'] for r in rows):
 ps=[w/'ua_green'/f'{city}_{i}.json' for i in [0,1,2]]
 if not all(p.exists() for p in ps):print('not ready',city,flush=True);continue
 docs=[json.loads(p.read_bytes()) for p in ps]
 boundaries=[shapely.make_valid(shape(f['geometry'])) for d in docs[:2] for f in d['features'] if f.get('geometry')]
 greens=[shapely.make_valid(shape(f['geometry'])) for f in docs[2]['features'] if f.get('geometry')]
 coverage=shapely.union_all(boundaries);tree=shapely.STRtree(greens)
 selected=[r for r in rows if r['city']==city]
 xs=np.array([r['x_3035']-500 for r in selected]);ys=np.array([r['y_3035']-500 for r in selected]);cells=shapely.box(xs,ys,xs+1000,ys+1000)
 fractions=shapely.area(shapely.intersection(cells,coverage))/1e6
 known=fractions>=0.999999;values=np.full(len(cells),np.nan)
 for ix in np.where(known)[0]:
  cell=cells[ix];indices=tree.query(cell,predicate='intersects')
  # Union prevents double-counting polygons from neighbouring Urban Atlas FUAs.
  geom=shapely.union_all([greens[j] for j in indices]);values[ix]=shapely.intersection(cell,geom).area/1e6
 for r,frac,val in zip(selected,fractions,values):out[(city,r['grid_id'])]={'ua_city_coverage_fraction_2018':round(float(frac),6),'urban_green_share_2018':None if np.isnan(val) else float(val),'urban_green_status_2018':'available_city_core' if not np.isnan(val) else 'outside_verified_city_core'}
 print(city,'fully covered cells',int(known.sum()),'green polygons',len(greens),flush=True)
pickle.dump(out,(w/'ua_aggregated.pkl').open('wb'))
