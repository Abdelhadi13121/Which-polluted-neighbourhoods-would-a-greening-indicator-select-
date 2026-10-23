# NO2 source comparability and alternative-data test
1 October 2026

## Decision
The current evidence does not certify the 2021–2024 EEA series as a temporally uniform neighbourhood-change product. This is not evidence that the official maps are invalid. Shared mapping methods support their use as annual assessments, but fine-scale change estimates are sensitive to the alternative reconstruction actually tested here.

The data-repair search achieved two concrete downloads and one cross-product test. It did not produce a replacement covering all ten cities through 2024. Preserve the original panel; do not splice the alternative's 2021–2023 maps to EEA 2024, because that would introduce a product boundary into the change measure.

## EEA evidence
The downloaded 2021, 2022 and 2023 methodology PDFs share RIMM: regression, residual kriging, and merging rural/background/traffic layers. Their NO2 models use population, land-cover and traffic-related covariates, among other predictors. Consequently, regressions of predicted pollution on related urban characteristics may partly reflect map construction and should not be interpreted as independent causal evidence.

The 2021 report, Table A3.10 and printed page 115, gives cross-validation RMSE of 2.1, 3.7 and 6.0 micrograms/m3 for rural, urban background and traffic areas. The 2022 report gives 2.4, 4.4 and 6.1 (Table A3.10, printed page 121). Its Annex A2.2 explains the decision to retain CAMS forecasts for consistency with 2020–2021, while also documenting ensemble and emissions updates. The 2023 report gives 1.9, 4.4 and 6.2 (Table A3.10, printed pages 127–128), and documents an emissions-input update in November 2023.

These RMSEs are annual station-based diagnostics, not standard errors of each grid-cell change. Interannual error covariance is unavailable here. They cannot be subtracted from observed changes or inserted into independent-cell confidence intervals.

The 2024 catalogue explicitly labels the release validated, June 2026, identifier eea_r_3035_1_km_aq-interpolated-no2_p_2024_v01_r00. Its lineage cites the 2023 report and says the detailed 2024 report will appear at the end of 2026. Generic metadata wording also refers to up-to-date observations/EMEP whereas recent reports discuss CAMS; do not resolve this inconsistency by guessing a 2024 input version. The unavailable year-specific report leaves a documentation gap, not proof of a methodological break.

## Downloaded Europe-wide alternative
Open Earth Monitor / University of Münster, Zenodo record 19566932, version 2. The 197,744,434-byte annual NO2 Zarr archive was downloaded and its published MD5 verified. Actual metadata contain six annual slices, 1-km EPSG:3035 coordinates, concentrations in micrograms/m3, and an error layer. 2018 starts in May and is not a complete annual baseline. Full years are 2019–2023; there is no 2024 slice.

The project uses RIMM and EEA station data, so this is cross-product sensitivity, not independent ground truth. A single archive does not prove unchanged annual inputs or validate neighbourhood trends. The uncertainty field is described by the authors as combining component standard errors; no spatial/temporal error covariance is supplied by this test. Annual model-metric CSV was also downloaded; its leave-one-out and simple-fit diagnostics must be kept distinct.

## Matched-grid empirical test
The alternative's x and y coordinate arrays match the existing cell centres exactly, checked numerically before extraction. No upsampling or interpolation was applied. All six concentration and error slices were sampled. The comparison below uses the same inhabited cells observed in both products in 2021, 2022 and 2023. City means use fixed 2021 population weights. Correlations use equal cell weights.

| City | Matched cells | EEA change 2021–23 | Alternative change 2021–23 | Cell-change correlation |
|---|---:|---:|---:|---:|
| Paris | 11830 | -3.05 | -3.00 | 0.352 |
| Madrid | 3560 | -0.55 | -0.65 | 0.017 |
| Barcelona | 2860 | -0.09 | -0.80 | -0.123 |
| Milan | 2939 | -2.26 | -2.87 | 0.188 |
| Rome | 4883 | 0.55 | -1.67 | 0.084 |
| Berlin | 4651 | -2.34 | -1.62 | 0.126 |
| Vienna | 4639 | -1.10 | -2.18 | 0.445 |
| Amsterdam | 1829 | -2.06 | -0.88 | -0.019 |
| Warsaw | 7740 | -1.77 | -1.40 | 0.040 |
| Lisbon | 2659 | 1.43 | 1.56 | 0.374 |

Changes are micrograms/m3. Mean-change direction agrees in nine cities; Rome differs. Correlations of the cell-level changes range from -0.123 to 0.445. This specifically weakens confidence in neighbourhood differentiation; it does not imply that average city trends or pollution levels are uniformly unreliable. Coastal missingness reduces common coverage in several cities; all comparisons use the matched sample, and the output records its population.

No correlation threshold was selected to declare a product correct. Neither product is treated as truth. These differences can reflect predictors, fitting, monitoring coverage, smoothing and implementation choices. They are not estimated measurement errors against a known true surface.

## Downloaded local comparator
Barcelona Supercomputing Center, Zenodo 16737066: Dataset2A.zip was downloaded and verified against MD5 aa9f39ffc61ed90326b8e61910ddacf4. Inspection confirms six annual CSVs for 2019–2024, each with 1,068 census tracts and NO2, relative uncertainty and exceedance fields. This supplies a real local comparator through 2024. It is municipality-level coverage, not the Barcelona FUA and not the other nine cities. It has not been spatially matched to our 1-km grid in this task; no comparison result is claimed. Year-specific predictor tuning and shared monitoring inputs mean it is not automatically an invariant or independent benchmark.

The repository specifies research/education use and restrictions on redistributing numerical data. The raw archive is retained locally, outside the compact results package; publication redistribution terms need to be resolved before distributing it.

## Other candidates assessed
- Global monthly 0.01-degree NO2 (Zenodo 19740022): ends in 2023, units ppb; no 2024 replacement. Annual global archives are roughly 9 GB each. Raw arrays were not downloaded. Nominal resolution does not establish effective neighbourhood resolution.
- S-MESH European surface NO2 (Zenodo 7590177): 2019–2021, satellite-overpass estimates; does not cover the target changes to 2024.
- CAMS regional reanalysis: regional-scale contextual check, not a substitute for fine within-city contrasts. No new account-gated download was attempted.
- Earlier EEA consistent reconstruction ends in 2019 and cannot serve the prospective 2021 census-based question.

## Implication for the agreed research question
Keep the question fixed. A demographic-benefit coefficient from one surface is not enough when cell-change patterns differ across products. If the existing study is developed further, its minimum evidential requirement is agreement of the substantive demographic-change conclusion across the overlapping products, with 2024 separately qualified until its method is documented, and local validation with appropriately matched spatial support. This requirement is now based on an executed sensitivity test, not a demand for perfectly identical annual models.

A ten-city 2021–2024 replacement has not been obtained, and no source repairs were silently applied to the final dataset.

## Reproducibility
compare_oemc.py reads the verified archive using NumPy and numcodecs, verifies grid alignment, samples concentrations and errors, and produces oemc_eea_change_comparison.csv and oemc_sampled.npz. Download and metadata records are retained locally. This package contains evidence and scripts, not the 200-MB archive or dependencies.

## Sources
- EEA 2024 catalogue: https://sdi.eea.europa.eu/catalogue/srv/api/records/4c6361bd-cfd4-48de-9b4b-101cfb37f1f0
- EEA 2021–2023 reports: exact PDF URLs and hashes in download_manifest.json.
- Alternative: https://zenodo.org/records/19566932
- Barcelona data: https://zenodo.org/records/16737066
- Barcelona methods: https://www.nature.com/articles/s41597-026-06592-x
- Global alternative: https://zenodo.org/records/19740022
- S-MESH: https://zenodo.org/doi/10.5281/zenodo.7590177
