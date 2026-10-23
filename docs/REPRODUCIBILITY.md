# Reproduction design

## Inputs and identity

The two original CSVs are retained without changing any value, header, row order or line ending. Data restoration checks both compressed parts and the reconstructed bytes against SHA-256.

| Input | SHA-256 |
| --- | --- |
| `european_urban_panel_2010_2025.csv` | `eff20c2c0305f47411d9d683a0af564a300cd2c4cda4159de98ca799431aa1ba` |
| `paper_dataset.csv` | `60ef72798a24bf884c7005fd65627c529b93edd5a98b4f25b5e6ca56cfd1f6b4` |

`paper_dataset.csv` contains the fixed 2018 analytical slice. The full panel carries all 86 original fields, including variables not used in the paper, to preserve provenance and support reuse. Confidential or unavailable counts remain missing, with their status columns retained.

## Execution order

`requirements.txt` pins the main scientific libraries. `requirements-lock.txt` also records the transitive packages from the verified Python 3.12 environment; use `python -m pip install -r requirements-lock.txt` to recreate those exact versions.

1. `scripts/prepare_data.py` verifies all gzip parts and restores both original files.
2. `src/paper_analysis.py` writes the baseline tables to `outputs/original_script/`.
3. `src/panel_extension.py` reproduces baseline estimates internally, constructs annual priority comparisons and writes `outputs/panel_extension/`.
4. `src/make_figures.py` regenerates PDF and PNG figures in `outputs/figures/`.
5. `scripts/verify_results.py` checks all archived numerical CSV tables, including schema, row order, text values and floating-point values (relative tolerance 1e-6, absolute tolerance 1e-8).

`reproduce.py` performs these steps in order and records the actual software environment. The supplied `validation/` record distinguishes successful numerical reproduction from substantive identification or publication claims. PDF binary hashes need not match across systems because fonts and embedded metadata can vary; reference PDFs and numerical source tables are preserved.

## Packaging edits

Only repository paths were changed in the three main scripts, apart from removal of the unused Pesaran CD calculation. Its covariance assumptions after fixed-effects removal were not accepted in the paper. No alternative estimator was substituted, and no reported coefficient, bootstrap seed or sample rule was changed.

Baseline and panel reference tables are frozen reference results. New runs never overwrite them. Generated outputs and decompressed CSVs are ignored by Git.

## Optional records

`src/literature_screen.py` is optional and requires the original licensed Scopus exports (`literature/s1.csv` through `s5.csv`). Those records are not redistributed. Its paths are made repository-relative, and its outputs go to `outputs/literature/`. Search logs and counts are supplied in `literature/`; full literature screening cannot be independently rerun without the omitted exports.

Historical acquisition scripts remain in `source_extraction/` with their original working-file assumptions. They require additional geospatial libraries, source downloads and intermediate files, and were not rerun for this release. `requirements.txt` covers analytical reproduction, not historical acquisition. Services and products may change after the archived retrieval date.

## Scope

This package covers the urban-greening indicator analysis only.
