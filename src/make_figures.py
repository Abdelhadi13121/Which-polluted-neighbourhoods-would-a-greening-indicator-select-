"""Figures for the empirical section. Reads outputs/panel_extension/*.csv, writes outputs/figures/*.png (300 dpi).
Design: one y-scale per panel, thin marks, direct labels, recessive grid, identity carried by marker and line style
as well as colour (greyscale-safe). Colours: first three slots of a validated categorical palette."""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parents[1]
O = HERE / 'outputs' / 'panel_extension'; F = HERE / 'outputs' / 'figures'; F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
COL = {'no2': '#2a78d6', 'pm25': '#eb6834', 'pm10': '#1baf7a'}
MK = {'no2': 'o', 'pm25': 's', 'pm10': '^'}; LS = {'no2': '-', 'pm25': '--', 'pm10': ':'}
LAB = {'no2': 'NO$_2$', 'pm25': 'PM$_{2.5}$', 'pm10': 'PM$_{10}$'}
plt.rcParams.update({'font.family': ['Arial', 'DejaVu Sans'], 'font.size': 8.5, 'axes.edgecolor': INK2, 'axes.labelcolor': INK, 'text.color': INK,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.linewidth': .7, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .6, 'savefig.dpi': 300, 'pdf.fonttype': 42, 'figure.dpi': 120})
def panel(ax, s): ax.text(-0.02, 1.04, s, transform=ax.transAxes, fontsize=10, fontweight='bold', ha='right')
def leg(ax, loc, pols=('no2', 'pm25', 'pm10')):
    """Legend with colour + marker + line style, so identity never rests on colour alone."""
    h = [Line2D([0], [0], color=COL[p], ls=LS[p], marker=MK[p], ms=4.5, lw=1.2, label=LAB[p].replace('$', '$')) for p in pols]
    ax.legend(handles=h, loc=loc, frameon=False, fontsize=7.5, handlelength=2.6, labelcolor=INK, borderaxespad=.3)
def end_labels(ax, x, items, gap):
    """Place direct labels at x for (y, text) items, pushing them apart by at least `gap` (data units)."""
    items = sorted(items); ys = [y for y, _ in items]
    for i in range(1, len(ys)): ys[i] = max(ys[i], ys[i - 1] + gap)
    shift = (np.mean([y for y, _ in items]) - np.mean(ys)); ys = [y + shift for y in ys]
    for y_, (_, t) in zip(ys, items): ax.text(x, y_, t, fontsize=8, va='center', color=INK)

cy = pd.read_csv(O / 'city_year_estimates.csv'); py = pd.read_csv(O / 'pooled_year_estimates.csv')
CITIES = list(dict.fromkeys(cy.city))

# ---------------------------------------------------------------- Figure 1: city-level kappa and replacement (NO2, 2018)
d = cy[(cy.pollutant == 'no2') & (cy.year == 2018)].set_index('city').sort_values('kappa', ascending=False)
pk = py[(py.pollutant == 'no2') & (py.year == 2018) & (py.metric == 'kappa')].iloc[0]; pr = py[(py.pollutant == 'no2') & (py.year == 2018) & (py.metric == 'replacement')].iloc[0]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
for ax, m, pool_row, lo, hi, bench, bl, xl in [(axs[0], 'kappa', pk, -.25, .95, .5, 'κ = 0.5', 'Chance-adjusted overlap κ'), (axs[1], 'replacement', pr, .1, 1.0, .5, '0.5', 'Replacement rate (1 − overlap)')]:
    ys = np.arange(len(d))[::-1] + 1.5
    for y_, (c, r) in zip(ys, d.iterrows()):
        ax.plot([r[m + '_lo'], r[m + '_hi']], [y_, y_], color=INK2, lw=1.1, solid_capstyle='butt')
        ax.plot(r[m], y_, 'o', ms=5.5, mfc=('white' if c == 'Lisbon' else COL['no2']), mec=COL['no2'], mew=1.2, zorder=3)
    ax.plot([pool_row.t_lo, pool_row.t_hi], [0.4, 0.4], color=INK, lw=2.2, solid_capstyle='butt'); ax.plot(pool_row['mean'], 0.4, 'D', ms=7, color=INK, zorder=4)
    ax.axvline(bench, color=INK2, lw=.8, ls=(0, (4, 3))); ax.text(bench, len(d) + 2.1, bl, ha='center', va='bottom', fontsize=7.5, color=INK2)
    if m == 'kappa': ax.axvline(0, color=INK2, lw=.6, ls=':'); ax.text(0, len(d) + 2.1, 'chance level (κ = 0)', ha='center', va='bottom', fontsize=7.5, color=INK2)
    else: ax.axvline(.8, color=INK2, lw=.6, ls=':'); ax.text(.8, len(d) + 2.1, 'chance level (1 − b)', ha='center', va='bottom', fontsize=7.5, color=INK2)
    ax.set_xlim(lo, hi); ax.set_ylim(-.3, len(d) + 1.9); ax.set_xlabel(xl); ax.grid(axis='y', visible=False)
axs[0].set_yticks(list(np.arange(len(d))[::-1] + 1.5) + [0.4]); axs[0].set_yticklabels([c + ('†' if c == 'Lisbon' else '') for c in d.index] + ['Mean of cities'], color=INK)
for ax, s in zip(axs, 'ab'): panel(ax, s)
fig.text(.01, .005, '95% intervals: 5 km spatial-block bootstrap (cities); t-interval across the 10 cities (mean). † Lisbon: all green-indicator slots are tie-allocated.', fontsize=6.8, color=INK2)
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(F / 'fig1_city_kappa.png'); fig.savefig(F / 'fig1_city_kappa.pdf'); plt.close(fig)

# ---------------------------------------------------------------- Figure 2: stability of indicator disagreement and map-series diagnostic
cr = pd.read_csv(O / 'consecutive_rank_corr.csv')
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.2))
ax = axs[0]; lab_items = []
for pol in ['no2', 'pm25', 'pm10']:
    s = py[(py.pollutant == pol) & (py.metric == 'kappa')].sort_values('year')
    ax.fill_between(s.year[s.year <= 2024], s.boot_lo[s.year <= 2024], s.boot_hi[s.year <= 2024], color=COL[pol], alpha=.13, lw=0)
    ax.plot(s.year[s.year <= 2024], s['mean'][s.year <= 2024], color=COL[pol], ls=LS[pol], marker=MK[pol], ms=4.2, lw=1.2)
    ax.plot(s.year[s.year == 2025], s['mean'][s.year == 2025], color=COL[pol], marker=MK[pol], ms=4.5, mfc='white', ls='none')
    lab_items.append((s['mean'].iloc[-1], LAB[pol]))
ax.legend(handles=[Line2D([0], [0], color=COL[p], ls=LS[p], marker=MK[p], ms=4.5, lw=1.2, label=LAB[p]) for p in ('no2', 'pm25', 'pm10')], loc='upper right', ncol=3, frameon=False, fontsize=7.5, handlelength=2.4, columnspacing=1.1)
ax.axvline(2014.5, color=INK2, lw=.8, ls=(0, (4, 3))); ax.text(2014.35, .015, 'PM series discontinuity', fontsize=7, color=INK2, va='bottom', ha='right')
ax.axhline(0, color=INK2, lw=.6); ax.set_xlim(2009.5, 2026.8); ax.set_ylim(-.02, .52); ax.set_ylabel('Mean κ across cities'); ax.set_xlabel('Pollution year used for screening'); ax.set_xticks([2010, 2014, 2018, 2022, 2025])
panel(ax, 'a')
ax = axs[1]
for pol in ['no2', 'pm25', 'pm10']:
    s = cr[cr.pollutant == pol]
    ax.plot(s.year_to, s.mean_rho, color=COL[pol], ls=LS[pol], marker=MK[pol], ms=4.2, lw=1.2)
    ax.text(2025.35, s.mean_rho.iloc[-1] + (.015 if pol == 'no2' else (-.012 if pol == 'pm25' else .012)), LAB[pol], fontsize=8, va='center')
leg(ax, 'lower right'); ax.axvline(2014.5, color=INK2, lw=.8, ls=(0, (4, 3))); ax.set_xlim(2010.5, 2026.8); ax.set_ylim(.55, 1.01); ax.set_ylabel('Within-city Spearman ρ, year t−1 vs t'); ax.set_xlabel('Year t'); ax.set_xticks([2011, 2015, 2019, 2023, 2025])
panel(ax, 'b')
fig.text(.01, .005, 'Bands in (a): 95% fixed-city spatial-block bootstrap (5 km, B = 1,000). Hollow markers: 2025 interim release.', fontsize=6.8, color=INK2)
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(F / 'fig2_stability.png'); fig.savefig(F / 'fig2_stability.pdf'); plt.close(fig)

# ---------------------------------------------------------------- Figure 3: canopy-gradient dynamics relative to 2018
gp = pd.read_csv(O / 'gradient_panel.csv'); gp = gp[(gp.spec == 'baseline') & (gp.block_km == 10) & (gp.term == 'canopy')]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=True)
ax = axs[0]; s = gp[gp.pollutant == 'no2'].sort_values('year'); m = s.year <= 2024
ax.fill_between(s.year[m], 100 * (np.exp(s.supt_lo[m]) - 1), 100 * (np.exp(s.supt_hi[m]) - 1), color=COL['no2'], alpha=.13, lw=0)
ax.vlines(s.year, 100 * (np.exp(s.lo) - 1), 100 * (np.exp(s.hi) - 1), color=COL['no2'], lw=1.1)
ax.plot(s.year[m], s.pct[m], color=COL['no2'], marker='o', ms=4.2, lw=1.2); ax.plot(s.year[~m], s.pct[~m], color=COL['no2'], marker='o', ms=4.5, mfc='white', ls='none')
ax.plot([2018], [0], marker='o', ms=4.5, mfc='white', mec=INK2, ls='none'); ax.axhline(0, color=INK2, lw=.7)
ax.set_title('NO$_2$', fontsize=8.5, loc='left', color=INK); ax.set_xlabel('Year'); ax.set_ylabel('100θ: change in log-pollution gradient\non canopy since 2018 (100 × log points per 10 pp)', fontsize=7.8)
ax.set_xticks([2010, 2014, 2018, 2022, 2025]); panel(ax, 'a')
ax = axs[1]; lab_items = []
for pol in ['pm25', 'pm10']:
    s = gp[gp.pollutant == pol].sort_values('year'); m = s.year <= 2024
    ax.fill_between(s.year[m], 100 * (np.exp(s.lo[m]) - 1), 100 * (np.exp(s.hi[m]) - 1), color=COL[pol], alpha=.13, lw=0)
    ax.plot(s.year[m], s.pct[m], color=COL[pol], ls=LS[pol], marker=MK[pol], ms=4.2, lw=1.2); ax.plot(s.year[~m], s.pct[~m], color=COL[pol], marker=MK[pol], ms=4.5, mfc='white', ls='none')
    lab_items.append((s.pct.iloc[-1], LAB[pol]))
leg(ax, 'upper right', ('pm25', 'pm10'))
ax.axvline(2014.5, color=INK2, lw=.8, ls=(0, (4, 3))); ax.axhline(0, color=INK2, lw=.7); ax.plot([2018], [0], marker='o', ms=4.5, mfc='white', mec=INK2, ls='none')
ax.set_title('Particulate matter (map-series discontinuity at 2014/15)', fontsize=8.5, loc='left', color=INK); ax.set_xlabel('Year'); ax.set_xlim(2009.5, 2026.8); ax.set_xticks([2010, 2014, 2018, 2022, 2025]); panel(ax, 'b')
axs[0].set_xlim(2009.5, 2025.8)
fig.text(.01, .005, 'Cell and city×year fixed effects; green share and log population interacted with year. Bars/bands: pointwise 95% CI (10 km block clusters, 215).\nShaded band in (a): simultaneous sup-t 95% band, 2010–2024. Hollow markers: 2018 base (zero by construction) and 2025 interim release.', fontsize=6.6, color=INK2, linespacing=1.3)
fig.tight_layout(rect=(0, .07, 1, 1)); fig.savefig(F / 'fig3_gradient.png'); fig.savefig(F / 'fig3_gradient.pdf'); plt.close(fig)

# ---------------------------------------------------------------- Figure 4: specification curve (all usable specifications)
rb = pd.read_csv(O / 'robustness_with_kappa.csv')
g = rb.groupby(['scale_km', 'offset_x_km', 'offset_y_km', 'pollutant', 'high_pollution_quantile', 'budget_fraction']).agg(kappa=('kappa', 'mean'), replacement=('replacement', 'mean'), cities=('city', 'nunique')).reset_index()
g = g[g.cities >= 6]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1))
for ax, m, yl, s_ in [(axs[0], 'kappa', 'Mean κ across usable cities', 'a'), (axs[1], 'replacement', 'Mean replacement rate', 'b')]:
    lab_items = []
    for pol in ['no2', 'pm25', 'pm10']:
        v = np.sort(g[g.pollutant == pol][m].to_numpy()); ax.plot(np.arange(len(v)) / (len(v) - 1), v, color=COL[pol], ls=LS[pol], lw=1.3, marker=MK[pol], ms=2.6, markevery=max(1, len(v) // 14))
        lab_items.append((v[-1], LAB[pol]))
    leg(ax, 'lower right' if m == 'kappa' else 'upper left')
    if m == 'kappa': ax.axhline(.5, color=INK2, lw=.7, ls=(0, (4, 3))); ax.text(.02, .515, 'κ = 0.5', fontsize=7, color=INK2); ax.set_ylim(0, .62)
    else: ax.axhline(.5, color=INK2, lw=.7, ls=(0, (4, 3))); ax.set_ylim(.3, .9)
    ax.set_xlim(-.02, 1.16); ax.set_xticks([0, .5, 1]); ax.set_xticklabels(['min', 'median', 'max']); ax.set_xlabel('Specifications, sorted by estimate within each pollutant'); ax.set_ylabel(yl); panel(ax, s_)
fig.text(.01, .005, 'Specifications: 1 and 2 km footprints (4 offsets), eligibility quantile {0.5, 0.75, 0.9}, budget share {0.1, 0.2, 0.3}; specifications with ≥ 6 usable cities.', fontsize=6.8, color=INK2)
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(F / 'fig4_spec_curve.png'); fig.savefig(F / 'fig4_spec_curve.pdf'); plt.close(fig)
print('figures written to', F, '| specs plotted per pollutant:', g.groupby('pollutant').size().to_dict())




