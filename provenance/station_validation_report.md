# NO2 station consistency check: revised research decision

29 September 2026. This report supersedes the provisional NO2-inequality interpretation in comparability_audit.md.

## Decision

Falling average NO2 is supported by both the station and grid data examined. Increasing relative neighbourhood inequality is not validated: at the retained monitoring locations, station CV falls in every city, while grid CV rises in six of eight. Do not use increasing NO2 inequality as the main empirical claim at this stage.

## Design and coverage

Source: EEA AQ_Statistics_WM regulatory annual statistics service, layer 0. Queried NO2 annual means (P1Y), 2017–2024, using ten FUA bounding boxes in EPSG:3035 and subsequently testing exact inclusion in the saved FUA polygons. Each download was checked against the service count and unique OBJECTIDs.

Eligible records: verification code 1, preliminary flag 0, fixed measurements, units ug.m-3, data coverage at least 90%, nonnegative reported concentration. Keys are namespace plus sampling-point identifier. Duplicate point-years with identical concentrations are collapsed; conflicting values would be excluded. Retained points have unchanged station type and coordinates moving no more than 100 m from their baseline position. Grid values use the 1-km cell containing the baseline point; this is a spatial-support mismatch with point monitoring and may miss roadside gradients.

The strict eight-year panel retains 77 sampling points in five cities. A separate six-year endpoint panel requires every year in 2017–2019 and 2022–2024, retaining 166 sampling points in eight cities (996 point-year records). It avoids imputing missing intermediate years and does not reconstruct full trajectories for those additional points. Points are weighted equally; these are not population-weighted neighbourhood estimates. Sampling points are not necessarily distinct physical stations.

The queried service returned no Warsaw records; no Vienna sampling point passed the complete endpoint requirements. Madrid and Barcelona lack 2020 records in this service extract; Berlin lacks 2021. These are service/sample limitations, not evidence that those countries lack measurements. The regulatory assessment layer may not contain every valid monitoring station.

## Matched-location results

Each comparison uses 2017–2019 versus 2022–2024 means. CV is the spatial standard deviation divided by the mean across retained sampling points.

| City | Points | Measured mean change % | Grid mean change % | Measured CV change % | Grid CV change % |
|---|---:|---:|---:|---:|---:|
| Paris | 28 | -32.4 | -31.6 | -7.3 | 2.0 |
| Madrid | 43 | -27.7 | -25.2 | -5.6 | 5.8 |
| Barcelona | 24 | -26.7 | -25.4 | -5.4 | 7.3 |
| Milan | 12 | -25.5 | -25.2 | -3.4 | 2.5 |
| Rome | 15 | -26.3 | -22.9 | -9.8 | -3.9 |
| Berlin | 20 | -36.4 | -33.5 | -7.0 | 20.4 |
| Amsterdam | 19 | -28.9 | -29.2 | -8.1 | 1.2 |
| Lisbon | 5 | -23.3 | -24.6 | -0.7 | -14.8 |

Station-level concentration-change correlations with grid changes range from 0.42 to 0.83. Agreement in average trends does not establish agreement in distributional trends. Background and traffic strata are also supplied where at least three sampling points remain. Small samples, especially Lisbon (five), warrant caution. These are descriptive results without a station-based confidence interval or significance claim.

## Grid-only sign stability

Across two endpoint windows and three weighting/sample choices, only Paris, Barcelona and Berlin have increasing NO2 CV in all six variants. Rome decreases in all six. Other cities change sign across variants. The measured CV at the retained sampling points falls even in Paris, Barcelona and Berlin. This discordance needs explanation rather than selective emphasis on the map result.

## Limits of the check

This is not independent validation: monitoring stations may be inputs to the EEA surfaces. Their locations are selected rather than representative, and 1-km cells smooth point-scale variation. The service can contain rounded values and incomplete regulatory reporting. Exact physical-site identity, instrumental continuity and calibration histories have not been audited. Neither increasing inequality across all neighbourhoods nor its absence can be established solely from this selected station panel. Data coverage of 90% is an analytical inclusion rule, not a claim of comprehensive regulatory completeness.

## Next scientific decision

Keep cleaner air and absolute narrowing as provisional descriptive results. Suspend the increasing-relative-inequality headline. The appropriate next analysis is to explain the map–station discrepancy using station-type strata, co-located unique physical sites, map prediction uncertainty and a consistently reconstructed exposure product. A methods-focused paper on the sensitivity of inequality estimates is a possible direction, but its novelty and scope require a literature review before choosing it. Do not force the original article narrative.

## Sources and files

- [EEA annual-statistics service](https://air.discomap.eea.europa.eu/arcgis/rest/services/AirQuality/AQ_Statistics_WM/MapServer/0).
- [EEA statistics viewer description](https://www.eea.europa.eu/en/analysis/maps-and-charts/air-quality-statistics-dashboards/).
- station_sample_audit.csv and station_consistency_results.csv: strict eight-year sample.
- station_endpoint_sample_audit.csv and station_endpoint_consistency_results.csv: six endpoint years.
- station_endpoint_grid_pairs.csv: matched measurements and map concentrations.
- no2_sign_stability.csv: endpoint/weighting stability.
- Raw service responses with query parameters are retained in the stations subfolder.