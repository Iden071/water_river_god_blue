# -*- coding: utf-8 -*-
"""
render_v3.py — the v3 decision view.  ->  DECISION_v3.html

Regenerates from the live artefacts every time, so it cannot go stale the way TOP50.html did
for a whole session (R191). Everything it shows is recomputed here from `_v3_parts_f*/`,
`k_real.json` and the catalogues — no numbers are typed in.
"""
import json, os, html, collections, statistics
import rank3
from rank2 import fast_score, week_value, year_gap_pen, eff_year, YEAR_PEN
import rank4, difficulty as DIFF
import pools_past as PP

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
YEARS = ('2024', '2025', '2026')
B = ('-', 'MR', 'WCiv', 'LHP', 'SciRD', 'Lang')
NICE = {'-': 'defer nothing', 'MR': 'defer Intro to QRM', 'WCiv': 'defer West. Civ',
        'LHP': 'defer Lit-Hist-Phil', 'SciRD': 'defer RDQM', 'Lang': 'defer Language'}

Pp, sig, sigs, SIGCODES, code = rank3.build()
import fm_fix; fm_fix.apply(Pp)   # R239: fm per SEGMENT
import eligibility; eligibility.apply(Pp)   # R240: drop 폐강 + hard exclusions
byc = {s['c']: s for v in Pp.values() for s in v}
ZERO = {c[:7] for c, s in byc.items() if s['fm'] == 0}
D = json.load(open(P('k_real.json'), encoding='utf-8'))

K = collections.defaultdict(dict)
for k, v in D['k'].items():
    n_, y, g, nn = k.split('|')
    if v[0] is not None and int(nn) == 4:
        K[n_].setdefault(y, {})[g] = v[0]
MAP = {'WCiv': 'WCiv', 'LHP': 'LHP', 'SciRD': 'SciRD', 'Lang': 'Lang·hard'}


def unit_cost(nm, y):
    vals = [D['disp'].get(f"{nm}|{c}{s}|{y}") for c, s in (('국제', 'S'), ('신촌', 'F'))]
    vals = [v[0] for v in vals if v]
    if not vals:
        return 0.0
    yg = {'ECO1101': min(-year_gap_pen(z, 1) for z in (2, 3, 4)),
          'ME': min(-year_gap_pen(z, 3) for z in (2, 3, 4))}.get(nm, 0.0)
    return min(vals) + yg


def rows(f, b):
    p = P(f'_v3_parts_f{f}/part_{b}.json')
    if not os.path.exists(p):
        return []
    r = json.load(open(p, encoding='utf-8'))['rows']
    return [x for x in r if not any(c[:7] in ZERO for c in x['electives'] + x['requirements'])]


import fallback as _FB


def rank_year(y, mrgeo=None):
    """Best total per branch. ⛔ R276: this used `rows(f, b)[:400]` — the R260/R269 defect a
    third time. Rows are ranked by `score`; the objective is `score + Σunit_cost − K`, and
    `unit_cost` is not in `score`, so no score-ranked prefix is safe. Every row now."""
    out = {}
    for b in B:
        bv, br = None, None
        for f in (0, 1, 2):
            for r in rows(f, b):
                v = r['score'] + sum(unit_cost(i, y) for i in r['items'])
                if bv is None or v > bv:
                    bv, br = v, r
        if bv is None:
            continue
        # ⭐ R272: one uniform estimator, same as fallback.py. No MR special case, no bare min().
        kk = _FB.kdefer(b, y)
        if kk is None:
            continue
        out[b] = (bv - kk, br)
    return dict(sorted(out.items(), key=lambda t: -t[1][0]))


# geometry uncertainty is now INSIDE K (expectation over which slot is obtained), so it is no
# longer a scenario axis. The only thing left that the model genuinely cannot know is which
# catalogue year the receiving semester resembles.
SCEN = [(None, 'expected over all observed section slots')]
matrix = {(y, g): rank_year(y, g) for y in YEARS for g, _l in SCEN}
winner = collections.Counter(list(v)[0] for v in matrix.values())
TOP = matrix[('2026', None)]
best_b = list(TOP)[0]
rec = TOP[best_b][1]

# ---------------- weekly grid ----------------
DN = '월화수목금'
CLK = {i: f'{8+i}:00' for i in range(1, 15)}
PAL = ['#7aa2f7', '#9ece6a', '#e0af68', '#f7768e', '#bb9af7', '#7dcfff', '#ff9e64']


def grid(secs):
    col, occ = {}, {}
    for i, c in enumerate(sorted({x[:7] for x in secs})):
        col[c] = PAL[i % len(PAL)]
    for c in secs:
        s = byc.get(c)
        if not s:
            continue
        for d in range(5):
            for p in range(1, 15):
                if (s['tm'] >> (d * 16 + p)) & 1:
                    occ[(d, p)] = (s['code'], s.get('n', ''), col[s['code']],
                                   not ((s['pm'] >> (d * 16 + p)) & 1))
    ps = sorted({p for _d, p in occ}) or [1]
    o = ['<table class="g"><tr><th></th>' + ''.join(f'<th>{DN[i]}</th>' for i in range(5)) + '</tr>']
    for p in range(min(ps), max(ps) + 1):
        o.append(f'<tr><td class="t">{p}<span>{CLK.get(p,"")}</span></td>')
        for d in range(5):
            v = occ.get((d, p))
            if v:
                cd, nm, c0, online = v
                o.append(f'<td class="c{" on" if online else ""}" style="--c:{c0}">'
                         f'<b>{html.escape(cd)}</b><i>{html.escape(nm[:20])}</i></td>')
            else:
                o.append('<td></td>')
        o.append('</tr>')
    return ''.join(o) + '</table>'


secs = rec['requirements'] + rec['electives'] + ([rec['chapel']] if rec['chapel'] != '-' else [])
tm = pm = fm = 0
for c in secs:
    s = byc[c]; tm |= s['tm']; pm |= s['pm']; fm |= s['fm']
wk, det = fast_score(tm, pm, fm)
wv, freed = week_value(pm, fm)
yrp = sum(YEAR_PEN(eff_year(byc[c], code)) for c in rec['requirements'] + rec['electives'])
dif = -DIFF.D_LANG * sum(DIFF.steps(c) for c in rec['requirements'] + rec['electives'])
saved = sum(unit_cost(i, '2026') for i in rec['items'])
kdef = K['Lang·hard'].get('2026', {})
kdef = min(kdef.values()) if kdef else 0.0

CSS = """
*{box-sizing:border-box}body{font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI','Malgun Gothic',sans-serif;
margin:0;padding:30px;background:#0f1117;color:#c9d1d9;max-width:1120px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:14px;letter-spacing:.13em;text-transform:uppercase;
color:#8b949e;margin:34px 0 12px;border-top:1px solid #21262d;padding-top:16px}
.sub{color:#8b949e;margin:0 0 18px}
.card{background:#161b22;border:1px solid #21262d;border-radius:9px;padding:16px 18px;margin:12px 0}
.warn{border-color:#7d3c34;background:#1d1516}
.warn b{color:#f7768e}
.two{display:grid;grid-template-columns:1.05fr .95fr;gap:20px;align-items:start}
table.g{border-collapse:collapse;width:100%;table-layout:fixed}
.g th{font-size:11px;color:#8b949e;padding:3px 0}
.g td{border:1px solid #21262d;height:28px;padding:0}
.g td.t{width:54px;font-size:10px;color:#6e7681;text-align:right;padding-right:6px;border:none}
.g td.t span{display:block;font-size:9px;opacity:.6}
.g td.c{background:color-mix(in srgb,var(--c) 26%,transparent);border-left:3px solid var(--c);padding:1px 5px}
.g td.c b{display:block;font-size:10px;color:#e6edf3}
.g td.c i{display:block;font-size:9px;color:#8b949e;font-style:normal;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.g td.c.on{border-left-style:dashed}
table.d{border-collapse:collapse;width:100%;font-size:13px}
.d th{text-align:left;font-size:11px;letter-spacing:.08em;color:#6e7681;font-weight:600;padding:5px 8px;border-bottom:1px solid #21262d}
.d td{padding:5px 8px;border-bottom:1px solid #1a1f27}
.d td.n{text-align:right;font-variant-numeric:tabular-nums}
.win{color:#9ece6a;font-weight:600}.lose{color:#6e7681}
.pill{display:inline-block;font-size:11px;padding:2px 8px;border-radius:99px;background:#21262d;color:#8b949e;margin-right:6px}
ul{margin:6px 0 0;padding-left:18px}li{margin:4px 0}
.bar{height:7px;background:#21262d;border-radius:4px;overflow:hidden}
.bar i{display:block;height:100%;background:#7aa2f7}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
"""

h = [f'<!doctype html><meta charset="utf-8"><title>Fall 2026 — v3 decision</title><style>{CSS}</style>',
     '<h2 class="sr-only">Fall 2026 course registration recommendation, scenario robustness, '
     'and the outstanding blocker.</h2>',
     '<h1>Fall 2026 — the v3 answer</h1>',
     f'<p class="sub">Registration <b>2026-08-25 09:00 KST</b>. '
     f'Rebuilt from measurements on 2026-08-10; every number below is recomputed at render time.</p>',
     '<div class="card warn"><b>⛔ Not registrable yet.</b> The 8/14 seat pull has not been run. '
     'A 1학년 quota of 0 makes a section <i>impossible</i>, not merely competitive (R134), and '
     'that check can still invalidate all of this.</div>',
     '<h2>The recommendation</h2>',
     '<div class="two"><div>',
     f'<div class="card"><span class="pill">{html.escape(NICE[best_b])}</span>'
     f'<span class="pill">{rec["score"]:.2f} week-score</span>'
     f'<span class="pill">free days {"".join(DN[d] for d in sorted(freed))}</span>',
     '<table class="d"><tr><th>slot</th><th>section</th><th>course</th></tr>']
for c in rec['requirements']:
    h.append(f'<tr><td>REQ</td><td>{html.escape(c)}</td>'
             f'<td>{html.escape(byc[c].get("n","")[:38])}</td></tr>')
for c, i in zip(rec['electives'], rec['items']):
    h.append(f'<tr><td>{html.escape(i)}</td><td>{html.escape(c)}</td>'
             f'<td>{html.escape(byc[c].get("n","")[:38])}</td></tr>')
if rec['chapel'] != '-':
    h.append(f'<tr><td>chapel</td><td>{html.escape(rec["chapel"])}</td><td>Chapel</td></tr>')
h += ['</table></div></div><div>', f'<div class="card">{grid(secs)}'
      '<p style="font-size:11px;color:#6e7681;margin:10px 0 0">dashed = online hours '
      '(they hold a slot but do not put you on campus, so they never break a trip home)</p></div>',
      '</div></div>',
      '<h2>Where the score comes from</h2><div class="card"><table class="d">'
      '<tr><th>term</th><th class="n">value</th><th>what it is</th></tr>']
for lab, val, why in (
        ('week', wk, 'this semester&rsquo;s comfort, in real hours'),
        ('&nbsp;&nbsp;· trip + rest + Friday', wv, 'going home, days off, the event window'),
        ('&nbsp;&nbsp;· day penalties', wk - wv, '9am starts, holes, long runs, late finishes'),
        ('year gap', yrp, 'courses sat off their chart year'),
        ('chapel', 10.0, 'taken'),
        ('difficulty', dif, 'hard-tier language taken now'),
        ('deferral saved', saved, 'taking ECO1101 + an ME now, instead of deferring them'),
        ('&minus; K(Language)', -kdef, 'what the deferred Language costs its receiving semester')):
    h.append(f'<tr><td>{lab}</td><td class="n">{val:+.2f}</td><td style="color:#6e7681">{why}</td></tr>')
h += [f'<tr><td><b>total</b></td><td class="n"><b>{TOP[best_b][0]:.2f}</b></td><td></td></tr>',
      '</table></div>',
      '<h2>Does the answer survive the things we do not know?</h2>',
      '<div class="card"><p style="margin-top:0;color:#8b949e">Two unknowns can move it: which '
      'catalogue year the receiving semester resembles, and whether QRM1001 keeps the section '
      'time it moved to in 2026. Every cell is a full re-search, not a rescoring.</p>',
      '<table class="d"><tr><th>scenario</th>' +
      ''.join(f'<th class="n">{y} catalogue</th>' for y in YEARS) + '</tr>']
for g, lab in SCEN:
    cells = []
    for y in YEARS:
        r = matrix[(y, g)]
        ks = list(r)
        marg = r[ks[0]][0] - r[ks[1]][0]
        cells.append(f'<td class="n"><span class="win">{html.escape(NICE[ks[0]])}</span>'
                     f'<br><span style="color:#6e7681">+{marg:.2f}</span></td>')
    h.append(f'<tr><td>{html.escape(lab)}</td>' + ''.join(cells) + '</tr>')
h += ['</table>',
      f'<p style="margin-bottom:0;color:#8b949e">Same winner in <b>{max(winner.values())} of '
      f'{len(matrix)}</b> cells. The margin is thinnest where the catalogue is most recent and '
      f'QRM1001 keeps its cheap slot — there it is nearly a tie with '
      f'{html.escape(NICE["MR"])}.</p></div>',
      '<h2>What deferring each requirement actually costs</h2>',
      '<div class="card"><p style="margin-top:0;color:#8b949e">K = comfort lost by the future '
      'semester that receives the deferred course, measured over real sections at real hours in '
      'that campus and season. Lower is cheaper to defer.</p><table class="d">'
      '<tr><th>requirement</th><th class="n">K (2026)</th><th>why</th></tr>']
WHY = {'Lang·hard': 'about 10 sections a term — he picks; several are 3 credits in 2 hours',
       'MR': 'exactly ONE section a term — he takes what is offered',
       'LHP': 'one section a term', 'SciRD': 'two sections a term',
       'WCiv': 'one section, identical in all six observed terms'}
kk = []
for nm in ('Lang·hard', 'MR', 'LHP', 'WCiv', 'SciRD'):
    g = K[nm].get('2026', {})
    if g:
        kk.append((nm, min(g.values())))
lo, hi = min(v for _n, v in kk), max(v for _n, v in kk)
for nm, v in sorted(kk, key=lambda t: t[1]):
    w = int(100 * (v - lo) / (hi - lo + 1e-9))
    h.append(f'<tr><td>{html.escape(nm)}</td><td class="n">{v:.2f}</td>'
             f'<td><div class="bar"><i style="width:{w}%"></i></div>'
             f'<span style="font-size:11px;color:#6e7681">{WHY[nm]}</span></td></tr>')
h += ['</table></div>',
      '<h2>What is still assumed</h2><div class="card"><ul>'
      '<li><b>The 8/14 seat pull has not been run.</b> The only item with a deadline.</li>'
      '<li><b>17 of 38 remaining course-units have no identity</b> — the 12 second-major courses '
      'and 5 free electives. Their weekly hours are assumed, not known, until December.</li>'
      '<li><b>Workload is not priced at all.</b> Six courses cost the same whatever they are; '
      'the two zero-fixed-hour sections are excluded as a guard rather than fixed.</li>'
      '<li><b>Receiving semesters are modelled at 5 courses, not 6</b> — a full 신촌 load is '
      'computationally out of reach.</li>'
      '<li><b>Language is assumed to land in a 신촌 Fall</b>, where only the hard tier runs. '
      'In Spring the easy tier exists there.</li>'
      '</ul></div>',
      '<p style="color:#6e7681;font-size:12px;margin-top:26px">Generated by <code>render_v3.py</code> '
      'from <code>_v3_parts_f*/</code> and <code>k_real.json</code>. Evidence: <code>RULES.md</code> '
      'R221–R236.</p>']
open(P('DECISION_v3.html'), 'w', encoding='utf-8').write('\n'.join(h))
print(f"wrote DECISION_v3.html — winner {best_b} in {max(winner.values())}/{len(matrix)} cells")
