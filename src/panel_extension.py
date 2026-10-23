"""Panel extension of the European urban green-indicator screening paper.

Run (after paper_analysis.py has written outputs/original_script):
    python panel_extension.py            # full run, B = 1000 bootstrap draws
    python panel_extension.py --quick    # smoke test, B = 40

Reads european_urban_panel_2010_2025.csv (1,279,808 rows = 79,988 cells x 16 years) and the
outputs of paper_analysis.py. Writes outputs/panel_extension/*.csv and summary.json.

Design (all exploratory, no preregistration; associations are not causal effects):
  A. Reproduce the 2018 primary estimates and spatial block bootstrap of paper_analysis.py
     (same sample, same seeds, same estimator) and assert equality.
  B. Re-run the screening estimator for every pollution year 2010-2025, bootstrapping all
     years jointly from the same block resamples (5 km blocks).
  C. Out-of-time validity: persistence of eligibility and of priority sets relative to 2018.
  D. Panel gradient: cell fixed effects and city-by-year effects, canopy x year contrasts
     relative to 2018, with joint block-clustered covariance, sup-t bands and a trend contrast.
  E. Composition of the cells on which the two indicators disagree.
  F. Diagnostics: Moran's I, residual correlogram, selection into the Urban Atlas core,
     WHO / EU threshold exceedance, cross-city pooling (t, HKSJ random effects, sign tests).
  G. Robustness summary built from outputs/original_script/robustness_all.csv plus panel-based
     alternatives (multi-year mean pollution).
"""
from pathlib import Path
import argparse, json, time
import numpy as np
import pandas as pd
from scipy import stats, sparse
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[1]
PANEL = HERE / 'data' / 'european_urban_panel_2010_2025.csv'
SLIM = HERE / 'data' / 'paper_dataset.csv'
ORIG = HERE / 'outputs' / 'original_script'
OUT = HERE / 'outputs' / 'panel_extension'
ap = argparse.ArgumentParser()
ap.add_argument('--quick', action='store_true')
args = ap.parse_args()
OUT.mkdir(parents=True, exist_ok=True)

SEED = 20260930
B = 40 if args.quick else 1000
YEARS = list(range(2010, 2026))          # 2025 is an interim EEA release
MAIN = [y for y in YEARS if y <= 2024]
BASE = 2018
POLS = ['no2', 'pm25', 'pm10']
COL = {p: p + '_annual_ug_m3' for p in POLS}
WHO = {'no2': 10., 'pm25': 5., 'pm10': 15.}      # WHO 2021 annual guideline levels
EU30 = {'no2': 20., 'pm25': 10., 'pm10': 20.}    # EU Directive 2024/2881, limit values from 2030
SUMMARY = {}
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f}s]', *a, flush=True)

# ------------------------------------------------------------------ data
usecols = ['city', 'grid_id', 'x_3035', 'y_3035', 'population_2021', 'tree_cover_share_2018',
           'tree_valid_area_fraction_2018', 'urban_green_share_2018', 'year', 'aq_release_status',
           'within_reference_aq_coverage'] + list(COL.values())
df = pd.read_csv(PANEL, usecols=usecols)
base = df[df.year == BASE].reset_index(drop=True)
slim_ids = pd.read_csv(SLIM, usecols=['grid_id']).grid_id.values
assert (base.grid_id.values == slim_ids).all(), 'cell order differs from paper_dataset.csv'
CITIES = list(dict.fromkeys(base.city))
Qall = {}
for p in POLS:
    piv = df.pivot(index='grid_id', columns='year', values=COL[p]).reindex(base.grid_id)
    Qall[p] = piv[YEARS].to_numpy(float)                      # N_all x 16
pop = base.population_2021.to_numpy(float); tree = base.tree_cover_share_2018.to_numpy(float)
green = base.urban_green_share_2018.to_numpy(float); cover = base.tree_valid_area_fraction_2018.to_numpy(float)
x = base.x_3035.to_numpy(float); y = base.y_3035.to_numpy(float); city = base.city.to_numpy()
log('panel loaded', df.shape, 'cells', len(base))

# sample construction (identical to paper_analysis.estimate_main)
finite3 = np.logical_and.reduce([np.isfinite(Qall[p][:, YEARS.index(BASE)]) for p in POLS])
steps = [('All FUA grid cells', np.ones(len(base), bool)),
         ('+ population > 0', pop > 0),
         ('+ air-quality maps available', (pop > 0) & finite3),
         ('+ tree cover valid (>= 95% of area)', (pop > 0) & finite3 & np.isfinite(tree) & (cover >= .95)),
         ('+ Urban Atlas green share available (common sample)',
          (pop > 0) & finite3 & np.isfinite(tree) & (cover >= .95) & np.isfinite(green))]
rows = []
for name, m in steps:
    rows.append(dict(step=name, cells=int(m.sum()), population_2021=float(np.nansum(pop[m])),
                     **{c: int((m & (city == c)).sum()) for c in CITIES}))
pd.DataFrame(rows).to_csv(OUT / 'sample_construction.csv', index=False)
MASK = steps[-1][1]
IDS = {c: np.flatnonzero(MASK & (city == c)) for c in CITIES}
assert sum(len(v) for v in IDS.values()) == 7833, 'common sample is not 7,833 cells'
# every common-sample cell must have a finite value in every year
for p in POLS:
    assert np.isfinite(Qall[p][MASK]).all(), 'missing pollution in common sample'
SUMMARY['common_cells'] = int(MASK.sum()); SUMMARY['common_population'] = float(pop[MASK].sum())

# ------------------------------------------------------------------ estimator (verbatim logic)
def alloc(v, k):
    cut = np.sort(v)[k - 1]; forced = v < cut; tied = v == cut; remaining = k - int(forced.sum())
    return forced.astype(float) + tied * remaining / tied.sum(), forced, tied, remaining

def est_fast(T, G, P, Q, q=.75, b=.2):
    idx = np.flatnonzero(Q >= np.quantile(Q, q)); k = int(len(idx) * b)
    if k < 5: return None
    t, g, p, qq = T[idx], G[idx], P[idx], Q[idx]
    a = alloc(t, k)[0]; c = alloc(g, k)[0]
    ov = a @ c / k; bs = k / len(idx); cp, gp = a @ p, c @ p
    return np.array([1 - ov, (ov - bs) / (1 - bs), cp - gp, (a - c) @ qq / k,
                     cp / gp - 1 if gp > 0 else np.nan, ov, cp, gp])
METRICS = ['replacement', 'kappa', 'pop_diff', 'poll_diff', 'rel_pop_diff', 'overlap', 'canopy_pop', 'green_pop']

def sets(T, G, Q, q=.75, b=.2):
    """Priority-set allocation vectors over all cells of a city (zeros outside eligibility)."""
    idx = np.flatnonzero(Q >= np.quantile(Q, q)); k = int(len(idx) * b)
    a = np.zeros(len(T)); c = np.zeros(len(T))
    if k < 5: return None
    a[idx] = alloc(T[idx], k)[0]; c[idx] = alloc(G[idx], k)[0]
    return a, c, idx, k

def blocks_for(ids, km):
    keys = np.column_stack((np.floor(x[ids] / (km * 1000)), np.floor(y[ids] / (km * 1000))))
    _, inv = np.unique(keys, axis=0, return_inverse=True); inv = np.asarray(inv).ravel()
    return inv, [np.flatnonzero(inv == j) for j in range(inv.max() + 1)]

# ------------------------------------------------------------------ A + B: screening estimates by year
log('A/B: point estimates and joint block bootstrap for all years')
pt_rows, boot_store = [], {}
for ci, ct in enumerate(CITIES):
    ids = IDS[ct]; T, G, P = tree[ids], green[ids], pop[ids]
    inv, blocks = blocks_for(ids, 5)
    for pi_, pol in enumerate(POLS):
        Qm = Qall[pol][ids]
        pts = np.array([est_fast(T, G, P, Qm[:, j]) for j in range(len(YEARS))])
        rng = np.random.default_rng(SEED + ci * 100 + 5 + pi_ * 10000)   # same stream as paper_analysis.py
        draws = np.full((B, len(YEARS), len(METRICS)), np.nan)
        for rep in range(B):
            ii = np.concatenate([blocks[j] for j in rng.integers(0, len(blocks), len(blocks))])
            Tb, Gb, Pb = T[ii], G[ii], P[ii]
            for j in range(len(YEARS)):
                e = est_fast(Tb, Gb, Pb, Qm[ii, j])
                if e is not None: draws[rep, j] = e
        boot_store[(ct, pol)] = draws
        for j, yr in enumerate(YEARS):
            r = dict(city=ct, pollutant=pol, year=yr, blocks_5km=len(blocks))
            for m, name in enumerate(METRICS):
                d = draws[:, j, m]; d = d[np.isfinite(d)]
                r[name] = pts[j, m]
                if name in ('replacement', 'kappa', 'pop_diff', 'poll_diff', 'rel_pop_diff'):
                    r[name + '_se'] = d.std(ddof=1); r[name + '_lo'] = np.quantile(d, .025); r[name + '_hi'] = np.quantile(d, .975)
            pt_rows.append(r)
    log('  done', ct)
cy = pd.DataFrame(pt_rows); cy.to_csv(OUT / 'city_year_estimates.csv', index=False)

# A: assert reproduction of the original 2018 results
pe = pd.read_csv(ORIG / 'primary_estimates.csv'); sr = pd.read_csv(ORIG / 'spatial_resampling.csv')
chk = cy[cy.year == BASE].merge(pe, on=['city', 'pollutant'])
assert np.allclose(chk.replacement_x, chk.replacement_y, atol=1e-9), 'replacement differs from original script'
assert np.allclose(chk.kappa, chk.chance_adjusted_overlap, atol=1e-9), 'kappa differs from original script'
assert np.allclose(chk.pop_diff, chk.population_difference, atol=1e-6)
# The panel stores pollution to 6-7 decimals, paper_dataset.csv to ~15 (max gap 5e-7 ug/m3), so the
# pollution contrast is compared at 1e-5; set-based metrics (overlap, kappa, population) match to 1e-9.
assert np.allclose(chk.poll_diff, chk.pollution_difference, atol=1e-5)
if not args.quick:
    s5 = sr[(sr.block_km == 5) & (sr.metric == 'chance_adjusted_overlap')].merge(
        cy[cy.year == BASE][['city', 'pollutant', 'kappa_lo', 'kappa_hi']], on=['city', 'pollutant'])
    dev = max(np.abs(s5.spatial_resampling_p025 - s5.kappa_lo).max(), np.abs(s5.spatial_resampling_p975 - s5.kappa_hi).max())
    SUMMARY['bootstrap_reproduction_max_abs_dev_kappa_ci'] = float(dev)
    assert dev < 5e-3, f'bootstrap interval differs from original by {dev}'
    log(f'A: 2018 point estimates reproduce paper_analysis.py; 5 km bootstrap kappa intervals match to {dev:.2e}')
else:
    log('A: point estimates reproduce paper_analysis.py (bootstrap check skipped in --quick)')

# ------------------------------------------------------------------ pooling across cities
def pool(theta, v=None, bench=None):
    theta = np.asarray(theta, float); n = len(theta); out = dict(n=n, mean=theta.mean(), sd=theta.std(ddof=1))
    se = out['sd'] / np.sqrt(n); tcrit = stats.t.ppf(.975, n - 1)
    out.update(se=se, t_lo=theta.mean() - tcrit * se, t_hi=theta.mean() + tcrit * se,
               min=theta.min(), max=theta.max())
    if bench is not None:
        out['bench'] = bench; out['n_below'] = int((theta < bench).sum()); out['n_above'] = int((theta > bench).sum())
        out['sign_p'] = stats.binomtest(int((theta < bench).sum()), int(((theta < bench) | (theta > bench)).sum()), .5).pvalue
        try: out['wilcoxon_p'] = stats.wilcoxon(theta - bench, method='exact').pvalue
        except Exception: out['wilcoxon_p'] = np.nan
        out['t_p'] = stats.ttest_1samp(theta, bench).pvalue
    if v is not None:
        v = np.asarray(v, float); w = 1 / v; fe = (w * theta).sum() / w.sum(); Q = (w * (theta - fe) ** 2).sum(); df_ = n - 1
        tau2 = max(0., (Q - df_) / (w.sum() - (w ** 2).sum() / w.sum())); ws = 1 / (v + tau2); mu = (ws * theta).sum() / ws.sum()
        qh = (ws * (theta - mu) ** 2).sum() / df_; se_hk = np.sqrt(max(qh, 1.) / ws.sum())
        out.update(re_mean=mu, re_se=se_hk, re_lo=mu - tcrit * se_hk, re_hi=mu + tcrit * se_hk, tau2=tau2,
                   I2=max(0., (Q - df_) / Q), Q=Q, Q_p=1 - stats.chi2.cdf(Q, df_),
                   pi_lo=mu - stats.t.ppf(.975, n - 2) * np.sqrt(tau2 + se_hk ** 2),
                   pi_hi=mu + stats.t.ppf(.975, n - 2) * np.sqrt(tau2 + se_hk ** 2))
    return out

BENCH = {'kappa': 0.5, 'replacement': 0.5, 'rel_pop_diff': 0.0, 'poll_diff': 0.0}
prow = []
for pol in POLS:
    for yr in YEARS:
        s = cy[(cy.pollutant == pol) & (cy.year == yr)].set_index('city').loc[CITIES]
        for m in ['kappa', 'replacement', 'rel_pop_diff', 'poll_diff']:
            pr = pool(s[m], v=s[m + '_se'] ** 2, bench=BENCH[m])
            # fixed-city bootstrap interval of the equal-weight mean (within-city sampling uncertainty only)
            dm = np.nanmean(np.stack([boot_store[(c, pol)][:, YEARS.index(yr), METRICS.index(m)] for c in CITIES]), axis=0)
            pr.update(boot_lo=np.nanquantile(dm, .025), boot_hi=np.nanquantile(dm, .975), boot_se=np.nanstd(dm, ddof=1))
            prow.append(dict(pollutant=pol, year=yr, metric=m, **pr))
py_ = pd.DataFrame(prow); py_.to_csv(OUT / 'pooled_year_estimates.csv', index=False)

# temporal-stability test of the pooled kappa path (base 2018). Two windows: the full 2010-2024 series and
# the 2015-2024 window chosen after the consecutive-year rank diagnostic (below) showed a discontinuity in the
# particulate-matter map series between 2014 and 2015. Both are reported; neither is preregistered.
WINDOWS = {'2010-2024': MAIN, '2015-2024': [y for y in MAIN if y >= 2015]}
stab = []
for wname, wyears in WINDOWS.items():
    for pol in POLS:
        for m in ['kappa', 'replacement']:
            path = np.array([cy[(cy.pollutant == pol) & (cy.year == yr)].set_index('city').loc[CITIES][m].mean() for yr in wyears])
            dr = np.stack([np.nanmean(np.stack([boot_store[(c, pol)][:, YEARS.index(yr), METRICS.index(m)] for c in CITIES]), axis=0) for yr in wyears], axis=1)  # B x years
            yrs = np.array(wyears, float); w = (yrs - yrs.mean()) / ((yrs - yrs.mean()) ** 2).sum()
            slope = w @ path; sd = dr @ w
            bi_ = wyears.index(BASE); dlt = path - path[bi_]; dd = dr - dr[:, [bi_]]; se_t = np.nanstd(dd, axis=0, ddof=1); se_t[bi_] = np.nan
            ok_ = np.arange(len(wyears)) != bi_
            tobs = np.nanmax(np.abs(dlt[ok_] / se_t[ok_])); tdr = np.nanmax(np.abs((dd[:, ok_] - dlt[ok_]) / se_t[ok_]), axis=1)
            stab.append(dict(window=wname, pollutant=pol, metric=m, path_min=path.min(), path_max=path.max(), path_first=path[0], path_2018=path[bi_], path_2024=path[-1],
                             slope_per_year=slope, slope_lo=np.nanquantile(sd, .025), slope_hi=np.nanquantile(sd, .975), slope_se=np.nanstd(sd, ddof=1),
                             mde80_slope=2.8 * np.nanstd(sd, ddof=1), max_abs_dev_from_2018=np.abs(dlt[ok_]).max(), supt_stat=tobs, supt_p=float(np.nanmean(tdr >= tobs)), supt_crit95=np.nanquantile(tdr, .95)))
pd.DataFrame(stab).to_csv(OUT / 'temporal_stability.csv', index=False)
log('B: temporal-stability tests done')

# map-series diagnostic: within-city rank correlation between consecutive years (common sample)
cons = []
for pol in POLS:
    for j in range(len(YEARS) - 1):
        r_ = [stats.spearmanr(Qall[pol][IDS[c], j], Qall[pol][IDS[c], j + 1]).statistic for c in CITIES]
        cons.append(dict(pollutant=pol, year_from=YEARS[j], year_to=YEARS[j + 1], mean_rho=float(np.mean(r_)), min_rho=float(np.min(r_)), max_rho=float(np.max(r_))))
pd.DataFrame(cons).to_csv(OUT / 'consecutive_rank_corr.csv', index=False)

# ------------------------------------------------------------------ C: out-of-time validity
prs = []
for ct in CITIES:
    ids = IDS[ct]; T, G = tree[ids], green[ids]
    for pol in POLS:
        Qm = Qall[pol][ids]; s18 = sets(T, G, Qm[:, YEARS.index(BASE)])
        a18, c18, e18, k18 = s18; E18 = np.zeros(len(ids), bool); E18[e18] = True
        for j, yr in enumerate(YEARS):
            st = sets(T, G, Qm[:, j]); at, cc, et, kt = st; Et = np.zeros(len(ids), bool); Et[et] = True
            rs_ = stats.spearmanr(Qm[:, YEARS.index(BASE)], Qm[:, j]).statistic
            prs.append(dict(city=ct, pollutant=pol, year=yr, spearman_vs_2018=rs_, eligible_retention=(E18 & Et).sum() / E18.sum(),
                            canopy_set_retention=at @ a18 / kt, green_set_retention=cc @ c18 / kt,
                            canopy_chance=kt / Et.sum(), n=len(ids)))
sp_ = pd.DataFrame(prs); sp_.to_csv(OUT / 'set_persistence.csv', index=False)
# non-monotonic decay diagnostic: Spearman against the year gap (all cities pooled, NO2)
g = sp_[(sp_.pollutant == 'no2')].groupby('year').spearman_vs_2018.mean()
SUMMARY['spearman_no2_by_year'] = {int(k): float(v) for k, v in g.items()}

# ------------------------------------------------------------------ cluster-robust machinery
def design(ids, spatial=False):
    t, g_, p = tree[ids], green[ids], pop[ids]; c = city[ids]; cs = list(dict.fromkeys(c))
    D = np.column_stack([c == k for k in cs]).astype(float)
    X = np.column_stack([t / .1, g_ / .1, np.log(p), D])
    if spatial:
        sp = []
        for k in cs:
            m = c == k; xx = (x[ids] - x[ids][m].mean()) / 1e4; yy = (y[ids] - y[ids][m].mean()) / 1e4
            sp.extend([m * xx, m * yy, m * xx * xx, m * yy * yy, m * xx * yy])
        X = np.column_stack([X, *sp])
    return X

def cluster_inv(ids, km):
    keys = [(a, int(b // (km * 1000)), int(d // (km * 1000))) for a, b, d in zip(city[ids], x[ids], y[ids])]
    lk = {z: i for i, z in enumerate(dict.fromkeys(keys))}
    return np.array([lk[z] for z in keys]), len(lk)

def ols_multi(X, Y, inv, ng):
    """OLS of each column of Y on X; joint CR1 covariance across columns, clustered on inv.
    Returns coef (K x m) and V over vec(coef) ordered column-major by outcome (outcome-major blocks)."""
    n, k = X.shape; m = Y.shape[1]; A = np.linalg.pinv(X.T @ X)
    coef = A @ X.T @ Y; res = Y - X @ coef
    M = sparse.csr_matrix((np.ones(n), (inv, np.arange(n))), shape=(ng, n))
    U = np.zeros((ng, m * k))
    for j in range(m):
        S = M @ (X * res[:, [j]]); U[:, j * k:(j + 1) * k] = S @ A
    V = U.T @ U * (ng / (ng - 1)) * ((n - 1) / (n - k))
    return coef, V, res, np.linalg.matrix_rank(X)

# ------------------------------------------------------------------ original adjusted associations (replicated) + heterogeneity
log('replicating adjusted associations and testing slope heterogeneity')
allids = np.concatenate([IDS[c] for c in CITIES])
assoc_rows, het_rows = [], []
for spec, sflag in [('city_FE', False), ('city_FE_city_quadratic_spatial_trends', True)]:
    X = design(allids, sflag)
    for km in [5, 10]:
        inv, ng = cluster_inv(allids, km)
        for pol in POLS:
            Yv = Qall[pol][allids, YEARS.index(BASE)][:, None]
            coef, V, res, rk = ols_multi(X, Yv, inv, ng); se = np.sqrt(np.diag(V))
            r2 = 1 - (res ** 2).sum() / ((Yv - Yv.mean()) ** 2).sum()
            for j, term in enumerate(['canopy_per_10_percentage_points', 'ua_green_per_10_percentage_points', 'log_population_2021']):
                assoc_rows.append(dict(pollutant=pol, model=spec, term=term, coefficient_ug_m3=coef[j, 0], spatial_cluster_se=se[j],
                                       block_km=km, clusters=ng, n=len(allids), design_rank=rk, design_columns=X.shape[1], r_squared=r2,
                                       pct_of_sample_mean=100 * coef[j, 0] / Yv.mean()))
# check against original
ao = pd.read_csv(ORIG / 'adjusted_associations.csv'); ar = pd.DataFrame(assoc_rows)
mm = ao.merge(ar, on=['pollutant', 'model', 'term', 'block_km'], suffixes=('_o', '_n'))
assert len(mm) == len(ao) and np.allclose(mm.coefficient_ug_m3_o, mm.coefficient_ug_m3_n, atol=1e-8) and np.allclose(mm.spatial_cluster_se_o, mm.spatial_cluster_se_n, atol=1e-8)
log('  adjusted associations reproduce paper_analysis.py')
# slope heterogeneity: canopy x city and green x city interactions, Wald test of equal slopes
cs_ = CITIES
for spec, sflag in [('city_FE', False), ('city_FE_city_quadratic_spatial_trends', True)]:
    X0 = design(allids, sflag); c_ = city[allids]
    for var, j0 in [('canopy', 0), ('ua_green', 1)]:
        Xi = np.column_stack([X0[:, j0:j0 + 1] * (c_ == k)[:, None] for k in cs_] + [X0[:, [1 - j0]], X0[:, 2:]])
        inv, ng = cluster_inv(allids, 10)
        for pol in POLS:
            Yv = Qall[pol][allids, YEARS.index(BASE)][:, None]
            coef, V, res, rk = ols_multi(Xi, Yv, inv, ng); b = coef[:10, 0]; Vb = V[:10, :10]
            R = np.hstack([np.eye(9), -np.ones((9, 1))]) @ np.eye(10) if False else (np.eye(10)[:-1] - np.eye(10)[1:])[:9]
            Rb = R @ b; W = Rb @ np.linalg.solve(R @ Vb @ R.T, Rb)
            for kk, ct in enumerate(cs_):
                het_rows.append(dict(spec=spec, variable=var, pollutant=pol, city=ct, slope_per_10pp=b[kk], se=np.sqrt(Vb[kk, kk]),
                                     wald_equal_slopes=W, wald_df=9, wald_p_chi2=1 - stats.chi2.cdf(W, 9), wald_p_F=1 - stats.f.cdf(W / 9, 9, ng - 1), clusters=ng))
pd.DataFrame(assoc_rows).to_csv(OUT / 'associations_replicated.csv', index=False)
het = pd.DataFrame(het_rows); het.to_csv(OUT / 'association_heterogeneity.csv', index=False)
# within-city SD of canopy (for per-SD conversions)
tw = tree[allids] - pd.Series(tree[allids]).groupby(city[allids]).transform('mean').to_numpy()
SUMMARY['canopy_within_city_sd'] = float(tw.std(ddof=1)); SUMMARY['canopy_pooled_sd'] = float(tree[allids].std(ddof=1))
SUMMARY['no2_2018_mean_common'] = float(Qall['no2'][allids, YEARS.index(BASE)].mean())

# ------------------------------------------------------------------ D: panel gradient (cell FE, city x year effects)
log('D: panel gradient contrasts relative to 2018')
bi = YEARS.index(BASE); others = [j for j in range(len(YEARS)) if j != bi]; oy = [YEARS[j] for j in others]
grad_rows, grad_sum = [], []
rng_s = np.random.default_rng(SEED)
for pol in POLS:
    LY = np.log(Qall[pol][allids]); DY = LY[:, others] - LY[:, [bi]]            # N x 15, log-point changes relative to 2018
    for spec, sflag in [('baseline', False), ('spatial_trends', True)]:
        X = design(allids, sflag)
        for km in [5, 10]:
            inv, ng = cluster_inv(allids, km); coef, V, res, rk = ols_multi(X, DY, inv, ng); K = X.shape[1]; Tn = len(others)
            for term_i, term in enumerate(['canopy', 'ua_green', 'log_population']):
                idx = [t * K + term_i for t in range(Tn)]; b = coef[term_i, :]; Vt = V[np.ix_(idx, idx)]; se = np.sqrt(np.diag(Vt))
                main_mask = np.array([yr <= 2024 for yr in oy])
                Vm = Vt[np.ix_(main_mask, main_mask)]; bm = b[main_mask]; sem = se[main_mask]
                corr = Vm / np.outer(sem, sem); sim = rng_s.multivariate_normal(np.zeros(len(bm)), corr, size=200000, method='eigh')
                crit = np.quantile(np.abs(sim).max(axis=1), .95); tobs = np.abs(bm / sem).max(); psup = float((np.abs(sim).max(axis=1) >= tobs).mean())
                ev, evec = np.linalg.eigh(Vm); keep = ev > ev.max() * 1e-8; Wd = (bm @ evec[:, keep]) ** 2 @ (1 / ev[keep])
                for t_, yr in enumerate(oy):
                    grad_rows.append(dict(pollutant=pol, spec=spec, block_km=km, term=term, year=yr, coef_log_pts_per_10pp=b[t_], se=se[t_], pct=100 * (np.exp(b[t_]) - 1),
                                          lo=b[t_] - 1.96 * se[t_], hi=b[t_] + 1.96 * se[t_], supt_lo=b[t_] - crit * se[t_] if yr <= 2024 else np.nan,
                                          supt_hi=b[t_] + crit * se[t_] if yr <= 2024 else np.nan, interim=int(yr == 2025), clusters=ng))
                # window-specific tests; the base-year coefficient is zero by construction and enters the trend with zero variance
                for wname, wyears in WINDOWS.items():
                    sel = np.array([yr in wyears for yr in oy]); bw = b[sel]; Vw = Vt[np.ix_(sel, sel)]; sw = np.sqrt(np.diag(Vw))
                    simw = rng_s.multivariate_normal(np.zeros(len(bw)), Vw / np.outer(sw, sw), size=200000, method='eigh'); mx = np.abs(simw).max(axis=1)
                    critw = np.quantile(mx, .95); tobsw = np.abs(bw / sw).max(); psupw = float((mx >= tobsw).mean())
                    ev, evec = np.linalg.eigh(Vw); keep = ev > ev.max() * 1e-8; Wd = (bw @ evec[:, keep]) ** 2 @ (1 / ev[keep])
                    yrs = np.array(wyears, float); wt = (yrs - yrs.mean()) / ((yrs - yrs.mean()) ** 2).sum()
                    wfull = np.array([wt[wyears.index(yr)] for yr in oy if yr in wyears])        # weights on the non-base years of the window
                    slope = wfull @ bw; slope_se = np.sqrt(wfull @ Vw @ wfull)
                    # step test between the 2010-2014 and 2015-2019 vintages (mean contrast), base year contributes 0
                    pre = np.array([1 / 5 if 2010 <= yr <= 2014 else 0. for yr in oy]); post = np.array([1 / 5 if (2015 <= yr <= 2019 and yr != BASE) else 0. for yr in oy])
                    stp = (pre - post) @ b; stp_se = np.sqrt((pre - post) @ Vt @ (pre - post))
                    grad_sum.append(dict(window=wname, pollutant=pol, spec=spec, block_km=km, term=term, clusters=ng, n=len(allids), supt_crit=critw, supt_max_abs_t=tobsw, supt_p=psupw,
                                         wald=Wd, wald_rank=int(keep.sum()), wald_p=1 - stats.chi2.cdf(Wd, int(keep.sum())),
                                         trend_log_pts_per_year=slope, trend_se=slope_se, trend_pct_per_year=100 * slope, trend_lo=100 * (slope - 1.96 * slope_se), trend_hi=100 * (slope + 1.96 * slope_se),
                                         mde80_trend_pct=100 * 2.8 * slope_se, mde80_pointwise_pct_min=100 * 2.8 * sw.min(), mde80_pointwise_pct_max=100 * 2.8 * sw.max(),
                                         max_abs_coef_pct=100 * np.abs(bw).max(), step_pre_minus_post_pct=100 * stp, step_se_pct=100 * stp_se, step_z=stp / stp_se))
pd.DataFrame(grad_rows).to_csv(OUT / 'gradient_panel.csv', index=False)
pd.DataFrame(grad_sum).to_csv(OUT / 'gradient_summary.csv', index=False)

# cross-sectional level gradient by year (city FE, per 10 pp canopy) for the descriptive path
lvl = []
X = design(allids, False); inv, ng = cluster_inv(allids, 10)
for pol in POLS:
    Ym = Qall[pol][allids]; coef, V, res, rk = ols_multi(X, Ym, inv, ng); K = X.shape[1]
    for t_, yr in enumerate(YEARS):
        lvl.append(dict(pollutant=pol, year=yr, canopy_coef=coef[0, t_], canopy_se=np.sqrt(V[t_ * K, t_ * K]), green_coef=coef[1, t_], green_se=np.sqrt(V[t_ * K + 1, t_ * K + 1]),
                        mean_level=Ym[:, t_].mean(), canopy_pct_of_mean=100 * coef[0, t_] / Ym[:, t_].mean()))
pd.DataFrame(lvl).to_csv(OUT / 'gradient_levels_by_year.csv', index=False)

# ------------------------------------------------------------------ E: composition of the cells on which the indicators disagree (NO2, 2018)
log('E: disagreement groups')
grp, rows_lpm = [], []
Dcells = []
for ct in CITIES:
    ids = IDS[ct]; T, G, P = tree[ids], green[ids], pop[ids]; Q = Qall['no2'][ids, bi]
    a, c, idx, k = sets(T, G, Q)
    cx = (P * x[ids]).sum() / P.sum(); cyy = (P * y[ids]).sum() / P.sum(); dist = np.hypot(x[ids] - cx, y[ids] - cyy) / 1000
    z = lambda v: (v - v.mean()) / v.std(ddof=1)
    Dcells.append(pd.DataFrame(dict(city=ct, i=ids[idx], a=a[idx], c=c[idx], pop=P[idx], no2=Q[idx], dist=dist[idx], z_lnpop=z(np.log(P))[idx], z_no2=z(Q)[idx], z_dist=z(dist)[idx],
                                    canopy=T[idx], green=G[idx])))
Dc = pd.concat(Dcells, ignore_index=True)
w_both = Dc.a * Dc.c; w_can = Dc.a * (1 - Dc.c); w_grn = (1 - Dc.a) * Dc.c
for name, w in [('canopy_only', w_can), ('both', w_both), ('green_only', w_grn)]:
    grp.append(dict(group=name, expected_cells=w.sum(), mean_population=np.average(Dc['pop'], weights=w), mean_no2=np.average(Dc.no2, weights=w), mean_dist_km=np.average(Dc.dist, weights=w),
                    mean_canopy=np.average(Dc.canopy, weights=w), mean_green=np.average(Dc.green, weights=w), share_green_zero=np.average((Dc.green == 0).astype(float), weights=w)))
pd.DataFrame(grp).to_csv(OUT / 'disagreement_groups.csv', index=False)
Dc['d'] = Dc.a - Dc.c
Xc = np.column_stack([Dc.z_lnpop, Dc.z_no2, Dc.z_dist, pd.get_dummies(Dc.city).to_numpy(float)])
keys = [(a_, int(b_ // 10000), int(d_ // 10000)) for a_, b_, d_ in zip(Dc.city, x[Dc.i], y[Dc.i])]
lk = {z_: i for i, z_ in enumerate(dict.fromkeys(keys))}; invc = np.array([lk[z_] for z_ in keys])
for dep in ['a', 'c', 'd']:
    coef, V, res, rk = ols_multi(Xc, Dc[[dep]].to_numpy(float), invc, len(lk)); se = np.sqrt(np.diag(V))
    for j, nm in enumerate(['z_log_population', 'z_no2', 'z_distance_to_centre']):
        rows_lpm.append(dict(dependent={'a': 'canopy_selection_prob', 'c': 'green_selection_prob', 'd': 'difference_canopy_minus_green'}[dep], term=nm, coef=coef[j, 0], se=se[j], p=2 * (1 - stats.norm.cdf(abs(coef[j, 0] / se[j]))), n=len(Dc), clusters=len(lk)))
pd.DataFrame(rows_lpm).to_csv(OUT / 'disagreement_lpm.csv', index=False)
# exposure-weighted burden (persons x ug/m3) covered by each priority set, primary year 2018
bur = []
for ct in CITIES:
    ids = IDS[ct]; P_ = pop[ids]
    for pol in POLS:
        Q_ = Qall[pol][ids, bi]; a_, c_, idx_, k_ = sets(tree[ids], green[ids], Q_)
        bc, bg = a_ @ (P_ * Q_), c_ @ (P_ * Q_)
        bur.append(dict(city=ct, pollutant=pol, burden_canopy=bc, burden_green=bg, rel_burden_diff=bc / bg - 1))
bur = pd.DataFrame(bur); bur.to_csv(OUT / 'burden_by_city.csv', index=False)
bp = []
for pol in POLS:
    pr = pool(bur[bur.pollutant == pol].rel_burden_diff, bench=0.0); bp.append(dict(pollutant=pol, **pr))
pd.DataFrame(bp).to_csv(OUT / 'burden_pooled.csv', index=False)
# tie diagnostics
tie = []
for ct in CITIES:
    ids = IDS[ct]; Q = Qall['no2'][ids, bi]; a, c, idx, k = sets(tree[ids], green[ids], Q)
    g_ = green[ids][idx]; cut = np.sort(g_)[k - 1]
    tie.append(dict(city=ct, eligible=len(idx), slots=k, green_zero_share_eligible=float((g_ == 0).mean()), green_tied_cells=int((g_ == cut).sum()), green_cut_value=float(cut),
                    share_of_green_slots_from_ties=float(c[idx][g_ == cut].sum() / k)))
pd.DataFrame(tie).to_csv(OUT / 'tie_diagnostics.csv', index=False)
# A slot is ambiguous only if the cut-off value is shared by more than one eligible cell (a single cell at the cut-off is selected with certainty).
tie_all = []
for pol in POLS:
    for ct in CITIES:
        ids = IDS[ct]; Qm = Qall[pol][ids, bi]; _, _, idx_, k_ = sets(tree[ids], green[ids], Qm)
        for nm, v in [('canopy', tree[ids][idx_]), ('green', green[ids][idx_])]:
            cut_ = np.sort(v)[k_ - 1]; forced_ = int((v < cut_).sum()); tied_ = int((v == cut_).sum()); rem_ = k_ - forced_
            tie_all.append(dict(pollutant=pol, city=ct, indicator=nm, slots=k_, cut_value=float(cut_), tied_cells=tied_, slots_remaining_for_ties=rem_, ambiguous_slots=rem_ if tied_ > 1 else 0))
tie_all = pd.DataFrame(tie_all); tie_all.to_csv(OUT / 'tie_diagnostics_all.csv', index=False)

# ------------------------------------------------------------------ F: diagnostics
log('F: Moran, correlogram, selection into the Urban Atlas core, exceedance')
mor = []; rngm = np.random.default_rng(SEED + 7)
def moran(z, nbr):
    z = z - z.mean(); return float((z * z[nbr].mean(axis=1)).sum() / (z * z).sum())
for ct in CITIES:
    ids = IDS[ct]; tr = cKDTree(np.column_stack([x[ids], y[ids]])); _, nbr = tr.query(np.column_stack([x[ids], y[ids]]), k=9); nbr = nbr[:, 1:]
    for nm, v in [('NO2_2018', Qall['no2'][ids, bi]), ('PM25_2018', Qall['pm25'][ids, bi]), ('canopy', tree[ids]), ('ua_green', green[ids]), ('log_population', np.log(pop[ids]))]:
        I = moran(v, nbr); perm = np.array([moran(rngm.permutation(v), nbr) for _ in range(199)])
        mor.append(dict(city=ct, variable=nm, n=len(ids), morans_I=I, perm_mean=perm.mean(), perm_sd=perm.std(ddof=1), z=(I - perm.mean()) / perm.std(ddof=1), pseudo_p=(1 + (perm >= I).sum()) / 200))
pd.DataFrame(mor).to_csv(OUT / 'morans_i.csv', index=False)
# residual correlogram for NO2 (spec: city FE; and with spatial trends)
cg = []
for spec, sflag in [('city_FE', False), ('city_FE_city_quadratic_spatial_trends', True)]:
    X = design(allids, sflag); Yv = Qall['no2'][allids, bi][:, None]; coef, V, res, rk = ols_multi(X, Yv, *cluster_inv(allids, 10)); e = res[:, 0]
    bins = [(0, 1.5), (1.5, 2.5), (2.5, 3.5), (3.5, 5.5), (5.5, 10.5), (10.5, 20.5)]; num = np.zeros(len(bins)); den = np.zeros(len(bins)); npairs = np.zeros(len(bins))
    off = 0
    for ct in CITIES:
        n_ = len(IDS[ct]); ee = e[off:off + n_]; off += n_; xy = np.column_stack([x[IDS[ct]], y[IDS[ct]]]); pr = cKDTree(xy).query_pairs(20500, output_type='ndarray')
        d_ = np.hypot(*(xy[pr[:, 0]] - xy[pr[:, 1]]).T) / 1000; prod = ee[pr[:, 0]] * ee[pr[:, 1]]
        for bi_, (lo_, hi_) in enumerate(bins):
            m = (d_ > lo_) & (d_ <= hi_); num[bi_] += prod[m].sum(); npairs[bi_] += m.sum()
    for bi_, (lo_, hi_) in enumerate(bins):
        cg.append(dict(spec=spec, dist_lo_km=lo_, dist_hi_km=hi_, pairs=int(npairs[bi_]), residual_correlation=num[bi_] / npairs[bi_] / (e ** 2).mean()))
pd.DataFrame(cg).to_csv(OUT / 'correlogram.csv', index=False)

# selection into the common sample
inhab = (pop > 0) & finite3
cv = []
for lab, m in [('Common sample (Urban Atlas core, inhabited)', MASK), ('Other inhabited cells with air-quality maps', inhab & ~MASK)]:
    cv.append(dict(group=lab, cells=int(m.sum()), population_2021=float(pop[m].sum()), mean_pop_per_cell=float(pop[m].mean()), mean_canopy=float(np.nanmean(tree[m])),
                   mean_no2_2018=float(Qall['no2'][m, bi].mean()), mean_pm25_2018=float(Qall['pm25'][m, bi].mean()), mean_pm10_2018=float(Qall['pm10'][m, bi].mean())))
pd.DataFrame(cv).to_csv(OUT / 'core_vs_noncore.csv', index=False)
SUMMARY['core_pop_share'] = float(pop[MASK].sum() / pop[inhab].sum()); SUMMARY['core_cell_share'] = float(MASK.sum() / inhab.sum())

# descriptives (common sample)
ds = []
for nm, v in [('Population 2021 (persons per cell)', pop), ('Tree cover density 2018 (share)', tree), ('Urban Atlas green share 2018 (share)', green),
              ('NO2 2018 (ug/m3)', Qall['no2'][:, bi]), ('PM2.5 2018 (ug/m3)', Qall['pm25'][:, bi]), ('PM10 2018 (ug/m3)', Qall['pm10'][:, bi]),
              ('NO2 2010 (ug/m3)', Qall['no2'][:, 0]), ('NO2 2024 (ug/m3)', Qall['no2'][:, YEARS.index(2024)])]:
    vv = v[MASK]; ds.append(dict(variable=nm, mean=vv.mean(), sd=vv.std(ddof=1), min=vv.min(), p25=np.quantile(vv, .25), median=np.median(vv), p75=np.quantile(vv, .75), max=vv.max(), n=len(vv)))
ds.append(dict(variable='Share of cells with Urban Atlas green share = 0', mean=float((green[MASK] == 0).mean()), n=int(MASK.sum())))
pd.DataFrame(ds).to_csv(OUT / 'descriptives.csv', index=False)
cc = []
for ct in CITIES:
    ids = IDS[ct]
    cc.append(dict(city=ct, cells=len(ids), population_2021=float(pop[ids].sum()), mean_canopy=float(tree[ids].mean()), mean_green=float(green[ids].mean()), green_zero_share=float((green[ids] == 0).mean()),
                   mean_no2_2018=float(Qall['no2'][ids, bi].mean()), mean_pm25_2018=float(Qall['pm25'][ids, bi].mean()),
                   corr_canopy_no2=float(np.corrcoef(tree[ids], Qall['no2'][ids, bi])[0, 1]), corr_green_no2=float(np.corrcoef(green[ids], Qall['no2'][ids, bi])[0, 1]),
                   spearman_canopy_green=float(stats.spearmanr(tree[ids], green[ids]).statistic)))
pd.DataFrame(cc).to_csv(OUT / 'city_descriptives.csv', index=False)
wm = tree[allids] - pd.Series(tree[allids]).groupby(city[allids]).transform('mean').to_numpy(); wg = green[allids] - pd.Series(green[allids]).groupby(city[allids]).transform('mean').to_numpy()
SUMMARY['spearman_canopy_green_pooled_within_city'] = float(stats.spearmanr(wm, wg).statistic)
# variance decomposition of the common-sample cell-year panel: city-year means / persistent cell component / within-cell residual
cityv = np.concatenate([[c] * len(IDS[c]) for c in CITIES]); vd = []
for pol in POLS:
    M = Qall[pol][allids]; tot = M.var(); cym = np.zeros_like(M)
    for c in CITIES:
        mk = cityv == c; cym[mk] = M[mk].mean(axis=0)
    Rm = M - cym; cmn = Rm.mean(axis=1, keepdims=True); Wn = Rm - cmn
    vd.append(dict(pollutant=pol, total_variance=tot, share_city_year_means=cym.var() / tot, share_persistent_cell_component=cmn.var() / tot, share_within_cell_residual=Wn.var() / tot))
pd.DataFrame(vd).to_csv(OUT / 'variance_decomposition.csv', index=False)
# pooled within-city correlations (common sample, 2018) and average annual log change
Z = pd.DataFrame({'canopy': tree[allids], 'ua_green': green[allids], 'log_population': np.log(pop[allids]), 'no2': Qall['no2'][allids, bi], 'pm25': Qall['pm25'][allids, bi], 'pm10': Qall['pm10'][allids, bi]})
Z = Z - Z.groupby(city[allids]).transform('mean'); Z.corr().to_csv(OUT / 'pooled_within_city_corr.csv')
trd = []
for pol in POLS:
    L_ = np.log(Qall[pol][allids])
    trd.append(dict(pollutant=pol, mean_annual_log_change_2010_2024=(L_[:, YEARS.index(2024)] - L_[:, 0]).mean() / 14, mean_annual_log_change_2015_2024=(L_[:, YEARS.index(2024)] - L_[:, YEARS.index(2015)]).mean() / 9))
pd.DataFrame(trd).to_csv(OUT / 'average_annual_change.csv', index=False)
# The unused, inadequately calibrated Pesaran CD diagnostic is omitted.
# exceedance of WHO 2021 AQG and EU 2030 limit values, common-sample population (2021 fixed)
ex = []
for pol in POLS:
    for yr in [2010, 2014, 2018, 2022, 2024]:
        q_ = Qall[pol][allids, YEARS.index(yr)]; P_ = pop[allids]
        ex.append(dict(pollutant=pol, year=yr, pop_weighted_mean=float(np.average(q_, weights=P_)), share_pop_above_WHO2021=float(P_[q_ > WHO[pol]].sum() / P_.sum()),
                       share_pop_above_EU2030=float(P_[q_ > EU30[pol]].sum() / P_.sum())))
pd.DataFrame(ex).to_csv(OUT / 'exceedance.csv', index=False)

# ------------------------------------------------------------------ G: robustness summary
log('G: robustness table')
rb = pd.read_csv(ORIG / 'robustness_all.csv'); ok = rb[rb.status == 'ok'].copy()
ok['base_share'] = ok.slots / ok.eligible_cells; ok['kappa'] = (ok.expected_overlap - ok.base_share) / (1 - ok.base_share); ok['replacement'] = 1 - ok.expected_overlap
def eqmean(d, col):
    g_ = d.groupby('city')[col].mean(); return g_.mean(), len(g_)
rob = []
def add(label, d, note=''):
    for pol in POLS:
        dd = d[d.pollutant == pol]
        if len(dd) == 0: continue
        k_, nc = eqmean(dd, 'kappa'); r_, _ = eqmean(dd, 'replacement')
        rob.append(dict(column=label, pollutant=pol, cities=nc, specs=len(dd), kappa=k_, replacement=r_, note=note))
b0 = ok[(ok.high_pollution_quantile == .75) & (ok.budget_fraction == .2)]
add('Baseline 1 km (q=.75, b=.20)', b0[(b0.scale_km == 1)])
add('2 km footprint (mean of 4 offsets)', b0[(b0.scale_km == 2)])
for q_ in [.5, .9]:
    add(f'Eligibility quantile {q_}', ok[(ok.scale_km == 1) & (ok.high_pollution_quantile == q_) & (ok.budget_fraction == .2)])
for b_ in [.1, .3]:
    add(f'Budget share {b_}', ok[(ok.scale_km == 1) & (ok.high_pollution_quantile == .75) & (ok.budget_fraction == b_)])
add('All usable specifications, 1 km', ok[ok.scale_km == 1]); add('All usable specifications, 2 km', ok[ok.scale_km == 2])
# baseline equality check against the primary script
bb = b0[(b0.scale_km == 1)].merge(pe, on=['city', 'pollutant']); assert np.allclose(bb.expected_overlap, bb.overlap, atol=1e-9), 'robustness baseline differs from primary'
mf = pd.read_csv(ORIG / 'matched_footprint.csv'); mf['kappa'] = mf.chance_adjusted_overlap
for res_ in [1, 2]:
    d = mf[mf.resolution_km == res_].groupby(['city', 'pollutant'])[['replacement', 'kappa']].mean().reset_index()
    for pol in POLS:
        dd = d[d.pollutant == pol]; rob.append(dict(column=f'Matched footprint, {res_} km resolution', pollutant=pol, cities=dd.city.nunique(), specs=len(mf[(mf.resolution_km == res_) & (mf.pollutant == pol)]), kappa=dd.kappa.mean(), replacement=dd.replacement.mean()))
# multi-year mean pollution as the screening variable (reduces single-year map noise)
for lab, yrs in [('Pollution = mean 2016-2020', range(2016, 2021)), ('Pollution = mean 2010-2024', MAIN)]:
    for pol in POLS:
        vals = []
        for ct in CITIES:
            ids = IDS[ct]; Qm = Qall[pol][ids][:, [YEARS.index(yv) for yv in yrs]].mean(axis=1); e = est_fast(tree[ids], green[ids], pop[ids], Qm); vals.append((e[1], e[0]))
        rob.append(dict(column=lab, pollutant=pol, cities=len(vals), specs=len(vals), kappa=np.mean([v[0] for v in vals]), replacement=np.mean([v[1] for v in vals])))
# 2025 interim release
for pol in POLS:
    d = cy[(cy.pollutant == pol) & (cy.year == 2025)]; rob.append(dict(column='Pollution year 2025 (interim release)', pollutant=pol, cities=10, specs=10, kappa=d.kappa.mean(), replacement=d.replacement.mean()))
for pol in POLS:
    d = cy[(cy.pollutant == pol) & (cy.year == 2018)]; rob.append(dict(column='Primary (2018, 1 km, q=.75, b=.20)', pollutant=pol, cities=10, specs=10, kappa=d.kappa.mean(), replacement=d.replacement.mean()))
    amb = set(tie_all[(tie_all.pollutant == pol) & (tie_all.ambiguous_slots > 0)].city)
    d9 = d[~d.city.isin(amb)]; rob.append(dict(column='Excluding cities with ambiguous green slots', pollutant=pol, cities=len(d9), specs=len(d9), kappa=d9.kappa.mean(), replacement=d9.replacement.mean(), note=', '.join(sorted(amb))))
    d9 = d[d.city != 'Berlin']; rob.append(dict(column='Excluding Berlin (lowest tie-free kappa)', pollutant=pol, cities=9, specs=9, kappa=d9.kappa.mean(), replacement=d9.replacement.mean()))
pd.DataFrame(rob).to_csv(OUT / 'robustness_summary.csv', index=False)
ok.to_csv(OUT / 'robustness_with_kappa.csv', index=False)
# leave-one-city-out for pooled primary kappa and replacement
loo = []
for pol in POLS:
    d = cy[(cy.pollutant == pol) & (cy.year == 2018)].set_index('city')
    for ct in CITIES:
        r_ = d.drop(ct); loo.append(dict(pollutant=pol, left_out=ct, kappa=r_.kappa.mean(), replacement=r_.replacement.mean()))
pd.DataFrame(loo).to_csv(OUT / 'leave_one_city_out.csv', index=False)

# 10 km bootstrap coverage warning table
s10 = sr[(sr.metric == 'chance_adjusted_overlap') & (sr.pollutant == 'no2')][['city', 'block_km', 'blocks', 'adequate_blocks']]
s10.to_csv(OUT / 'block_counts.csv', index=False)

SUMMARY.update(dict(seed=SEED, bootstrap_draws=B, years=YEARS, runtime_seconds=round(time.time() - t0, 1)))
(OUT / 'summary.json').write_text(json.dumps(SUMMARY, indent=2))
log('done; outputs in', OUT)
