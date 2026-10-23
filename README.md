# Which polluted neighbourhoods would a greening indicator select?

Replication data and code for *Which polluted neighbourhoods would a greening indicator select? Indicator dependence in urban greening screening across ten European cities, 2010 to 2024* (Benghalem and Benbouziane).

[![Integrity check](https://github.com/Abdelhadi13121/Which-polluted-neighbourhoods-would-a-greening-indicator-select-/actions/workflows/verify.yml/badge.svg)](https://github.com/Abdelhadi13121/Which-polluted-neighbourhoods-would-a-greening-indicator-select-/actions/workflows/verify.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![Code: MIT](https://img.shields.io/badge/code-MIT-green)
![Data and docs: CC BY 4.0](https://img.shields.io/badge/data%20and%20docs-CC%20BY%204.0-lightgrey)

## Overview

Greening programmes are increasingly directed to polluted neighbourhoods, yet the indicator used to find places that lack green space is seldom examined. This repository holds everything needed to reproduce a comparison of two Europe-wide indicators: tree canopy (Copernicus Tree Cover Density 2018) and mapped green urban areas (Urban Atlas 2018, class 14100).

Screening rule: within each city, take the most polluted quartile of 1-km cells and select the least green 20% of them under each indicator. The study then measures how far the two selected sets coincide.

| Item | Value |
| --- | --- |
| Cities | Amsterdam, Barcelona, Berlin, Lisbon, Madrid, Milan, Paris, Rome, Vienna, Warsaw |
| Common analytical sample | 7,833 inhabited 1-km cells |
| Full panel | 79,988 cells, 1,279,808 cell-year rows, 2010 to 2025 |
| Pollutants | NO2, PM2.5, PM10 (EEA annual interpolated maps) |
| Residents | Eurostat Census Grid 2021 |
| Agreement measures | Overlap, replacement, chance-adjusted overlap (kappa) with exact tie handling |
| Inference | Block resampling on 5 km and 10 km blocks, 1,000 draws, seed 20260930 |

Headline result for NO2 in 2018: mean chance-adjusted overlap across the ten cities is 0.30 and mean replacement is 0.56, so the indicators disagree on most selected cells.

Vegetation is observed in 2018 and population in 2021, while pollution varies annually. Results describe screening decisions and conditional associations. They do not identify the effect of vegetation on air quality.

## Quick start

Requires Python 3.12 and about 3 GB of free disk space.

```bash
git clone https://github.com/Abdelhadi13121/Which-polluted-neighbourhoods-would-a-greening-indicator-select-.git
cd Which-polluted-neighbourhoods-would-a-greening-indicator-select-

python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python scripts/verify_package.py   # checksums and metadata
python reproduce.py                # restore data, run analyses, regenerate figures, compare tables
```

`reproduce.py` restores the two analytical CSVs from the archived parts, verifies their SHA-256 checksums, runs the baseline and panel analyses, regenerates the four figures, and compares every archived result table with the new output. It stops at the first discrepancy. New results are written to `outputs/`; the reference tables are never overwritten.

Restore the inputs only, without the scientific stack:

```bash
python reproduce.py --data-only
```

To recreate the exact verified environment, use `requirements-lock.txt` instead of `requirements.txt`.

## Data

| File | Description |
| --- | --- |
| `european_urban_panel_2010_2025.csv` | Complete cell-year panel, 1,279,808 rows, 86 fields |
| `paper_dataset.csv` | Fixed 2018 analytical slice used in the baseline analysis |

The panel is 759,701,412 bytes uncompressed. It is stored losslessly as five ordered gzip parts under `data/archives/`, each below 25 MiB, with a sixth part for the smaller file. All parts are ordinary Git files, with no Git LFS and no external download. `data/manifest.json` lists the part and file checksums. Do not commit the restored CSVs, which `.gitignore` excludes.

Field definitions are in [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md). Source versions, retrieval dates and processing steps are in [`docs/PROVENANCE.md`](docs/PROVENANCE.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `reproduce.py` | One-command reproduction and verification |
| `src/` | Baseline analysis, panel extension, figures, optional literature screening |
| `scripts/` | Data restoration, checksum verification, numerical comparison |
| `data/` | Compressed analytical inputs and manifest |
| `reference_results/` | Frozen result tables (baseline and panel extension) |
| `reference_figures/` | The four vector figures and captions |
| `docs/` | Data dictionary, provenance, reproduction notes, data sources and licensing |
| `provenance/` | EEA source manifest, map and station comparability audits |
| `source_extraction/` | Historical acquisition scripts and extraction records |
| `literature/` | Search logs, screening counts and cited-reference provenance |
| `validation/` | Full-run comparison results and software versions |

## Verification

A full run on the preparation machine (Python 3.12.14, Windows 11, 1,000 bootstrap draws, seed 20260930) reproduced all 38 archived result tables within a relative tolerance of 1e-6 and an absolute tolerance of 1e-8, with schemas, row order and text columns also matching. Details are in [`validation/`](validation/VALIDATION.md). Continuous integration checks the manifest, Python syntax and lossless data restoration on every push; it does not rerun the full statistical analysis.

## Limitations

- Urban Atlas green share exists only inside the verified city mask; missing values outside it are not zero.
- Annual EEA maps are separately estimated surfaces with ancillary covariates, so year-to-year differences mix real change and map revisions. The audits in `provenance/` document this.
- Vegetation and population are single-date measures, which limits temporal interpretation.
- `source_extraction/` records the original data acquisition. It is not a tested one-command rebuild from current web services; the offline reproduction uses the archived inputs.
- `src/literature_screen.py` needs licensed Scopus exports that are not distributed here. Search logs and counts are provided.

## Citation

Cite the archived release through GitHub's **Cite this repository** panel, which reads [`CITATION.cff`](CITATION.cff). For exact replication, cite the version DOI of the archived release.

## Licence

Code: MIT ([`LICENSE`](LICENSE)). Authored derived data, figures and documentation: CC BY 4.0 ([`LICENSE-DATA.md`](LICENSE-DATA.md)). Upstream terms remain in force; in particular, GISCO geographical source data carry a non-commercial restriction and an attribution requirement. See [`docs/DATA_SOURCES_AND_LICENSING.md`](docs/DATA_SOURCES_AND_LICENSING.md).

Contains information from Eurostat, the Copernicus Land Monitoring Service and the European Environment Agency. © EuroGeographics for the administrative boundaries. This is a derived research product and is not an official product of any of these bodies.

## Contact

Abdelhadi Benghalem, University Center of Maghnia, Tlemcen, Algeria. a.benghalem@cu-maghnia.dz. ORCID [0000-0003-4057-7448](https://orcid.org/0000-0003-4057-7448).

For a reproducibility problem, open an issue with your Python version, the command you ran, the full error message and `outputs/reproduction_check.json` if it exists.
