import sys
sys.path.insert(0,'work/geolibs')
import pathlib,pickle,json,csv,hashlib,math,collections
import numpy as np
w=pathlib.Path('work');out=pathlib.Path('outputs');out.mkdir(exist_ok=True)
rows=pickle.load((w/'core.pkl').open('rb'));ua=pickle.load((w/'ua_aggregated.pkl').open('rb'))
cache={}
for r in rows:
 x,y=r['x_3035'],r['y_3035'];tx=x//40000*40000;ty=y//40000*40000;p=w/'tree_tiles'/f'{tx}_{ty}.npz'
 if p.exists():
  key=(tx,ty)
  if key not in cache:cache[key]=dict(np.load(p))
  a=cache[key];i=39-(y-ty)//1000;j=(x-tx)//1000;v=float(a['mean'][i,j]);frac=float(a['valid_fraction'][i,j])
  r['tree_cover_share_2018']=None if math.isnan(v) else v;r['tree_valid_area_fraction_2018']=frac;r['tree_status_2018']='available' if frac>0 else 'nodata'
 else:r.update(tree_cover_share_2018=None,tree_valid_area_fraction_2018=None,tree_status_2018='retrieval_failed')
 r.update(ua.get((r['city'],r['grid_id']),{'ua_city_coverage_fraction_2018':None,'urban_green_share_2018':None,'urban_green_status_2018':'retrieval_failed'}))
 r.update(tree_cover_share_2021=None,tree_status_2021='credential_required',urban_green_share_2021=None,urban_atlas_status_2021='credential_required',summer_lst_c_2021=None,lst_status_2021='credential_required')
 age=['population_under15','population_15to64','population_65plus'];p=r.get('population')
 r['age_total_differs_flag']=int(sum(r[a] for a in age)!=p) if p is not None and all(r.get(a) is not None for a in age) else None
 r['age_share_out_of_range_flag']=int(any(r.get(a) is not None and not 0<=r[a]<=1 for a in ['share_under15','share_65plus']))
 if r['census_cell_status']=='absent_from_source':
  for k in list(rows[0]):
   if k.endswith('_status') and k not in ['pm25_status','census_cell_status']:r.setdefault(k,'absent_from_source')
 # Keep explicit missing values; never convert absence or confidentiality to zero.
for r in rows:
 assert 0<=r['fua_cell_fraction']<=1
 assert r['x_3035']%1000==500 and r['y_3035']%1000==500
 for f in ['tree_cover_share_2018','urban_green_share_2018']:
  assert r.get(f) is None or -1e-9<=r[f]<=1+1e-9
assert len({(r['city'],r['grid_id']) for r in rows})==len(rows)==79988
assert len({r['city'] for r in rows})==10
cols=list(dict.fromkeys(k for r in rows for k in r))
csvpath=out/'european_urban_environment_health_1km.csv'
with csvpath.open('w',encoding='utf-8',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader();writer.writerows(rows)
with csvpath.open(encoding='utf8',newline='') as f:
 check=list(csv.DictReader(f));assert len(check)==len(rows) and len(check[0])==len(cols)
assert not any(r['tree_status_2018']=='retrieval_failed' or r['urban_green_status_2018']=='retrieval_failed' for r in rows),'Incomplete optional retrieval'
stats=[]
for city in dict.fromkeys(r['city'] for r in rows):
 a=[r for r in rows if r['city']==city];stats.append({'city':city,'rows':len(a),'census':sum(r['census_cell_status']=='reported' for r in a),'pm':sum(r['pm25_status']=='available' for r in a),'tree':sum(r['tree_cover_share_2018'] is not None for r in a),'green':sum(r['urban_green_share_2018'] is not None for r in a),'population':sum(r.get('population') or 0 for r in a)})
def count(pred):return sum(pred(r) for r in rows)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
hashes={n:sha(w/n) for n in ['fua.txt','census.zip','pm.zip']};hashes[csvpath.name]=sha(csvpath)
table='\n'.join(f"| {s['city']} | {s['rows']:,} | {s['census']:,} | {s['pm']:,} | {s['tree']:,} | {s['green']:,} |" for s in stats)
age_missing=count(lambda r:r.get('population_under15') is None)
report=f'''# European urban environmental-health data: quality report

Run date: 28 September 2026. **79,988 city–grid rows, ten FUAs, EPSG:3035, 1-km cells.** The CSV has {len(cols)} columns. Census and PM2.5 refer to 2021. Retrieved Copernicus supplements refer to **2018**; 2021 Copernicus fields remain blank because downloads require credentials. No synthetic values or spatial imputation were used.

## Coverage

Counts below indicate non-missing values, except Census, which counts matched source records. Green coverage is deliberately limited to whole cells within Urban Atlas city/greater-city boundaries, not the entire FUA.

| City | Rows | Census records | PM2.5 2021 | Tree 2018 | Urban green 2018 |
|---|---:|---:|---:|---:|---:|
{table}

## Harmonisation and interpretation

- FUA boundaries are the official GISCO **2021, 1:100,000** polygons. Cells are selected when their centre is inside the FUA. Each cell remains a complete 1 km² square. `fua_cell_fraction` records its overlap with the FUA; population is **not** multiplied by that fraction. Edge-cell selection and generalised boundaries mean sums are not official FUA population totals.
- Census joins use exact `GRD_ID` identifiers. Coordinates are cell centres in metres; grid identifiers encode the southwest corner. All cells are retained, including unpopulated cells. The latest V3 archive was downloaded from Eurostat's current release link; its README says underlying national data were received on 22 January 2025. The reference period remains the 2021 census round. There are 212 cells with multiple reporting countries; their source totals are retained, not split at national borders.
- EEA PM2.5 is an interpolated annual concentration surface in µg/m³, not a station observation or a health-outcome measure. Its 1-km grid and LAEA/GRS80 projection parameters match the census grid; origins differ from exact kilometre coordinates by less than 0.001 m. Values were joined at cell centres without smoothing or upsampling. The raster's legacy CRS name is not recognised by automatic EPSG lookup; its projection parameters and official EPSG:3035 metadata were checked explicitly.
- Tree cover: the public **2018** ImageServer was requested as numeric single-band TIFF (`rasterFunction=None`), resampled by nearest neighbour to an aligned 10-m EPSG:3035 grid. Each 1-km value is the mean of valid 10-m density values divided by 100. Codes above 100 and NoData were excluded. `tree_valid_area_fraction_2018` is the valid-pixel fraction; coastal/partial cells therefore describe valid area, not necessarily the complete cell. These are service-derived aggregates, with possible reprojection effects, not a fresh 2021 tree product.
- Urban green: **2018 Urban Atlas class 14100 (Green urban areas)** polygons, transformed by the official service to EPSG:3035, were unioned and intersected with cells. The denominator is 1 km². Values are supplied only where city/greater-city boundary coverage is at least 0.999999 of the cell. Elsewhere they are missing, not zero. This measure excludes forests, agricultural land and other classes. It is not total vegetation, tree canopy, or verified public access. `ua_city_coverage_fraction_2018` documents the restricted coverage.

## Missingness and quality flags

- **15 census cells are absent**, all in Lisbon. They remain in the table with `absent_from_source`; population and demographic values are blank.
- **450 PM2.5 values are missing**: Amsterdam 423, Lisbon 27. None has positive reported population. PM2.5 ranges from 3.939 to 22.726 µg/m³ across available cells.
- Census source codes **−8888 (confidential)** and **−9999 (unavailable)** become blank numeric values with a separate status for each demographic variable. Zero remains a measured/reported zero. Under-15 counts are missing in {age_missing:,} rows including absent cells. Ratios are blank when population is zero/missing or the numerator is missing.
- **{count(lambda r:r['age_total_differs_flag']==1):,} rows** have reported age bands that do not sum to total population. **{count(lambda r:r['age_share_out_of_range_flag']==1):,} rows** have an under-15 or 65+ ratio outside [0,1]. These source inconsistencies are preserved and flagged, not clipped. Eurostat documents disclosure-control perturbations and category totals that may differ. Exclude or investigate flagged ratios before modelling.
- National unallocated-population records have no grid geometry and cannot be assigned to these cities; they are not distributed across cells. Small-area census statistics are not exact headcounts. Tree and green data have a three-year mismatch with the core data.

## Credential-gated layers

Anonymous catalogue searches succeeded for 2021 Urban Atlas, 2021 tree-cover density and 2021 hourly LST. Actual CDSE product download requests returned **HTTP 401 Unauthorized** for all three. No credentials were supplied. Their 2021 numerical fields are blank and status is `credential_required`. The available LST archive is nominally 5 km; regridding it would not create independent 1-km temperature information. No summer LST statistic was calculated. The older public Urban Atlas service required spatially bounded queries; non-spatial queries timed out.

## Column guide

- **Keys:** `city`, `fua_code`, `grid_id`, `year`, `epsg`, `x_3035`, `y_3035`, `cell_area_km2`, `fua_cell_fraction`.
- **Census:** `population`, male/female counts, under-15/15–64/65+ counts, employed persons, birthplace categories, and previous-year residence categories. All are persons. `birth_elsewhere` means born outside the reporting country and other EU states. `residence_moved_from_abroad` refers to residence one year before the census. Each has a `_status` column. `land_surface_km2`, `populated_flag`, `census_countries`, and `census_cell_status` retain source context.
- **Demographic ratios:** `share_under15`, `share_65plus` are fractions, with the two age-quality flags described above.
- **Environment:** `pm25_annual_ug_m3`, `pm25_year`, `pm25_status`; `tree_cover_share_2018`, its valid-area fraction/status; `urban_green_share_2018`, its city-coverage fraction/status. Shares are fractions (0.25 = 25%). The three unavailable 2021 Copernicus measures and their statuses are explicit.

## Official sources and reproducibility

1. [GISCO 2021 FUA polygons](https://gisco-services.ec.europa.eu/distribution/v2/urau/geojson/URAU_RG_100K_2021_3035_FUA.geojson).
2. [Eurostat census grid release page](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids), [V3 archive](https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip). Attribution: European Union, 2026. Reuse here includes geographic selection, joins and derived ratios.
3. [EEA 2021 PM2.5 metadata and download](https://sdi.eea.europa.eu/data/c0ca09a4-d9fe-4772-bc48-90cf31639442), dataset `eea_r_3035_1_km_aq-interpolated-pm25_p_2021_v01_r00`, August 2023.
4. [Copernicus 2018 tree-cover ImageServer](https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer), [2018 Urban Atlas MapServer](https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/UrbanAtlas/UA_UrbanAtlas_2018/MapServer), layers 0/1 (city boundaries) and 2 (class 14100). Attribution: European Union, Copernicus Land Monitoring Service/EEA. Values were spatially aggregated/derived.
5. [Urban Atlas 2021](https://land.copernicus.eu/en/products/urban-atlas/urban-atlas-2021), [tree-cover series](https://land.copernicus.eu/en/products/high-resolution-layer-forests-and-tree-cover/tree-cover-density-2018-present-raster-100-m-europe-yearly), [LST archive](https://land.copernicus.eu/en/products/temperature-and-reflectance/hourly-land-surface-temperature-global-v1-0-5km), [CDSE authentication/download documentation](https://documentation.dataspace.copernicus.eu/APIs/OData.html).

Validation: unique `(city, grid_id)` keys; all ten cities; exact 1-km centre alignment; source projection parameters; source-status handling; environmental fraction ranges; CSV re-read and row count. All Urban Atlas download counts match independent service counts with the same projection, and all 31,938 returned geometries are valid. A separate single-cell tree request matches the tiled aggregate exactly. Dynamic public-service extracts are cached locally with the processing scripts. Census and PM2.5 source archives are also retained locally.

SHA-256 checksums:

```text
FUA GeoJSON  {hashes['fua.txt']}
Census ZIP   {hashes['census.zip']}
PM2.5 ZIP    {hashes['pm.zip']}
Merged CSV   {hashes[csvpath.name]}
```
'''
(out/'data_quality_report.md').write_text(report,encoding='utf8')
(w/'final_stats.json').write_text(json.dumps({'cities':stats,'rows':len(rows),'columns':len(cols),'hashes':hashes,'tree_missing':count(lambda r:r['tree_cover_share_2018'] is None),'green_available':count(lambda r:r['urban_green_share_2018'] is not None)},indent=2))
print(json.dumps(stats,indent=2),flush=True);print('SAVED',csvpath,csvpath.stat().st_size,'bytes',len(cols),'columns',flush=True)
