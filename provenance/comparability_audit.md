> Subsequent station check: measured relative NO2 dispersion fell in all eight retained endpoint cities, while matched grid dispersion rose in six. The NO2-inequality headline is not validated. See station_validation_report.md.

# Comparability audit and revised empirical assessment

29 September 2026. This report supersedes the broad interpretation in the first feasibility report. It is a source-method audit and period-sensitivity analysis, not independent validation against observations.

## Decision

The original claim of widespread increasing relative disparity is not robust to restricting the baseline to the post-2017 mapping era. Treat 2010–2024 results as exploratory across-method comparisons. The better-supported candidate question is pollutant-specific convergence after 2017, particularly persistent relative NO2 disparities alongside broader particulate-matter convergence. Do not yet describe 2017–2024 as a fully harmonized series.

## Source evidence and period selection

1. The official 2017 mapping report describes incorporation of an urban traffic layer for PM10 and PM2.5, alongside rural and urban background layers. The 2019/2020 reports explicitly identify 2017 as a major PM methodology change. This directly affects within-city contrasts. The downloaded 2017 PM2.5 README points to that report; its source UUID is bc1ffac8-7be7-40b4-92aa-c0948c119771. PM10 UUID: 48288a9e-f054-4728-9a30-6c80d2b65330.

2. The official 2022 report presents old- and updated-method results for overlapping historical years for comparability. Retrospective updated maps may exist, but they have not been substituted into this panel.

3. The 2023 report retains the RIMM framework. Downloaded validated-2024 metadata references that report. A shared framework does not guarantee identical station networks, predictors, smoothing, road/land-cover inputs or fine-scale uncertainty. The detailed vintage-by-vintage audit is incomplete.

4. The EEA has separately reconstructed a consistent 2005–2019 series for PM10, NO2 and ozone. This is evidence that consistent trend products require additional work; our concatenated annual releases are not that reconstructed product. PM2.5 is not listed in that reconstruction.

The post-change test was selected from documentation before its results were examined: 2017–2019 versus 2022–2024. A companion test excludes the newest validated year by comparing 2017–2019 with 2021–2023; it includes 2021 and is not a COVID-free comparison. Changes in the time window and atmospheric conditions also affect results, so differences cannot be attributed quantitatively to the 2017 method change.

## Results with fixed 2021 population weights

| Comparison | Lower mean | Narrower P90–P10 gap | Higher relative CV | Higher Gini |
|---|---:|---:|---:|---:|
| original_2010_2012_vs_2022_2024 | 30/30 | 22/30 | 21/30 | 22/30 |
| post_change_2017_2019_vs_2022_2024 | 30/30 | 30/30 | 10/30 | 11/30 |
| exclude_2024_2017_2019_vs_2021_2023 | 29/30 | 30/30 | 8/30 | 8/30 |

### Post-2017 results by pollutant

| Pollutant | Lower mean | Narrower absolute gap | Higher relative CV | Higher Gini |
|---|---:|---:|---:|---:|
| pm25 | 10/10 | 10/10 | 1/10 | 1/10 |
| pm10 | 10/10 | 10/10 | 2/10 | 2/10 |
| no2 | 10/10 | 10/10 | 7/10 | 8/10 |

Relative CV rises after 2017 in Warsaw for PM2.5; Amsterdam and Warsaw for PM10; and Paris, Madrid, Barcelona, Berlin, Vienna, Amsterdam and Warsaw for NO2. Some changes are small: NO2 CV rises only about 0.6% in Amsterdam. Counts of signs are descriptive, not significance tests.

## Weighting and boundary sensitivity

| Weight/sample, post-2017 | Lower mean | Narrower absolute gap | Higher CV |
|---|---:|---:|---:|
| population | 30/30 | 30/30 | 10/30 |
| equal_cell | 28/30 | 30/30 | 8/30 |
| interior | 30/30 | 30/30 | 11/30 |

NO2 threshold-inclusive high-exposure retention ranges from 82.4% to 94.4%. This describes overlap of cells above each period's weighted P80 threshold, using 2021 population, not movement of individuals. Ties are retained; groups need not contain exactly 20%.

## What was run

270 endpoint comparisons: three periods × three weighting/sample choices × ten cities × three pollutants. 810 convergence regression records: the same comparisons with 5/10/20-km covariance blocks. 450 annual tie diagnostics: ten cities × three pollutants × fifteen years. Descriptive beta regressions remain vulnerable to regression to the mean; the new endpoint results are not a causal model. The original full-period demographic models have not been promoted to post-2017 evidence and should be re-estimated only after the analysis period is settled.

## Publication recommendation

Revise the working paper around pollutant-specific convergence, rather than preserving the original headline. The absolute narrowing finding survives these checks. The broad claim that relative inequality usually increased does not. A credible next validation would compare NO2 trajectories with a stable regulatory-station subset and examine the detailed interpolation inputs and uncertainty by vintage. Such station data may also enter the maps, so this would be a consistency check rather than a fully independent validation. Reconstructed consistent maps would be preferable for long-period inference.

## Official references

- [2017 mapping report](https://www.eionet.europa.eu/etcs/etc-atni/products/etc-atni-reports/etc-atni-report-9-2019-european-air-quality-maps-for-2017-pm10-pm2-5-ozone-no2-and-nox-spatial-estimates-and-their-uncertainties).
- [2019 mapping report](https://www.eionet.europa.eu/etcs/etc-atni/products/etc-atni-reports/etc-atni-report-1-2021-european-air-quality-maps-for-2019-pm10-pm2-5-ozone-no2-and-nox-spatial-estimates-and-their-uncertainties).
- [2022 mapping report](https://www.eionet.europa.eu/etcs/etc-he/products/etc-he-products/etc-he-reports/etc-he-report-2024-4-air-quality-maps-of-eea-member-and-cooperating-countries-for-2022-pm10-pm2-5-o3-no2-nox-and-bap-spatial-estimates-and-their-uncertainties).
- [2023 mapping report](https://www.eionet.europa.eu/etcs/etc-he/products/etc-he-products/etc-he-reports/etc-he-report-2025-5-air-quality-maps-of-eea-member-and-cooperating-countries-for-2023-pm10-pm2-5-o3-no2-nox-and-bap-spatial-estimates-and-their-uncertainties).
- [Consistent reconstructed trend series](https://www.eionet.europa.eu/etcs/etc-atni/products/etc-atni-reports/etc-he-report-2021-11-air-quality-evolution-and-trends-in-europe-in-2005-2019-based-on-spatial-maps-trend-analysis-and-population-exposure-using-reconstructed-consistent-data-fusion-maps-for-pm10-ozone-and-no2).