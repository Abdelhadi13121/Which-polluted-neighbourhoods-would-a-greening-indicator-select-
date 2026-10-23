# Data sources and acknowledgements

This is a derived research package, with source retrieval recorded as 28 September 2026 in the original provenance. It does not represent an official Eurostat, Copernicus or EEA product. It combines, aggregates, filters and analyses upstream information; conclusions are the authors' responsibility.

## Eurostat and GISCO

Population: Eurostat Census Grid 2021 V3. Spatial selection: GISCO 2021 functional urban areas. Cite the exact source files and checksums in `PROVENANCE.md`. Eurostat's general reuse policy allows reuse with acknowledgement, with exceptions for third-party and some geographic material. No original FUA boundary vector files are redistributed here; the derived grid retains cell IDs, coordinates and overlap/selection attributes.

GISCO's statistical-unit terms, checked on 6 October 2026, restrict the geographical source data to non-commercial use and require boundary attribution. The authors' CC BY notice does not override these conditions. This package contains derived selection and overlap attributes, not the original boundary vectors; it does not grant unrestricted commercial reuse of GISCO-derived material.

Boundary acknowledgement: **© EuroGeographics for the administrative boundaries**.

[GISCO statistical-unit copyright conditions](https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units)

[Eurostat copyright and reuse](https://ec.europa.eu/eurostat/help/copyright-notice)

## Copernicus Land Monitoring Service

Tree Cover Density 2018 and Urban Atlas 2018 class 14100 were aggregated or intersected with the analysis grid. The mapped-green availability mask is an extraction decision described in the provenance.

Generated using European Union's Copernicus Land Monitoring Service information. CLMS permits full, open and free access subject to source acknowledgement, disclosure of modifications and no implication of EU endorsement. Product access points:

- [Urban Atlas 2018](https://land.copernicus.eu/en/products/urban-atlas/urban-atlas-2018)
- [CLMS data policy](https://land.copernicus.eu/en/data-policy)

## European Environment Agency

The panel uses annual interpolated pollution surfaces. A 64-entry pollutant-year manifest provides dataset identifiers, URLs, release labels and checksums in `provenance/eea_source_manifest.csv`. The EEA general notice permits acknowledged reuse of material for which it holds the rights; individual exceptions still apply. Source meaning and limitations must be retained.

- [EEA legal notice](https://www.eea.europa.eu/en/legal-notice)
- [EEA interpolated air-quality series](https://www.eea.europa.eu/en/datahub/datahubitem-view/82700fbd-2953-467b-be0a-78a520c3a7ef)

## Package licensing scope

MIT covers original software contributions. CC BY 4.0 covers the authors' original derived-data, figure and documentation contributions to the extent they hold those rights. These notices do not convert third-party rights into authors' rights or remove upstream conditions.
