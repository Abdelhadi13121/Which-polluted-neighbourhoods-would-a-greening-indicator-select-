# Release validation

Full analytical reproduction completed on 6 October 2026.

- Python: 3.12.14; platform: Windows-11-10.0.26200-SP0.
- Bootstrap draws: 1000; seed: 20260930.
- Runtime: 169.7 seconds on the preparation machine.
- Archived CSV tables checked: **38**; all passed.
- Numeric tolerance: relative 1e-06, absolute 1e-08; schemas, row order and text columns also compared.
- Both analytical inputs restored losslessly and checked against original SHA-256 values.
- Four figures regenerated; PDF binary equality is not required because metadata/fonts can vary.

See `reproduction_check.json` for each table and `run_summary.json` for software versions. This verifies computational reproduction of archived tables, not causal identification. Historical web acquisition and optional licensed literature searches were not rerun.
