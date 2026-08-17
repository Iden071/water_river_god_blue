# -*- coding: utf-8 -*-
"""
render_v3_top50.py — the v3 ranking as a browsable top-50.  ->  TOP50_v3.html

Same shape as the old TOP50.html, but ranked by the v3 objective and with the scenario
switchable in the page, because collapsing the catalogue-year and QRM1001-slot variation into
one ranking is exactly what we agreed not to do.

    score = week + year-pen + chapel + difficulty
          + Σ deferral cost SAVED by each elective unit taken now
          − K(deferred requirement | catalogue year, its section geometry)

The first three lines are fixed per timetable; the last two move with the scenario, so the
page recomputes and re-sorts client-side when you change it. Cards are the union of the top 50
under every scenario, so switching never reveals a card that was not measured.
"""
import sys, json, os, html, collections
import rank3
from rank2 import fast_score, week_value, year_gap_pen, eff_year, YEAR_PEN
import difficulty as DIFF

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
YEARS = ('2026',)
GEOS = ('partition over sems 3-8',)
B = ('-', 'MR', 'WCiv', 'LHP', 'SciRD', 'Lang')
LABEL = {'-': 'postpones nothing', 'MR': 'postpones QRM입문', 'WCiv': 'postpones West.Civ',
         'LHP': 'postpones Lit·Hist·Phil', 'SciRD': 'postpones RDQM', 'Lang': 'postpones language'}
KEY = {'WCiv': 'WCiv', 'LHP': 'LHP', 'SciRD': 'SciRD', 'Lang': 'Lang·hard'}
DN = '월화수목금'
PAL = ['#6f8fd0', '#7fa25e', '#c69a4e', '#c96f7e', '#9a7fc0', '#5f9fb5', '#c08050']

Pp, sig, sigs, SIGCODES, code = rank3.build()
import fm_fix; fm_fix.apply(Pp)   # R239: fm per SEGMENT
import eligibility; eligibility.apply(Pp)   # R240: drop 폐강 + hard exclusions
byc = {s['c']: s for v in Pp.values() for s in v}
ZERO = {c[:7] for c, s in byc.items() if s['fm'] == 0}
D = json.load(open(P('k_real.json'), encoding='utf-8'))

KD = collections.defaultdict(lambda: collections.defaultdict(dict))
for k, v in D['k'].items():
    n_, y, g, nn = k.split('|')
    if v[0] is not None and int(nn) == 4:
        KD[n_][y][g] = v[0]


def unit_cost(nm, y):
    vals = [D['disp'].get(f"{nm}|{c}{s}|{y}") for c, s in (('국제', 'S'), ('신촌', 'F'))]
    vals = [v[0] for v in vals if v]
    if not vals:
        return 0.0
    yg = {'ECO1101': min(-year_gap_pen(z, 1) for z in (2, 3, 4)),
          'ME': min(-year_gap_pen(z, 3) for z in (2, 3, 4))}.get(nm, 0.0)
    return round(min(vals) + yg, 3)


# ⭐ R294 — SCORED BY THE PARTITION, NOT BY K.
# The old scoring was `score + Σunit_cost − K(deferred)`. K priced deferral as if the penalty
# vanished; R285 showed that for a required course it is only RELOCATED. This now scores every
# candidate the way partition_verdict does:
#
#     total(card) = Fall week score  +  best Σ best_week over semesters 3–8 of ITS remainder
#
# There is no K and no unit_cost term — a Fall elective that discharges a ledger unit is
# already priced by that unit being absent from the remainder.
#
# The DP is cached on the remainder, and distinct remainders are few (one per branch x the
# ledger items the electives burn), so this is cheap despite running over every candidate.
import partition_solve as _PS
import partition_verdict as _PV
_PD, _PVAL = _PS.table()
_PS.SINCHON_BONUS = float(os.environ.get('SINCHON_BONUS', 30.0))
# disk-cached: `solve()` rebuilds its subset table on every call, so a cold render was doing
# that once per distinct remainder over 62k candidates and never finished. Distinct remainders
# are few; solve each once, persist, and every later render is instant.
_FUTP = P('_future_cache.json')
_FUT = {}
if os.path.exists(_FUTP) and os.path.getsize(_FUTP):
    try:
        _FUT = dict(json.load(open(_FUTP, encoding='utf-8')))   # keys are opaque strings now
    except Exception:
        _FUT = {}


def future_value(branch, r):
    rem = _PV.remainder(branch, r)
    key = _PS.cache_key(rem, _PD)          # RED-TEAM F2: bonus + table are IN the key
    if key not in _FUT:
        _FUT[key] = _PS.solve(rem, _PVAL, _PD['base'])[0]
        json.dump(_FUT, open(_FUTP, 'w', encoding='utf-8'), ensure_ascii=False)
    return _FUT[key]


# ---------------- collect candidates ----------------
seen, cands = set(), []
# ⛔ R263. This renderer UNIONS three separate searches (MAX_FREE 0/1/2). If they were run
# under different scoring constants, the union silently mixes incomparable candidates and
# ranks them against each other. That is inert only while every extra term is zero — the
# moment prof_ratings.csv has a single row, an f2 scored WITH professors would be ranked
# against f0/f1 scored WITHOUT them, and the professor bonus would look like a free win.
_seen_consts = {}
for f in (0, 1, 2):
    for b in B:
        p = P(f'_v3_parts_f{f}/part_{b}.json')
        if not os.path.exists(p):
            continue
        _blob = json.load(open(p, encoding='utf-8'))
        _c = dict(_blob.get('consts') or {})
        _c.pop('MAX_FREE', None)          # the one constant these runs are SUPPOSED to differ in
        _seen_consts[f'f{f}/{b}'] = _c
        for r in _blob['rows']:
            allc = r['requirements'] + r['electives']
            if any(c[:7] in ZERO for c in allc):
                continue          # R218 guard: zero-fixed-hour sections excluded
            cells = tuple(sorted({(d, pp) for c in allc + ([r['chapel']] if r['chapel'] != '-' else [])
                                  for d in range(5) for pp in range(1, 15)
                                  if (byc[c]['tm'] >> (d * 16 + pp)) & 1}))
            # ⛔ R278. This keyed on COURSE CODES, so two timetables with the identical week
            # shape AND identical score but interchangeable courses became separate cards —
            # and each then listed the other as an "equal swap". Measured: 88 cards collapsed
            # to 55 groups; one score/shape had FIVE cards, another three differing only by
            # UIC1805 Beginning Chinese vs UIC1806 Beginning Japanese. That is precisely what
            # the equal-swap list exists to express INSIDE one card.
            # Key on the scenario-invariant identity instead: same branch, same occupied
            # cells, same pre-K score, same ledger items => identical under every scenario.
            k = (b, cells, round(r['score'], 3), tuple(sorted(r['items'])))
            if k in seen:
                continue
            seen.add(k)
            r['defer'] = b
            cands.append(r)


_distinct = {json.dumps(c, sort_keys=True, ensure_ascii=False) for c in _seen_consts.values()}
if len(_distinct) > 1:
    print("⛔ REFUSING TO RENDER — the part files were scored under DIFFERENT constants.")
    print("   Ranking them against each other is meaningless (R263). Seen:")
    for _k, _v in sorted(_seen_consts.items()):
        print(f"     {_k:12s} {_v}")
    print("\n   Re-run every MAX_FREE with the same constants:")
    print("     for mf in 0 1 2 99; do MAX_FREE=$mf D_LANG=10.0 python research_v3.py; done")
    sys.exit(1)
if _distinct:
    print(f"  consts check: all part files agree — {sorted(_distinct)[0]}")


def sc(r, y, g):
    f = future_value(r['defer'], r)
    return None if f < -1e17 else r['score'] + f


# pre-warm the DP cache over the distinct remainders, so ranking is a lookup
_rems = {}
for _c in cands:
    _rems.setdefault(tuple(sorted(_PV.remainder(_c['defer'], _c).items())), _c)
print(f"  {len(_rems)} distinct remainders to solve")
for _i, _c in enumerate(_rems.values(), 1):
    future_value(_c['defer'], _c)
    if _i % 10 == 0:
        print(f"    solved {_i}/{len(_rems)}", flush=True)

keep = set()
for y in YEARS:
    for g in GEOS:
        ranked = sorted((c for c in cands if sc(c, y, g) is not None),
                        key=lambda c: -sc(c, y, g))[:50]
        keep.update(id(c) for c in ranked)
cards = [c for c in cands if id(c) in keep]
cards.sort(key=lambda c: -(sc(c, '2026', GEOS[0]) or -1e9))
print(f"{len(cands)} structurally distinct candidates -> {len(cards)} cards "
      f"(union of the top 50 across {len(YEARS)*len(GEOS)} scenarios)")

# ---------------- render ----------------
# ---------------------------------------------------------------------------
# EQUAL REPLACEMENTS — verified by RECOMPUTING the score, not by matching a signature
# ---------------------------------------------------------------------------
# Two kinds, and they are not the same thing:
#   (a) same course code, different 분반, IDENTICAL CELLS -> a professor choice and a true
#       drop-in fallback. ⛔ R282/R284: the cell check was in this comment but NOT in the code —
#       equality was tested by rescoring alone, so mirror-image weeks (UIC1551-04 화8,9/목7 vs
#       UIC1551-01 화7/목8,9) were offered as interchangeable. They score the same; they are
#       not the same week. R284 is the rule: SAME CELLS or it is not a swap at all.
#   (b) a DIFFERENT course whose substitution leaves the total score unchanged. Under v3 the
#       score depends on tm/pm/fm, the year penalty, credits, the difficulty tier AND the
#       ledger item (because items now carry a deferral saving), so all of those must match.
# R197's discipline: never assert an equal swap from a signature. Swap it in, rescore, compare.
POOL_OF = {}
for _nm, _pool in (('MR', Pp['MR']), ('WCiv', Pp['WCiv']), ('LHP', Pp['LHP']),
                   ('SciRD', Pp['SciRD']), ('OPEN', Pp['OPEN']), ('Chapel', Pp['Chapel'])):
    for _s in _pool:
        POOL_OF.setdefault(_s['c'], _nm)
LANGSET = {c for c in byc if byc[c]['code'] in DIFF.LANG_ALL}

# ⛔ `refetch_listings` v4 keeps ONE RECORD PER (section, query) on purpose, so that 과목종별
# is not collapsed across the majors that list it (that was its v3 bug). A section listed by
# two majors therefore appears TWICE in the pool. The ranking is unaffected — electives are
# collapsed by signature before enumeration — but anything that ITERATES a pool double-counts.
# Measured 2026-08-10: exactly 4 redundant rows, all four language sections
# (UIC1805-01/02, UIC1806-01/02), which is why #17 listed "UIC1806" twice.
POOL_UNIQ = {}
for _nm, _pool in Pp.items():
    _seen, _u = set(), []
    for _s in _pool:
        if _s['c'] in _seen:
            continue
        _seen.add(_s['c']); _u.append(_s)
    POOL_UNIQ[_nm] = _u
_dups = sum(len(v) - len(POOL_UNIQ[k]) for k, v in Pp.items())
if _dups:
    print(f"  ⚠ {_dups} duplicate section rows removed before the equal-swap scan")


def _score_of(secs, items):
    """The fixed part of the v3 score for a set of sections (everything not scenario-dependent)."""
    tm = pm = fm = 0
    for c in secs:
        s = byc[c]
        if tm & s['tm']:
            return None
        tm |= s['tm']; pm |= s['pm']; fm |= s['fm']
    acad = [c for c in secs if POOL_OF.get(c) != 'Chapel']
    wk = fast_score(tm, pm, fm)[0]
    yr = sum(YEAR_PEN(eff_year(byc[c], code)) for c in acad)
    dif = -DIFF.D_LANG * sum(DIFF.steps(c) for c in acad)
    ch = 10.0 if any(POOL_OF.get(c) == 'Chapel' for c in secs) else -4.2
    return round(wk + yr + dif + ch, 6)


def equal_swaps(r):
    """{section: (same_bunban, other_courses)} — both verified by rescoring."""
    allc = r['requirements'] + r['electives'] + ([r['chapel']] if r['chapel'] != '-' else [])
    items = dict(zip(r['electives'], r['items']))
    base = _score_of(allc, items)
    out = {}
    for c in allc:
        pool_nm = POOL_OF.get(c)
        if pool_nm is None:
            continue
        # the language slot lives in OPEN but is scored as a requirement
        pool = POOL_UNIQ[pool_nm]
        others, same = [], []
        present = {x[:7] for x in allc}
        for s2 in pool:
            c2 = s2['c']
            if c2 == c:
                continue
            if c2[:7] in ZERO:
                continue
            cand = [x for x in allc if x != c] + [c2]
            if s2['code'] != byc[c]['code'] and s2['code'] in present:
                continue
            # an elective swap must advance the SAME ledger item, or the saving changes
            if c in items and s2['code'] != byc[c]['code']:
                import rank4 as _R4
                if _R4.item_of_section(s2, code) != items[c]:
                    continue
            # a requirement swap must stay inside the same requirement (pool guarantees it),
            # and a language swap must keep the same difficulty tier
            if (c in LANGSET) != (c2 in LANGSET):
                continue
            v = _score_of(cand, items)
            if v is None or abs(v - base) > 1e-6:
                continue
            # ⛔ R282. The test above is "substitute and rescore to the same total" — it does
            # NOT check hours, but the label said "professor choice, and your fallback if this
            # one fills", which claims a drop-in replacement. UIC1551-04 (화8,9/목7) and
            # UIC1551-01 (화7/목8,9) score identically and were shown as interchangeable; they
            # are mirror-image weeks, not the same week with a different professor. Swapping
            # one in on 8/25 gives you a DIFFERENT timetable that happens to be worth the same.
            # Split the two cases and label them honestly.
            # ⭐ R284 — THE RULE (Iden, 2026-08-16): "it has to have the same cells to be
            # considered swappable. Otherwise, it shows up as a different timetable."
            #
            # A swap is a claim that you can substitute this section and still be looking at
            # THE SAME timetable. That is only true if the week is unchanged. If the cells
            # move, it is a different timetable — and the dedup (R278) already decides what
            # happens to those: it becomes its own card, or it does not make the top 50.
            # Either way it is not this card's business.
            #
            # This deletes the "equal-scoring, DIFFERENT hours" category outright rather than
            # relabelling it (R282) or cross-referencing it (R283). Both of those kept a
            # category that should not exist. Every other condition — identical score, same
            # ledger item, same difficulty tier, no conflict — still applies exactly as before.
            if not (s2['tm'] == byc[c]['tm'] and s2['pm'] == byc[c]['pm']
                    and s2['fm'] == byc[c]['fm']):
                continue
            (same if s2['code'] == byc[c]['code'] else others).append(s2)
        if same or others:
            out[c] = (same, others)
    return out


def grid(r):
    allc = r['requirements'] + r['electives'] + ([r['chapel']] if r['chapel'] != '-' else [])
    col = {c: PAL[i % len(PAL)] for i, c in enumerate(sorted({x[:7] for x in allc}))}
    occ = {}
    for c in allc:
        s = byc[c]
        for d in range(5):
            for p in range(1, 15):
                if (s['tm'] >> (d * 16 + p)) & 1:
                    occ[(d, p)] = (s['code'], s.get('n', ''), s.get('p', ''), col[s['code']],
                                   not ((s['pm'] >> (d * 16 + p)) & 1))
    ps = sorted({p for _d, p in occ}) or [1]
    free = [d for d in range(5) if not any((d, p) in occ for p in range(1, 15))]
    o = ['<table class="g"><tr><th></th>' +
         ''.join(f'<th class="{"fr" if d in free else ""}">{DN[d]}</th>' for d in range(5)) + '</tr>']
    for p in range(min(ps), max(ps) + 1):
        o.append(f'<tr><td class="hh">{8+p}:00</td>')
        for d in range(5):
            v = occ.get((d, p))
            if v:
                cd, nm, pr, c0, on = v
                o.append(f'<td class="on{" vid" if on else ""}" style="background:{c0}" '
                         f'title="{html.escape(cd)} · {html.escape(nm)}'
                         f'{" · " + html.escape(pr) if pr else ""}">{html.escape(cd)}</td>')
            else:
                o.append(f'<td class="{"fr" if d in free else ""}"></td>')
        o.append('</tr>')
    return ''.join(o) + '</table>', col, free


def _one(x, withname):
    """Always identify a replacement by its 분반 AND its hours — never by course code alone,
    which made two different 분반 of the same course render identically (card #17)."""
    bits = [f'<u>{html.escape(x["c"])}</u>']
    if withname:
        bits.append(html.escape((x.get('n') or '')[:24]))
    t = x.get('t') or ''
    if t:
        bits.append(f'<i>{html.escape(t)}</i>')
    p = x.get('p') or ''
    if p:
        bits.append(f'<s>{html.escape(p)}</s>')
    return ' '.join(bits)


def _swaphtml(sw, c):
    same, others = sw.get(c, ([], []))
    h2 = ''
    if same:
        h2 += ('<span class="alt sw"><b>' + str(len(same)) + ' other 분반, same hours</b> — a pure '
               'professor choice, and a true drop-in if this one fills: '
               + ' · '.join(_one(x, False) for x in same[:6]) + '</span>')
    if others:
        h2 += ('<span class="alt sw"><b>' + str(len(others)) + ' equal swap'
               + ('s' if len(others) > 1 else '') + '</b> — different course, identical score: '
               + ' · '.join(_one(x, True) for x in others[:5])
               + ('…' if len(others) > 5 else '') + '</span>')
    return h2


def courselist(r, col, sw):
    o = ['<ul class="cl">']
    tag = {'REQ': 'requirement'}
    for c in r['requirements']:
        s = byc[c]
        o.append(f'<li><b style="background:{col[s["code"]]}"></b><span><strong>'
                 f'{html.escape(c)}</strong> {html.escape(s.get("n","")[:34])}'
                 f'<span class="alt">requirement</span>{_swaphtml(sw, c)}</span>'
                 f'<em>{html.escape(s.get("t",""))}</em></li>')
    for c, it in zip(r['electives'], r['items']):
        s = byc[c]
        note = {'ME': 'Major Elective — real degree progress',
                'ECO1101': 'Major Required — real degree progress',
                'FREE': 'pure free elective — displaces something better',
                'DM': '2nd-major course'}.get(it, it)
        o.append(f'<li><b style="background:{col[s["code"]]}"></b><span><strong>'
                 f'{html.escape(c)}</strong> {html.escape(s.get("n","")[:34])}'
                 f'<span class="alt">{html.escape(note)}</span>{_swaphtml(sw, c)}</span>'
                 f'<em>{html.escape(s.get("t",""))}</em></li>')
    if r['chapel'] != '-':
        s = byc[r['chapel']]
        o.append(f'<li><b style="background:{col[s["code"]]}"></b><span><strong>'
                 f'{html.escape(r["chapel"])}</strong> chapel</span>'
                 f'<em>{html.escape(s.get("t",""))}</em></li>')
    return ''.join(o) + '</ul>'


CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--mut:#6b6b6b;--fai:#9a9a9a;--ln:#e4e4e0;--sub:#f0f0ec;--card:#fff;--warn:#b8562f}
@media(prefers-color-scheme:dark){:root{--bg:#161615;--fg:#eeeeec;--mut:#a0a09a;--fai:#77776f;--ln:#33332f;--sub:#1f1f1d;--card:#1b1b1a;--warn:#e08a5f}}
*{box-sizing:border-box}
body{margin:0;padding:26px 22px 60px;background:var(--bg);color:var(--fg);font:14px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI","Malgun Gothic",sans-serif}
h1{font-size:19px;margin:0 0 3px;font-weight:600}
.sub{color:var(--mut);font-size:12.5px;margin:0 0 14px;max-width:76ch}
.note{border:1px solid var(--warn);color:var(--warn);border-radius:8px;padding:8px 12px;font-size:12.5px;margin:0 0 16px}
.bar{display:flex;gap:7px;flex-wrap:wrap;align-items:center;position:sticky;top:0;z-index:5;background:var(--bg);padding:9px 0 11px;border-bottom:1px solid var(--ln);margin-bottom:16px}
.bar button{font:inherit;font-size:12.5px;padding:4px 11px;border:1px solid var(--ln);background:var(--sub);color:inherit;border-radius:99px;cursor:pointer}
.bar button[aria-pressed=true]{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.bar .lb{font-size:11px;color:var(--fai);letter-spacing:.08em;text-transform:uppercase;margin-left:6px}
.bar .n{color:var(--mut);font-size:12.5px;margin-left:auto}
.c{border:1px solid var(--ln);border-radius:10px;margin-bottom:12px;background:var(--card);overflow:hidden}
.c header{display:flex;gap:9px;align-items:center;flex-wrap:wrap;padding:9px 13px;border-bottom:1px solid var(--ln);background:var(--sub)}
.rk{font-weight:700;font-size:15px;font-variant-numeric:tabular-nums;min-width:34px}
.sc{font-weight:600;font-variant-numeric:tabular-nums;font-size:15px}
.tg{font-size:11.5px;color:var(--mut);border:1px solid var(--ln);border-radius:99px;padding:1px 9px;background:var(--bg)}
.tg b{color:var(--fg)}
.tg.good b{color:#4a8a3a}.tg.cost b{color:var(--warn)}
.body{display:flex;gap:18px;padding:13px;flex-wrap:wrap;align-items:flex-start}
.gw{flex:1 1 340px;min-width:300px}
table.g{border-collapse:collapse;width:100%;table-layout:fixed;font-size:10.5px}
.g th{font-weight:600;color:var(--mut);font-size:11px;padding:2px 0}
.g th.fr,.g td.fr{background:var(--sub)}
.g td{border:1px solid var(--ln);height:21px;text-align:center;color:#fff;font-size:9.5px;overflow:hidden}
.g td.hh{border:0;color:var(--fai);font-size:9.5px;text-align:right;padding-right:6px;width:44px}
.g td.on{border-color:transparent}
.g td.vid{background-image:repeating-linear-gradient(45deg,rgba(0,0,0,.22) 0 3px,transparent 3px 6px)}
.cl{flex:1 1 300px;min-width:280px;list-style:none;margin:0;padding:0}
.cl li{display:flex;gap:7px;align-items:baseline;padding:3.5px 0;border-bottom:1px solid var(--ln);font-size:12px}
.cl li:last-child{border:0}
.cl b{width:9px;height:9px;border-radius:2px;flex:none;position:relative;top:1px}
.cl span{flex:1;min-width:0}.cl strong{font-weight:650}
.cl em{font-style:normal;color:var(--fai);font-size:11px;white-space:nowrap}
.alt{display:block;font-size:10.5px;color:var(--mut)}
.alt.sw{margin-top:2px;line-height:1.45}
.alt.sw b{width:auto;height:auto;display:inline;background:none!important;color:var(--fg);font-weight:600}
.alt.sw u{text-decoration:none;font-variant-numeric:tabular-nums;color:var(--fg)}
.alt.sw i{font-style:normal;color:var(--fg);opacity:.75}
.alt.sw s{text-decoration:none;color:var(--fai)}
.hid{display:none}
"""

out = ['<!doctype html><html lang="en"><meta charset="utf-8">',
       '<title>Fall 2026 · v3 ranking</title>',
       '<meta name="viewport" content="width=device-width,initial-scale=1">',
       f'<style>{CSS}</style>',
       '<h1>Fall 2026 — ranked under v3</h1>',
       '<p class="sub">Ranked by this semester&rsquo;s week, plus the deferral cost saved by '
       'taking a major course now, minus what the postponed requirement costs the semester that '
       'receives it. No continuation proxy, no crowding curve. Hatched blocks are online hours: '
       'they hold a slot but do not put you on campus, so they never break a trip home.</p>',
       '<p class="note">⛔ Not registrable yet — the 8/14 seat pull has not been run. '
       'A 1학년 quota of 0 makes a section impossible, not merely competitive.</p>',
       '<div class="bar">',
       '<span class="lb">catalogue</span>',
       ''.join(f'<button data-y="{y}"{" aria-pressed=true" if y=="2026" else ""}>{y}</button>'
               for y in YEARS),
       '<span class="lb">QRM1001 slot</span>',
       '<button data-g="all geometries (expected)" aria-pressed="true">expected over all slots</button>',
       '<span class="lb">show</span>',
       '<button data-f="all" aria-pressed="true">all</button>',
       ''.join(f'<button data-f="{b}">{html.escape(LABEL[b].replace("postpones ",""))}</button>'
               for b in B if b != '-'),
       '<button data-f="-">nothing</button>',
       '<span class="n" id="n"></span></div>', '<div id="list">']

meta = []
for i, r in enumerate(cards):
    g, col, free = grid(r)
    allc = r['requirements'] + r['electives'] + ([r['chapel']] if r['chapel'] != '-' else [])
    tm = pm = fm = 0
    for c in allc:
        s = byc[c]; tm |= s['tm']; pm |= s['pm']; fm |= s['fm']
    _wv, presfree = week_value(pm, fm)
    cr = sum(byc[c].get('cr', 0) for c in r['requirements'] + r['electives'])
    nfree = sum(1 for x in r['items'] if x == 'FREE')
    meta.append(dict(i=i, base=r['score'], d=r['defer'], items=r['items'],
                     fut=round(future_value(r['defer'], r), 3),
                     total=round(sc(r, '2026', GEOS[0]), 3)))
    out.append(
        f'<article class="c" id="c{i}" data-defer="{r["defer"]}">'
        f'<header><span class="rk"></span><span class="sc"></span>'
        f'<span class="tg">{html.escape(LABEL[r["defer"]])}</span>'
        f'<span class="tg">home <b>{"".join(DN[d] for d in sorted(presfree)) or "—"}</b></span>'
        f'<span class="tg">nothing at all <b>{"".join(DN[d] for d in free) or "—"}</b></span>'
        f'<span class="tg">{cr:.0f} cr</span>'
        + (f'<span class="tg cost">spends <b>{nfree}</b> free elective{"s" if nfree>1 else ""}</span>'
           if nfree else '<span class="tg good">all <b>degree progress</b></span>')
        + '<span class="tg brk"></span></header>'
        f'<div class="body"><div class="gw">{g}</div>{courselist(r, col, equal_swaps(r))}</div></article>')

out += ['</div>',
        '<script>',
        f'const M={json.dumps(meta,ensure_ascii=False)};',
        """
let F='all';
// R294: the total is computed in Python by the partition DP and embedded per card. There is
// no client-side rescoring any more — the old page recomputed `score + Σunit_cost − K`, and
// K no longer exists.
function score(m){return m.total;}
function render(){
  const rows=M.map(m=>({m,s:score(m)})).filter(x=>x.s!==null).sort((a,b)=>b.s-a.s);
  const list=document.getElementById('list'); let shown=0;
  rows.forEach((x,idx)=>{
    const el=document.getElementById('c'+x.m.i);
    const vis=(F==='all'||x.m.d===F)&&idx<50;
    el.classList.toggle('hid',!vis);
    el.querySelector('.rk').textContent='#'+(idx+1);
    el.querySelector('.sc').textContent=x.s.toFixed(2);
    el.querySelector('.brk').innerHTML='Fall week <b>'+x.m.base.toFixed(1)+
      '</b> + rest of degree <b>'+x.m.fut.toFixed(1)+'</b>';
    if(vis){shown++; list.appendChild(el);}
  });
  document.getElementById('n').textContent=shown+' shown · scored over all 8 semesters';
}
document.querySelectorAll('.bar button').forEach(b=>b.onclick=()=>{
  const g=b.dataset.y?'y':b.dataset.g?'g':'f';
  document.querySelectorAll('.bar button').forEach(o=>{
    if((o.dataset.y&&g==='y')||(o.dataset.g&&g==='g')||(o.dataset.f&&g==='f'))
      o.setAttribute('aria-pressed', o===b);});
  if(g==='f')F=b.dataset.f;
  render();});
render();
""", '</script>']
open(P('TOP50_v3.html'), 'w', encoding='utf-8').write('\n'.join(out))
print(f"wrote TOP50_v3.html — {len(cards)} cards, {os.path.getsize(P('TOP50_v3.html'))//1024} KB")
