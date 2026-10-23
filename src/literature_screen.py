"""Reproducible screening log for the literature review (Sections 1 and 2).

Reads the five Scopus exports in literature/ (s1.csv to s5.csv), de-duplicates on EID, applies the keyword
flags defined below to title, abstract and keywords, and writes counts and the flagged records to
outputs/literature/. It also matches the references cited in Sections 1 and 2 to the Scopus exports (by DOI)
and, if consensus_rows.pkl is supplied, to the Consensus results (by title).

The flags are a coarse relevance screen on titles, abstracts and keywords. They are not a systematic review:
no full-text screening was done. The nearest records were then read by hand (titles of all flagged records,
abstracts of the closest ones; see the appendix text)."""
from pathlib import Path
import re, json, sys, pickle
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
LIT = HERE / 'literature'
OUT = HERE / 'outputs' / 'literature'
OUT.mkdir(parents=True, exist_ok=True)

SEARCHES = {
    's1': 'TITLE-ABS-KEY(("urban" OR "city") AND ("tree cover" OR "tree canopy" OR "green space" OR "urban vegetation") AND ("air pollution" OR "air quality" OR "PM2.5" OR "NO2") AND ("deposition" OR "dispersion" OR "concentration*")) AND PUBYEAR > 2004 AND DOCTYPE(ar OR re)',
    's2': 'TITLE-ABS-KEY(("greenspace" OR "green space" OR "tree canopy") AND ("NDVI" OR "land cover" OR "tree cover" OR "park*") AND ("metric*" OR "indicator*" OR "exposure assessment") AND ("compar*" OR "sensitiv*" OR "rank*"))',
    's3': 'TITLE-ABS-KEY(("environmental justice" OR "inequalit*" OR "disparit*") AND ("green space" OR "greenness" OR "tree canopy") AND ("air pollution" OR "NO2" OR "PM2.5") AND ("Europe*"))',
    's4': 'TITLE-ABS-KEY(("tree planting" OR "urban greening" OR "green infrastructure" OR "nature-based solution*") AND ("priorit*" OR "target*" OR "siting" OR "optimi*" OR "hotspot*") AND ("air pollution" OR "air quality" OR "exposure"))',
    's5': 'TITLE-ABS-KEY(("air quality map*" OR "land use regression" OR "kriging" OR "data fusion") AND ("uncertaint*" OR "validation") AND "Europe*") OR TITLE-ABS-KEY(("modifiable areal unit problem" OR "buffer size") AND ("greenspace" OR "green space") AND "exposure")',
}

GREEN = r"green ?space|greenspace|urban green|green infrastructure|ndvi|greenness|tree canopy|tree cover|urban forest|urban tree|vegetation"
POLL = r"no2|nitrogen dioxide|pm2\.?5|pm10|air pollution|air quality|particulate"
IND = r"indicator|metric|operationali[sz]|definition of|measure of"
PRIO = r"prioriti[sz]|priority areas|target(?:ing)? (?:of )?(?:investment|intervention|greening)|where to (?:plant|green)|siting|site selection|hotspot"
INEQ = r"inequit|inequalit|environmental justice|deprivation|socioeconomic|equity|disadvantage"
COMP = r"rank|ranking|compar|differ|sensitiv|robust|agree|consisten|discrepan"
EUR = r"europe|european|\beu\b|fua|functional urban"
DATA = r"urban atlas|copernicus|tree cover density|high resolution layer"


def load():
    frames = []
    for k in SEARCHES:
        df = pd.read_csv(LIT / f'{k}.csv')
        df['search'] = k
        frames.append(df)
    allr = pd.concat(frames, ignore_index=True)
    rows = len(allr)
    per = allr.groupby('search').size().to_dict()
    uniq = allr.sort_values('search').drop_duplicates('EID').copy()
    uniq['Cited by'] = pd.to_numeric(uniq['Cited by'], errors='coerce').fillna(0)
    uniq['txt'] = (uniq['Title'].fillna('') + ' ' + uniq['Abstract'].fillna('') + ' ' + uniq['Author Keywords'].fillna('')).str.lower()
    return allr, uniq, rows, per


def main():
    allr, uniq, rows, per = load()
    has = lambda p: uniq['txt'].str.contains(p, regex=True)
    g, p, i, pr, q, c, e, d = (has(x) for x in (GREEN, POLL, IND, PRIO, INEQ, COMP, EUR, DATA))
    counts = {
        'rows_exported': rows,
        'rows_per_search': per,
        'unique_records': len(uniq),
        'duplicates_removed': rows - len(uniq),
        'excluded_retracted_or_erratum_types': int(uniq['Document Type'].isin(['Retracted', 'Erratum']).sum()),
        'green_and_pollution': int((g & p).sum()),
        'green_pollution_indicator': int((g & p & i).sum()),
        'green_pollution_prioritisation': int((g & p & pr).sum()),
        'green_pollution_indicator_prioritisation': int((g & p & i & pr).sum()),
        'green_indicator_comparison_urban': int((g & i & c & has(r'city|cities|urban')).sum()),
        'green_pollution_inequality_europe': int((g & p & q & e).sum()),
        'copernicus_or_urban_atlas_data': int(d.sum()),
        'green_pollution_europe_data_prioritisation_indicator': int((g & p & e & d & pr & i).sum()),
    }
    flags = {'green_pollution_indicator_prioritisation': g & p & i & pr,
             'green_indicator_comparison_urban': g & i & c & has(r'city|cities|urban'),
             'green_pollution_inequality_europe': g & p & q & e,
             'copernicus_or_urban_atlas_data': d}
    cols = ['Authors', 'Year', 'Title', 'Source title', 'Cited by', 'DOI', 'Document Type', 'search']
    log = []
    for name, m in flags.items():
        sub = uniq[m][cols].copy(); sub.insert(0, 'flag', name); log.append(sub)
    pd.concat(log).sort_values(['flag', 'Cited by'], ascending=[True, False]).to_csv(OUT / 'scopus_flagged_records.csv', index=False, encoding='utf-8-sig')

    # provenance of the references cited in Sections 1 and 2
    md = (HERE / 'outputs' / 'manuscript' / 'intro_litreview.md').read_text(encoding='utf8')
    refs = md.split('### References (Sections 1 and 2)')[1].strip().split('\n\n')
    final = HERE / 'final_text' / 'main_text.md'
    if final.exists():                                    # keep only the references still cited in Sections 1 and 2 of the final text
        s12 = final.read_text(encoding='utf8').split('## 1. Introduction')[1].split('## 3. Data')[0]
        def in_s12(r):
            fam = r.split(',')[0].strip() if re.match(r'^[^(]+?, [A-Z]', r) else r.split(' (')[0]
            return fam in s12 and re.search(r'\((\d{4})\)', r).group(1) in s12
        refs = [r for r in refs if in_s12(r)]
    dois = {r.strip().lower() for r in uniq['DOI'].dropna()}
    cons_titles = set()
    pk = HERE.parent / 'nonexistent'
    sp = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if sp and sp.exists():
        cons = pickle.load(open(sp, 'rb'))
        cons_titles = {re.sub(r'[^a-z0-9]', '', r['title'].lower())[:60] for r in cons}
    prov = []
    for r in refs:
        m = re.search(r'doi:(\S+)', r)
        doi = m.group(1).lower().rstrip('.') if m else ''
        title = re.sub(r'[^a-z0-9]', '', (re.split(r'\(\d{4}\)\.\s', r)[1] if re.search(r'\(\d{4}\)\.\s', r) else r).lower())[:60]
        prov.append({'ref': r[:70], 'doi': doi, 'in_scopus_exports': doi in dois, 'in_consensus_results': any(title[:40] == t[:40] for t in cons_titles)})
    pdf = pd.DataFrame(prov)
    pdf.to_csv(OUT / 'cited_reference_provenance.csv', index=False, encoding='utf-8-sig')
    counts['cited_refs'] = len(pdf)
    counts['cited_in_scopus_only'] = int((pdf.in_scopus_exports & ~pdf.in_consensus_results).sum())
    counts['cited_in_consensus_only'] = int((~pdf.in_scopus_exports & pdf.in_consensus_results).sum())
    counts['cited_in_both'] = int((pdf.in_scopus_exports & pdf.in_consensus_results).sum())
    counts['cited_in_neither'] = int((~pdf.in_scopus_exports & ~pdf.in_consensus_results).sum())
    json.dump(counts, open(OUT / 'screening_counts.json', 'w'), indent=1)
    print(json.dumps(counts, indent=1))
    print(pdf[~pdf.in_scopus_exports & ~pdf.in_consensus_results][['ref', 'doi']].to_string())


if __name__ == '__main__':
    main()
