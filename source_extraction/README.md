# Historical source acquisition record

These scripts and manifests are preserved from the source package. They describe how the frozen analytical panel was acquired and assembled. They are not invoked by `reproduce.py`.

Several scripts expect `work/`, `work/geolibs/`, `outputs/`, geospatial dependencies and intermediate files from the original acquisition session. Live endpoints and source releases may change. Raw source archives and tiles are not bundled. Two historical download helpers containing access strings were already omitted from the supplied source package and remain excluded.

For a tested, offline analytical reproduction, use the compressed datasets under `data/archives/` and run `python reproduce.py` from the repository root. Source-level rebuilding is a separate workflow and is not certified by the analytical reproduction check.
