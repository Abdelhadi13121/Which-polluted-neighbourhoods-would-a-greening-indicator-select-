# Data dictionary: `european_urban_panel_2010_2025.csv`

One row per 1 km cell and year: 79,988 cells x 16 years (2010 to 2025) = 1,279,808 rows, ETRS89-LAEA (EPSG:3035). Ten functional urban areas (FUA codes: Paris FR001F, Madrid ES001F, Barcelona ES002F, Milan IT002F, Rome IT001F, Berlin DE001F, Vienna AT001F, Amsterdam NL001F, Warsaw PL001F, Lisbon PT001F). `paper_dataset.csv` is the 2018 slice of the same grid used by `paper_analysis.py`.

Descriptions below follow the column names and the values found in the file. Where a definition could not be confirmed from the file itself it says so; the data owner should complete those entries before deposit.

| Columns | Content |
| --- | --- |
| `city`, `fua_code`, `grid_id`, `epsg`, `x_3035`, `y_3035`, `cell_area_km2`, `fua_cell_fraction` | Identifiers, cell centre coordinates (metres), cell area and the cell's fraction inside the FUA boundary (boundary year 2021, `fua_boundary_year`). |
| `population_2021`, `population_*_2021`, `employed_persons_2021`, `birth_*`, `residence_*`, `share_under15_2021`, `share_65plus_2021`, `land_surface_km2_2021`, `populated_flag_2021`, and the matching `*_status_2021` columns | Eurostat Census 2021 1 km grid counts. Status values: `reported` (1,279,568 rows) or `absent_from_source` (240 rows). |
| `tree_cover_share_2018`, `tree_valid_area_fraction_2018`, `tree_status_2018` | Copernicus Tree Cover Density 2018 averaged to the cell (share in [0, 1]) and the fraction of the cell with valid tree-cover data. `tree_status_2018` is `available` in every row. The analysis drops cells with valid fraction below 0.95 (55 cells). |
| `ua_city_coverage_fraction_2018`, `urban_green_share_2018`, `urban_green_status_2018` | Urban Atlas 2018 class 14100 (green urban areas) cell share. `urban_green_status_2018` is `available_city_core` (146,608 rows = 9,163 cells x 16 years; `ua_city_coverage_fraction_2018` equals 1 in every one) or `outside_verified_city_core` (all other cells, including 3,733 cells with a coverage fraction between 0 and 1). The green share is missing, not zero, outside the available set. The restriction is the extraction's: the product itself is distributed per functional urban area. |
| `year`, `census_reference_year`, `copernicus_baseline_year`, `within_reference_aq_coverage`, `aq_release_status` | Pollution year; census reference year (2021); Copernicus baseline year (2018); indicator that the cell lies inside the reference air-quality map coverage (0.9944 of cells); release status of the pollution map (`non_interim` for 2010 to 2024, `interim` for 2025). |
| `pm25_annual_ug_m3`, `pm10_annual_ug_m3`, `no2_annual_ug_m3` | EEA annual concentration maps (ug/m3) assigned to the cell. These three are used in the paper. |
| `pm10_daily_p904_ug_m3`, `pm10_daily_36th_highest_ug_m3`, `o3_*` | Further EEA indicators present in the file and not used in the paper (ozone is excluded by design; see Section 3.1). |
| `*_source_key`, `*_available`, `*_change_from_2021_ug_m3` | Internal source key per pollutant and year (for example `no2_2018`), availability flag, and change relative to 2021. The source keys are labels; they do not record raster filenames (see PROVENANCE.md). |
| `fua_population_*`, `fua_share_*_annual`, `fua_age_source_flags`, `fua_population_source` | Annual FUA-level population series (source label `Eurostat_urb_lpop1`) and status flags; not used in the paper. |

Sample used in the paper (2018): inhabited cells with valid tree cover and available green share = 7,833 cells (34.99 million of 52.29 million residents of inhabited cells).
