# Provenance of the analytical data

Everything below is taken from the extraction record kept by the data owner (`source_extraction/` and `provenance/` in this repository) and from the file itself. The restored panel file in `data/` is byte-identical to the build recorded in `source_extraction/build_stats.json` (SHA-256 `eff20c2c0305f47411d9d683a0af564a300cd2c4cda4159de98ca799431aa1ba`; 759,701,412 bytes; 1,279,808 rows; 86 columns).

The panel was built on 28 to 29 September 2026 from public sources with the scripts in `source_extraction/`; all sources were downloaded on 28 September 2026 (`retrieved_date` in `provenance/eea_source_manifest.csv`). No synthetic values and no spatial imputation were used in assembling the panel; the EEA pollution inputs themselves are interpolated products.

## Grid and study area

- 1 km cells of the Eurostat census grid (ETRS89-LAEA, EPSG:3035), cell identifiers `GRD_ID`; coordinates in the panel are cell centres, identifiers encode the south-west corner.
- Study area: ten functional urban areas from the GISCO 2021 FUA polygons at 1:100,000 (`URAU_RG_100K_2021_3035_FUA.geojson`, SHA-256 `531a3f69fbcecb3b781405f3168151d8847463377ce0083d49cbc22b95441543`). A cell is selected when its centre lies inside the FUA; it remains a complete 1 km2 square. `fua_cell_fraction` records its overlap with the FUA, and population is not multiplied by that fraction, so sums are not official FUA totals.

## Residents (Eurostat Census 2021 grid)

- File: `Eurostat_Census-GRID_2021_V3.zip` (SHA-256 `18a467e3d96b71dd89f0440cc184751bded45721cdff8ba778ece79d7a4f5843`), downloaded from the current Eurostat release link; the README of the archive states that the underlying national data were received on 22 January 2025. Exact `GRD_ID` joins.
- Source codes -8888 (confidential) and -9999 (unavailable) become blank values with a separate `*_status_2021` column; zero stays a reported zero. 15 cells (all in Lisbon) are absent from the source (240 rows over 16 years, status `absent_from_source`). 212 cells have several reporting countries and keep their source totals. 10,100 rows have age bands that do not sum to the total and 47 rows have ratios outside [0, 1]; they are flagged, not corrected. These flags are not used in the paper.

## Tree cover (Copernicus HRL Tree Cover Density 2018)

- Public ImageServer `HRL_TreeCoverDensity_2018`, requested as numeric single-band GeoTIFF (`rasterFunction=None`) in tiles, resampled by nearest neighbour to an aligned 10 m EPSG:3035 grid (`tree_tiles.py`).
- Cell value = mean of the valid 10 m density values divided by 100; codes above 100 and NoData are excluded. `tree_valid_area_fraction_2018` is the share of valid pixels. A separate single-cell request matched the tiled aggregate exactly. The paper keeps cells with valid fraction of at least 0.95.

## Mapped green (Copernicus Urban Atlas 2018, class 14100)

- Public Urban Atlas 2018 MapServer: class 14100 (green urban areas) polygons transformed to EPSG:3035, unioned and intersected with the cells (`ua_green.py`, `aggregate_ua.py`); the denominator is 1 km2. All returned counts matched independent service counts and all 31,938 geometries were valid.
- **Mask.** Values are supplied only where the cell is wholly inside the Urban Atlas city / greater-city boundary (coverage fraction at least 0.999999; layers 0 and 1 of the service); elsewhere the green share is missing, not zero. `ua_city_coverage_fraction_2018` records the coverage. In the panel this gives 9,163 cells with status `available_city_core`; 3,733 partly covered cells are `outside_verified_city_core`. This is the extraction's restriction and not a limit of the product, which is distributed per functional urban area.

## Pollution (EEA interpolated annual maps)

- One raster per pollutant and year from the EEA data hub; dataset identifiers, UUIDs, download URLs, archive sizes and SHA-256 checksums for all 64 pollutant-years (NO2, PM2.5, PM10 and O3, 2010 to 2025; the paper uses the first three) are in `eea_source_manifest.csv`. The NO2 identifiers and release labels are:

| Year | NO2 dataset identifier | Release label in the catalogue title | Status |
| --- | --- | --- | --- |
| 2010 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2010_v01_r00` | no month stated in the catalogue title | validated |
| 2011 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2011_v01_r00` | no month stated in the catalogue title | validated |
| 2012 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2012_v01_r00` | no month stated in the catalogue title | validated |
| 2013 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2013_v01_r00` | no month stated in the catalogue title | validated |
| 2014 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2014_v01_r00` | no month stated in the catalogue title | validated |
| 2015 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2015_v01_r00` | no month stated in the catalogue title | validated |
| 2016 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2016_v01_r00` | Apr. 2019 | validated |
| 2017 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2017_v01_r00` | Jan. 2020 | validated |
| 2018 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2018_v01_r00` | Jan. 2021 | validated |
| 2019 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2019_v01_r00` | Mar. 2022 | validated |
| 2020 | `eea_r_3035_1_km_aq-interpolated-NO2_p_2020_v01_r00` | no month stated in the catalogue title | validated |
| 2021 | `eea_r_3035_1_km_aq-interpolated-no2_p_2021_v01_r00` | August 2023 | validated |
| 2022 | `eea_r_3035_1_km_aq-interpolated-no2_p_2022_v01_r00` | June 2024 | validated |
| 2023 | `eea_r_3035_1_km_aq-interpolated-no2_p_2023_v01_r00` | June 2025 | validated |
| 2024 | `eea_r_3035_1_km_aq-interpolated-no2_p_2024_v01_r00` | validated data, June 2026 | validated |
| 2025 | `eea_r_3035_1_km_aq-interpolated-no2_p_2025_v00_r00` | interim data, June 2026 | interim |

- 2010 to 2024 are validated releases; 2025 is interim (June 2026), flagged `aq_release_status = interim` in the panel and excluded from the tests. Where the catalogue title carries no month, none is recorded here. The retrospective updated maps that some later reports describe were not substituted.
- **Assignment to cells.** `panel_sample.py` reads each native 1 km raster, checks the LAEA/GRS80 parameters and that the raster origin is on the kilometre grid (alignment within 0.01 m), applies the stored scale and offset, and takes the value of the pixel containing the cell centre (no smoothing, no resampling or upsampling). Negative and non-finite values become missing.
- **Coverage.** `panel_build.py` sets every pollution value to missing for cells outside the 2021 PM2.5 reference raster coverage (`within_reference_aq_coverage = 0`): 450 cells (Amsterdam 423, Lisbon 27), none with positive reported population. All other cells have a value for every year.

## Documentation of the map method (read for this package)

- ETC HE Report 2025/5 (2023 maps), p. 62: the NO2 map is a linear regression of station data on supplementary data followed by residual kriging; supplementary data are chemical-transport-model output, altitude, Sentinel-5P data, wind speed, population density and land-cover indicators for rural areas, the same plus temperature for urban background areas, and chemical-transport-model output, altitude and Sentinel-5P data for traffic areas; urban background and traffic layers are merged with gridded road data, the urban layer is combined with the rural layer using a 1 km population density grid, and the final 1 km map is representative of rural and urban background areas but not of urban traffic areas.
- The data owner's audits (`provenance/`) read the 2021 to 2023 reports and report cross-validation RMSE of 1.9 to 2.4, 3.7 to 4.4 and 6.0 to 6.2 ug/m3 for rural, urban background and traffic NO2, an emissions-input update documented in November 2023, and that the year-specific 2024 report was not yet available. They also state that the 2017 mapping report introduced an urban traffic layer for PM and that the 2019 and 2020 reports identify 2017 as a major PM method change. Those two statements were not re-read for this package.
- Station check (`provenance/station_validation_report.md` and `station_discrepancy_diagnostics.md`, unpublished, exploratory): for 166 regulatory sampling points in eight cities, mean NO2 changes between 2017 to 2019 and 2022 to 2024 agree with the maps, but the spatial coefficient of variation falls at the stations in every city while it rises in the maps in six of the eight. The stations may be inputs to the maps, so this is not independent validation. The manuscript cites it as an unpublished check.

## Not available or not done

- Copernicus 2021 products (Urban Atlas 2021, tree cover 2021, land surface temperature) could not be downloaded without credentials and are not in the panel.
- The raw archives (census 540 MB, EEA rasters) and tile caches are kept by the data owner and are not copied here; `source_extraction/` contains the historical scripts, manifest and quality report; a current end-to-end download is not validated. Two download helper scripts (`panel_direct_retry.py`, `probe_direct_download.py`) were not copied. The scripts use paths relative to the original working folder (`work/`, `outputs/`).
- Source licensing scope and the remaining GISCO-specific qualification are documented in `docs/DATA_SOURCES_AND_LICENSING.md`.
