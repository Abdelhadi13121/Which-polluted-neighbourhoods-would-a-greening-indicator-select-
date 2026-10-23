# Station–map discrepancy diagnostics

29 September 2026. Follow-up to the station consistency check. These diagnostics are exploratory and condition on a selected monitoring sample.

## Main conclusion

Do not claim a general increase in neighbourhood NO2 inequality. The data support falling mean NO2, but the sign and size of changes in spatial dispersion depend on measurement source, station type and analytical sample. The clearest map–station discrepancies in this sample are Madrid and Berlin. They are diagnostic findings, not proof that either source captures population exposure correctly.

## Site identity and spatial support

All 166 retained sampling points map to 166 distinct reported station identifiers (EoI codes, with station-ID fallback where absent), so duplicate instruments under a shared site code do not explain the results. There are 165 distinct 1-km cells: Paris has two reported sites in one cell. Codes are not a field verification of physical-site identity; nearby sites with different codes can remain.

## Paired spatial-block uncertainty

Resampled occupied spatial blocks with replacement, preserving each site's full six-year history and its paired grid values. Used 2,000 draws for each city/type/block size, with a fixed random seed (20260929). Blocks were 5 km and 10 km on the EPSG:3035 grid. Percentile intervals describe conditional resampling uncertainty, omit surface-model uncertainty, and do not turn purposively located stations into a representative sample.

The statistic below is the grid-estimated percentage change in CV minus the station-estimated percentage change in CV, in percentage points. These are unadjusted exploratory 95% intervals, not multiplicity-adjusted confirmatory tests.

| City | Difference, pp | 5-km interval | 10-km interval | 10-km blocks |
|---|---:|---|---|---:|
| Paris | 9.3 | [-1.6, 21.8] | [-4.2, 25.1] | 16 |
| Madrid | 11.4 | [3.6, 19.5] | [4.0, 19.9] | 26 |
| Barcelona | 12.6 | [-13.3, 24.5] | [-7.9, 26.6] | 11 |
| Milan | 5.9 | [-10.4, 20.9] | Too few blocks | 8 |
| Rome | 5.8 | [-13.8, 46.8] | [-14.4, 45.4] | 10 |
| Berlin | 27.4 | [16.7, 39.3] | [13.9, 41.1] | 14 |
| Amsterdam | 9.3 | [-53.1, 16.7] | Too few blocks | 7 |
| Lisbon | -14.1 | Too few blocks | Too few blocks | 3 |

Madrid and Berlin have intervals above zero at both block sizes. Other well-supported intervals include zero. Intervals based on fewer than ten occupied blocks are not interpreted here; their raw values remain in the CSV with a few-blocks flag. In Lisbon, only three 10-km blocks exist and some draws have zero baseline variance, making apparent precision misleading. Invalid draws were omitted and counts are reported. Ten blocks is a reporting heuristic, not a guarantee of reliable inference.

## Background and traffic stations

Background-only measured CV increases in Paris, Madrid, Milan and Amsterdam, and decreases in the other four cities. At 10-km blocks, all background intervals based on at least ten blocks include zero. This is weaker evidence than a simple count of signs suggests. Traffic-only estimates vary and several groups contain very few sites. All group estimates are retained in the result tables.

An exact variance decomposition splits CV squared into within-station-type and between-station-type components. For measured Paris and Madrid values, reductions between station-type means contribute more to the decline than within-type reductions. This offers an arithmetic explanation for why pooled and background-only summaries can differ, not a causal explanation of emissions or policies. Site types and sample composition are fixed across endpoints.

## Rounded-value sensitivity

All downloaded annual station values in this sample are integers. As a hypothetical quantization check, each site-year value was independently perturbed uniformly by up to ±0.5 µg/m³ in 1,000 draws. This is an assumed error scenario, not a documented source precision or a confidence interval. Pooled station CV continued to decline in all draws for seven cities; Lisbon changed sign in some draws (23.6% increases). Small rounding perturbations do not account for the main discrepancies, but no general bound on measurement error has been established.

## Research decision

The original inequality narrative should stay suspended. A defensible next research design would examine how mapped and monitored data change conclusions about urban exposure convergence, with explicit spatial-support and station-type analysis. Before committing to this as a paper, verify novelty and obtain less-rounded annual statistics or underlying validated time series, broaden station coverage, and seek a consistently reconstructed map product. The current station analysis is not independent of the mapping inputs, and its eight cities cannot stand in for all ten FUAs or Europe.

## Files

station_spatial_bootstrap.csv contains every interval, block count and valid-draw count. physical_site_audit.csv checks source site codes and shared cells. station_type_variance_decomposition.csv contains exact variance components. station_rounding_sensitivity.csv contains the assumed perturbation experiment. Reproduction scripts and raw station responses are included in the updated package.