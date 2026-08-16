# -*- coding: utf-8 -*-
"""
test_v3.py — the 2026-08-10 findings as LIVE ASSERTIONS, not prose.

Same discipline as `test_retired.py` (R187): a measurement written down as a conclusion decays
silently, so every claim that could change the 8/25 decision is re-measured on every run. A
broken assertion is re-opened in GAPS.md; this file is never edited to make it pass.

Run:  D_LANG=10.0 python test_v3.py
"""
import json, os, sys, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
ok, bad = [], []


def check(rule, claim, cond, detail=''):
    (ok if cond else bad).append((rule, claim, detail))


# ---------------------------------------------------------------- R221 · W_E2
import rank as RK
check('R221', 'W_E2 = half of W_E1, as elicited ("10am about half is right")',
      abs(RK.W_E2 - RK.W_E1 / 2) < 1e-9, f'W_E1={RK.W_E1} W_E2={RK.W_E2}')

# ------------------------------------------------------- R226 · V's inert terms
import continuation as CN
check('R226', 'the campus bonus is still a per-candidate CONSTANT (π = 5 invariant)',
      CN.SINCHON_SEMESTER_VALUE > 0,
      'if a candidate ever changes n_신촌 this must be re-measured — it was inert on all 12 states')

# --------------------------------------- R228 · measured curvature vs the live curve
inc = CN.INC
live_convex = all(inc[i] <= inc[i + 1] + 1e-9 for i in range(len(inc) - 1))
meas = json.load(open(P('b1_K.json'), encoding='utf-8')) if os.path.exists(P('b1_K.json')) else {}
concave = []
for name, rec in meas.items():
    c = rec.get('curve', {})
    v = [c[str(n)]['K'] for n in range(6) if str(n) in c and c[str(n)]]
    if len(v) >= 4:
        concave.append(v[0] >= v[-1])
check('R228', 'the LIVE crowding curve is convex while every MEASURED curve is concave',
      live_convex and concave and all(concave),
      f'live INC increasing={live_convex}; measured decreasing={sum(concave)}/{len(concave)} '
      f'-> continuation.INC must not be used for a deferral verdict')

# ----------------------------------------- R227/R232 · the Lang tier is SEASONAL
import pools_past as PP
import difficulty as DIFF
easy_sin = {'S': 0, 'F': 0}
for lab, rows in PP.terms().items():
    sea = PP.SEASON[lab.split('-')[1]]
    for r in rows:
        if str(r.get('subjtnb')) in DIFF.LANG_EASY and r.get('campsDivNm') == '신촌':
            easy_sin[sea] += 1
check('R232', 'the EASY language tier runs at 신촌 in Spring and NEVER in Fall',
      easy_sin['S'] > 0 and easy_sin['F'] == 0,
      f"신촌 easy-tier sections: Spring {easy_sin['S']}, Fall {easy_sin['F']} "
      f'-> P(hard)=1 applies only to a 신촌 FALL receiving semester')

hard_sin = sum(1 for lab, rows in PP.terms().items() for r in rows
               if str(r.get('subjtnb')) in DIFF.LANG_HARD and r.get('campsDivNm') == '신촌')
check('R232', 'the HARD tier is genuinely available at 신촌 (mileage_history was just thin)',
      hard_sin > 0, f'{hard_sin} 신촌 hard-tier sections across six terms')

# ------------------------------------------------- R229 · the precedence fix holds
import semester_sim as SS
_f, src = SS.sections_for('QRM1001', 'F', '국제')
cur_mask = _f[0]['tm'] if _f else 0
raw = json.load(open(P('raw_2026F.json'), encoding='utf-8'))
raw = raw if isinstance(raw, list) else list(raw.values())[0]
cat = [PP.parse(r.get('lctreTimeNm')) for r in raw if str(r.get('subjtnb')) == 'QRM1001']
check('R229', 'the CURRENT catalogue outranks history for the current term',
      bool(cat) and cur_mask == cat[0], f'sections_for -> {src}')

# ------------------------------------------ R236 · FREE is a residual, not a quota
from plan_model import ITEMS, TOTAL_CREDITS, DONE_CREDITS
by = {i['key']: i for i in ITEMS}
resid = TOTAL_CREDITS - DONE_CREDITS - sum(
    i['credits'] * i['count'] for i in ITEMS if i['key'] != 'FREE')
check('R236', 'FREE is the RESIDUAL of the degree arithmetic, not an allowance',
      abs(resid - by['FREE']['credits'] * by['FREE']['count']) < 1e-9,
      f"residual {resid} cr == FREE {by['FREE']['credits']*by['FREE']['count']} cr")
check('R236', 'FREE is the LEAST constrained ledger item (so deferring it is ~free)',
      by['FREE']['supply'] == max(i['supply'] for i in ITEMS)
      and by['FREE']['chart_year'] is None,
      f"supply {by['FREE']['supply']}, chart_year {by['FREE']['chart_year']}")

# --------------------------------- R227 · the Lang ledger item is STILL inconsistent
lang = by['Lang']
check('R227', 'the Lang ledger item names only easy-tier codes while claiming campus "any"',
      not (lang['campus'] == 'any' and set(lang['codes']) <= DIFF.LANG_EASY),
      f"campus={lang['campus']} codes={lang['codes']} — easy tier has 0 신촌 sections in Fall; "
      f'k_real.py bypasses this by using difficulty.LANG_* directly')

# --------------------------------------------- R225 · the ledger placeholders remain
nocode = [i['key'] for i in ITEMS if not i.get('codes')]
units = sum(i['count'] for i in ITEMS if not i.get('codes'))
check('R225', 'every ledger item has a course identity',
      not nocode, f'{units} units across {nocode} have no codes — their hours are ASSUMED')

# ------------------------ pool duplication (found via a display bug on card #17)
import rank3 as _R3
_P = _R3.build()[0]
_dup = {nm: len(v) - len({x['c'] for x in v}) for nm, v in _P.items()}
_tot = sum(_dup.values())
check('R237', 'rank3 pools are free of duplicate section rows',
      _tot == 0,
      f'{_tot} redundant rows {[k for k,v in _dup.items() if v]} — refetch_listings v4 keeps one '
      f'record per (section, query) so 과목종별 is not collapsed (its v3 bug). Correct for the '
      f'catalogue; anything that ITERATES a pool must deduplicate on section id first.')

# ------- R202/R152 · the Korean ME cap lived inside the layer v3 DELETED -----------
import rank4 as _R4
_P2 = _R3.build()[0]
import fm_fix as _FF, eligibility as _EL
_FF.apply(_P2, verbose=False); _EL.apply(_P2, verbose=False)
_code = lambda s: s['code']
_me = {}
for _s in _P2['OPEN']:
    if _R4.item_of_section(_s, _code) == 'ME':
        _me.setdefault(_s['c'], _s)
_capped = [c for c, s in _me.items()
           if s.get('lang') != '10' and ('상경' in (s.get('dept') or '') or
                                         '응용통계' in (s.get('dept') or ''))]
check('R152/R202', 'the Korean ME cap does not bind in Fall 2026',
      len(_capped) <= 4,
      f'{len(_capped)} of {len(_me)} ME-eligible sections are Korean 상경·응통. '
      f'⚠ the cap is enforced ONLY inside continuation.solve(), which v3 does not import — '
      f'if this count ever exceeds 4, nothing in the v3 path will notice.')

_noten = {}
for _pool in ('WCiv', 'LHP', 'SciRD', 'MR'):
    for _s in _P2[_pool]:
        if _s.get('lang') != '10':
            _noten.setdefault(_s['c'], _pool)
check('R92/R202', 'CC and MR pools stay English-taught',
      not _noten, f'non-English sections in a CC/MR pool: {dict(list(_noten.items())[:4])}')

# ------------------------------------ R247 · the seat pull, and its load-bearing file
SEATS = {}
if os.path.exists(P('fall2026_seats.json')):
    try:
        SEATS = json.load(open(P('fall2026_seats.json'), encoding='utf-8'))
    except Exception:
        SEATS = {}

check('R247', 'fall2026_seats.json exists — eligibility.py FILTERS on it, silently if absent',
      len(SEATS) > 100,
      f'{len(SEATS)} sections. If this file goes missing the 학년별정원 filter stops with no '
      f'error and the barred sections re-enter the pools.')


def _sy(sid):
    r = SEATS.get(sid)
    return [r.get(f'sy{i}PercpCnt') or 0 for i in range(1, 7)] if r else None


_star = _sy('UIC1561-01-00')
check('R247', 'UIC1561-01-00 does NOT bar a 1학년 (the 35.72 question)',
      _star is not None and not (any(_star) and _star[0] == 0),
      f'sy1..sy6 = {_star} — all-zero means NO per-year scheme, which is NO gate (R2/R134). '
      f'If this ever flips, the recommendation dies and fallback.json scores the branch at 28.911.')

_barred = {s for s, r in SEATS.items() if r
           and any(r.get(f'sy{i}PercpCnt') or 0 for i in range(1, 7))
           and not (r.get('sy1PercpCnt') or 0)}
import rank3 as _R3b, fm_fix as _FFb, eligibility as _ELb
_P3 = _R3b.build()[0]
_FFb.apply(_P3, verbose=False)
_ELb.apply(_P3, verbose=False)
_live = {x['c'] for v in _P3.values() for x in v}
check('R247', 'every 1학년-barred section is actually absent from the pools after filtering',
      _barred and not (_barred & _live),
      f'barred per the pull: {sorted(_barred)}; still in a pool: {sorted(_barred & _live)}')

# ---------------------- R248 · atnlcPercpCnt is NOT capacity, and must not reach a score
_bycode = collections.defaultdict(list)
for _s, _r in SEATS.items():
    if _r:
        _bycode[_s.split('-')[0]].append(_r)
_multi = {c: v for c, v in _bycode.items() if len(v) > 1}
_const = [c for c, v in _multi.items() if len({r.get('atnlcPercpCnt') for r in v}) == 1]
check('R248', 'atnlcPercpCnt is constant across 분반 -> it is NOT section capacity',
      _multi and len(_const) / len(_multi) > 0.9,
      f'{len(_const)}/{len(_multi)} multi-분반 courses hold it constant regardless of 강의실 '
      f'(UIC2151: 9 분반, 4 rooms, all "3"). It is a per-COURSE administrative number, so '
      f'여석 = 정원 - 신청 is meaningless and must never be computed.')

_SCORING = ['rank.py', 'rank2.py', 'rank3.py', 'rank4.py', 'research_v3.py', 'fallback.py',
            'plan_model.py', 'difficulty.py', 'continuation.py', 'semester_sim.py',
            'k_real.py', 'b1_curve.py', 'render_v3.py', 'render_v3_top50.py']
_leak = []
for _f in _SCORING:
    _p = P(_f)
    if os.path.exists(_p) and 'PercpCnt' in open(_p, encoding='utf-8', errors='ignore').read():
        _leak.append(_f)
check('R248', 'no scoring/ranking/rendering module reads the seat-count fields',
      not _leak,
      f'{_leak or "clean"} — only eligibility.py (sy1..sy6, the year gate) and the fetcher may '
      f'touch these fields. A 정원/신청 number entering a score would be R248 violated.')

# ---------------------------------------------- R249 · a blank row is not a bar
_blank = [s for s, r in SEATS.items() if not r]
check('R249', 'blank mileage rows exist and are NOT treated as bars',
      _blank and not (set(_blank) & _barred) and
      all(s in _live or s not in {x['c'] for v in _R3b.build()[0].values() for x in v}
          for s in ['YCE1253-01-00'] if s in SEATS),
      f'{len(_blank)} sections returned no row, including YCE1253-01-00 which is IN the '
      f'recommendation. Freshmen are invisible in this table (R7) and per-year quotas are '
      f'optional (R134), so absence is absence of evidence.')

# ------------------------------ R250 · the branch cache must not outlive its constants
import research_v3 as _RV
_parts = sorted(__import__('glob').glob(P('_v3_parts_f*/part_*.json')))
_unstamped = []
for _fp in _parts:
    try:
        _c = (json.load(open(_fp, encoding='utf-8')) or {}).get('consts')
    except Exception:
        _c = None
    if not _c:
        _unstamped.append(os.path.basename(os.path.dirname(_fp)) + '/' + os.path.basename(_fp))
check('R250', 'every cached branch records the constants it was scored with',
      _parts and not _unstamped,
      f'{len(_parts)} part files, {len(_unstamped)} unstamped {_unstamped[:4]} — STATE is keyed '
      f'on MAX_FREE ALONE, so without the stamp a changed D_LANG silently reuses the old '
      f'result. That is why neither D_LANG nor GPA_GATE_MULT had ever really been swept.')

_saved = (_RV.DIFF.D_LANG, _RV.DIFF.GPA_GATE_MULT)
_RV.DIFF.D_LANG = _saved[0] + 123.0
_stale_detected, _why = _RV.cache_is_valid(P('_v3_parts_f2/part_Lang.json'))
_RV.DIFF.D_LANG, _RV.DIFF.GPA_GATE_MULT = _saved
check('R250', 'a changed scoring constant INVALIDATES the cache',
      not _stale_detected,
      f'perturbing D_LANG by +123 -> cache_is_valid says "{_why}". If this ever reports '
      f'"current", every sensitivity sweep silently returns the baseline again.')

# --------------------- R251 · the unelicited constants, measured against the actual verdict
_sw = json.load(open(P('sweep_holes.json'), encoding='utf-8')) \
    if os.path.exists(P('sweep_holes.json')) else {}
_by_d = {}
for _k, _v in _sw.items():
    _d, _g = (float(x) for x in _k.split('|'))
    _by_d.setdefault(_d, {})[_g] = _v['defer']
_gate_inert = all(len(set(_g.values())) == 1 for _g in _by_d.values() if len(_g) > 1)
check('R251', 'GPA_GATE_MULT is inert FOR THE VERDICT (it multiplies a zero term)',
      _sw and _gate_inert,
      'the winning branch DEFERS Language, so sum(DIFF.steps(...)) = 0 and the whole `dif` '
      'term vanishes regardless of the multiplier. ⚠️ It stops being inert the instant the '
      'verdict flips to TAKING a language — and it has never been elicited.')

_flip = sorted(d for d in _by_d if any(v != 'Lang' for v in _by_d[d].values()))
check('R251', 'the verdict survives D_LANG far below its unelicited default',
      _sw and _flip and max(_flip) < DIFF.D_LANG / 2,
      f'defer!=Lang only at D_LANG <= {max(_flip) if _flip else "n/a"}; the default in force is '
      f'{DIFF.D_LANG}. Measured by re-SEARCHING at each grid point (sweep_holes.py), not by '
      f'rescoring a fixed candidate set — sweep_difficulty.py did the latter and has been '
      f'dead with a TypeError since R190.')

# ------------------- R259 · a NO-DATA bracket must not assert certainty on both arms
import risk as _RK
_lo, _hi, _b = _RK.p_win_bracket('ZZZ9999', 36, '국제')     # a course that cannot exist
check('R259', 'p_win_bracket with NO history returns the WIDEST bracket, not certainty',
      'NO DATA' in _b and _lo == 0.0 and _hi == 1.0,
      f'({_lo}, {_hi}) — it returned (1.0, 1.0) until 2026-08-16: a POINT estimate of certain '
      f'acquisition dressed as a neutral default, and R254 caught it deciding the deferral '
      f'verdict. Equal arms assert knowledge; with no observations the arms must be 0 and 1.')

# ------------------------------------------------------------------- report
print('=' * 78)
for r, c, d in ok:
    print(f'✅ HOLDS       [{r}]  {c}')
    if d:
        print(f'      {d}')
for r, c, d in bad:
    print(f'❌ DOES NOT HOLD [{r}]  {c}')
    if d:
        print(f'      {d}')
print('=' * 78)
print(f'{len(ok)} hold · {len(bad)} broken')
if bad:
    print('\n⛔ A finding has expired or a known defect is still live. Re-open it in GAPS.md —')
    print('   do not edit this test to make it pass.')
sys.exit(0)
