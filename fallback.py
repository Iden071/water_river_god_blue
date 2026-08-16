# -*- coding: utf-8 -*-
"""
fallback.py — what to click next if a section is gone.  ->  fallback.json

THE GAP THIS CLOSES (G-5 / G-6, open since session one)
On 8/25 Iden does not "choose a timetable" — he clicks in an order, on 대기순번제, and finds
out what he got. The model has only ever emitted a ranked SET. `PLANS.md` has tracked the
ranking and the click-order as separate work items throughout, and R168 recorded that they are
one object.

The equal-swap lists in `TOP50_v3.html` are not a fallback chain: by construction the optimum
has no equal-score alternative, so every course in the recommendation shows "no fallback".
That is tautological, not informative. **What is needed is the best DEGRADED timetable, scored**
— G-5's own words: "degraded branches must be scored, not merely listed".

WHAT THIS COMPUTES — and it needs no seat data
For each section in the recommendation, delete that 분반 from the pool and re-run the full v3
search. The result is the best timetable reachable *without* it, and the difference is what
losing that section actually costs.

    cost(section) = best v3 score with it − best v3 score without it

That is the click-order priority: **click the section whose loss costs most, first.**

⚠️ WHAT THE 8/14 PULL ADDS, AND WHAT IT DOES NOT
The 8/14 seat data supplies the PROBABILITY that each section is gone. It does not change any
number here. Cost × probability is the full picture; this file is the cost half, and it is
computable today.
"""
import json, os, sys, collections, copy, time

import rank as RK
import rank2 as R2, difficulty as DIFF
R2.LANG = set(DIFF.LANG_ALL)
import rank3, fm_fix, eligibility
from rank2 import fast_score, year_gap_pen, eff_year, YEAR_PEN
import research_v3 as RV

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
YEAR, GEO = '2026', '목4,5,6'
# rows kept per branch before maximising `total`. Must be large enough that the argmax of
# `total` is inside it; 60 was not (R260 — the winner sat at rank 115 by `score`).
# ⛔ R269. 3000 was STILL too small. R260 fixed `rows[:60]` but left `TOPN = 3000`, which is
# the same defect one level up: `run_branch` ranks by `score`, the objective is
# `score + Σunit_cost − K`, so the argmax can sit outside any score-ranked prefix. After the
# R264/R267 rebuild widened the `disp` spread it moved past rank 3000, and the symptom was
# NEGATIVE loss costs in the click order — losing a section appeared to IMPROVE the optimum,
# which is only possible if the base search never found it. Measured convergence:
#     TOPN  3000 -> 57.838      12000 -> 68.299      40000 -> 68.299
TOPN_SEARCH = int(os.environ.get('FB_TOPN', 20000))
B = ('-', 'MR', 'WCiv', 'LHP', 'SciRD', 'Lang')
MAP = {'WCiv': 'WCiv', 'LHP': 'LHP', 'SciRD': 'SciRD', 'Lang': 'Lang·hard'}

D = json.load(open(P('k_real.json'), encoding='utf-8'))
KD = collections.defaultdict(lambda: collections.defaultdict(dict))
for k, v in D['k'].items():
    n_, y, g, nn = k.split('|')
    if v[0] is not None and int(nn) == 4:
        KD[n_][y][g] = v[0]


def unit_cost(nm, y=YEAR):
    vals = [D['disp'].get(f"{nm}|{c}{s}|{y}") for c, s in (('국제', 'S'), ('신촌', 'F'))]
    vals = [v[0] for v in vals if v]
    if not vals:
        return 0.0
    yg = {'ECO1101': min(-year_gap_pen(z, 1) for z in (2, 3, 4)),
          'ME': min(-year_gap_pen(z, 3) for z in (2, 3, 4))}.get(nm, 0.0)
    return min(vals) + yg


# ---------------------------------------------------------------------------
# R272 — ONE RULE FOR EVERY BRANCH. No pinning, no special case, no bare min().
# ---------------------------------------------------------------------------
# The old version had two code paths and neither was chosen on purpose:
#     if b == 'MR':  return KD['MR'][y].get(g)   # pinned to a named geometry, enumerated
#     return min(d.values())                     # everything else: best case, assumed
# Iden, 2026-08-16: "I don't understand why there is an assymetry at all (except things I
# explicitly mentioned, like language difficulty)."  He is right — nobody chose it.
#
# The asymmetry also ran one way: `min()` rewards whichever item happens to have the most
# observed geometries, because min over 11 draws is an extreme and min over 1 is the value.
#
# THE UNIFORM RULE. You *choose* your future slot, but you may not get your first pick.
# Sort an item's geometries cheapest first; take the first one you actually obtain:
#
#     P(geometry obtainable) = 1 − Π (1 − p_course)   over courses offering that shape
#     E[K] = Σ  K_g · P(g) · Π (1 − P(cheaper g'))    + P(none) · worst
#
# min() and median() were both guesses at the same unmeasured quantity. This measures it:
#   p = 1  -> reduces exactly to min()          (you always get your pick)
#   p -> 0 -> reduces to the worst geometry     (you never do)
# `t` walks the measured bracket: 0 = p_lo (must MATCH the top bidder), 1 = p_hi (need only
# beat the weakest). Courses with no mileage history contribute the widest bracket (R259).
#
# ⚠️ SCOPE (purpose check, 2026-08-16). K is CONSTANT within a branch, so this changes only
# WHICH requirement is deferred — measured spread across the top 50 is 0.000, against 5.354
# for week-comfort and 1.666 for unit_cost. It must stay one number per branch. Do not grow
# it into a registration-forecasting subsystem; that is not what the model is for.
K_T = float(os.environ.get('K_T', 0.5))       # where in the measured bracket to evaluate

_PCACHE = {}


def _p_course(code, campus, t):
    key = (code, campus)
    if key not in _PCACHE:
        import risk
        lo, hi, basis = risk.p_win_bracket(code, 36, campus)
        if lo is None or hi is None:          # CAP-12: bidding is not a lever (R3)
            lo, hi = 0.0, 1.0
        _PCACHE[key] = (lo, hi)
    lo, hi = _PCACHE[key]
    return lo + t * (hi - lo)


_OWN = {}


def _geom_owners(name, camp, sea):
    """geometry label -> the course codes observed running at that shape."""
    if (name, camp, sea) in _OWN:
        return _OWN[(name, camp, sea)]
    import k_real as KR, pools_past as PP
    codes, _c, _s = KR.CASES[name]
    own = collections.defaultdict(set)
    for c in codes:
        for _lab, sigs in PP.course_geometries(c, camp, sea).items():
            for g in sigs:
                own[PP.show(g[0])].add(c)
    _OWN[(name, camp, sea)] = own
    return own


# ⚠️ `total()` calls this once per ROW — 113,278 rows x 6 branches. Uncached it rebuilt the
# owner map and re-read the mileage history every call and the run never finished.
_KCACHE = {}


def kdefer(b, y=YEAR, g=GEO, t=None):
    """Expected K for deferring branch `b`. Identical treatment for every branch."""
    if b == '-':
        return 0.0
    t = K_T if t is None else t
    ck = (b, y, t)
    if ck in _KCACHE:
        return _KCACHE[ck]
    v = _kdefer_uncached(b, y, t)
    if v is not None:
        # ⭐ R281. Deferring does not escape the professor. Subtracting the carry makes the
        # term CANCEL when persistence is 1.0 — a rating on a course whose professor never
        # changes then correctly has no effect on whether to defer it.
        v -= _prof_carry(b)
    _KCACHE[ck] = v
    return v


_PC = {}


def _prof_carry(b):
    if b in _PC:
        return _PC[b]
    import prof as PROF, k_real as KR, rank3, fm_fix, eligibility
    name = MAP.get(b, b)
    codes = KR.CASES[name][0] if name in KR.CASES else []
    global _POOLS_FOR_CARRY
    try:
        Pp = _POOLS_FOR_CARRY
    except NameError:
        import io as _io, contextlib as _cx
        with _cx.redirect_stdout(_io.StringIO()):
            Pp = rank3.build()[0]
            fm_fix.apply(Pp, verbose=False)
            eligibility.apply(Pp, verbose=False)
        _POOLS_FOR_CARRY = Pp
    secs = [s['c'] for v in Pp.values() for s in v if s['c'].split('-')[0] in set(codes)]
    _PC[b] = PROF.carry(codes, secs)
    return _PC[b]


def _kdefer_uncached(b, y, t):
    import k_real as KR
    name = MAP.get(b, b)
    d = KD[name].get(y)
    if not d:
        return None
    codes, camp, sea = KR.CASES[name]
    own = _geom_owners(name, camp, sea)
    geos = sorted(d.items(), key=lambda kv: kv[1])          # cheapest first
    e, surv = 0.0, 1.0
    for lab, k in geos:
        cs = own.get(lab) or set(codes)      # unowned -> treat as any course could offer it
        pg = 1.0
        for c in cs:
            pg *= (1.0 - _p_course(c, camp, t))
        pg = 1.0 - pg
        e += k * surv * pg
        surv *= (1.0 - pg)
    return e + surv * geos[-1][1]            # nothing obtained -> the worst shape


def total(row, b):
    k = kdefer(b)
    if k is None:
        return None
    return row['score'] + sum(unit_cost(i) for i in row['items']) - k


def search(exclude=(), topn=1):
    """Best v3 timetable per branch with `exclude` removed from every pool."""
    Pp, sig, sigs, SIGCODES, code = rank3.build()
    fm_fix.apply(Pp, verbose=False)
    eligibility.apply(Pp, verbose=False)
    ZERO = {c[:7] for c, s in
            {x['c']: x for v in Pp.values() for x in v}.items() if s['fm'] == 0 and s['tm']}
    for pool in Pp.values():
        pool[:] = [s for s in pool if s['c'] not in exclude and s['code'] not in ZERO]
    LANGP = [s for s in Pp['OPEN'] if code(s) in R2.LANG]
    ELEC = [s for s in Pp['OPEN'] if code(s) not in R2.LANG]
    REQ = {'MR': Pp['MR'], 'WCiv': Pp['WCiv'], 'LHP': Pp['LHP'],
           'SciRD': Pp['SciRD'], 'Lang': LANGP}
    best = None
    for b in B:
        if any(not REQ[n] for n in REQ if n != b):
            continue                      # a requirement pool was emptied -> branch impossible
        # ⛔ R260. This was `RV.TOPN = 60` with `rows[:60]` below — TRUNCATE THEN MAXIMISE.
        # `run_branch` ranks by raw `score`, but the objective is
        #     total = score + Σunit_cost(items) − kdefer(b)
        # and `unit_cost` — the displacement credit for an elective that discharges a
        # constrained ledger item — is NOT part of `score`. So the argmax of `total` need not
        # rank highly by `score`, and did not: the true maximiser sat at **rank 115**, worth
        # 78.622 against the 64.633 this function used to report. A 13.989 error, larger than
        # every margin argued from this model.
        RV.TOPN = TOPN_SEARCH
        import io, contextlib
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                RV.run_branch(b, Pp, REQ, ELEC, code)
        except Exception:
            continue
        p = os.path.join(RV.STATE, f'part_{b}.json')
        if not os.path.exists(p) or not os.path.getsize(p):
            continue
        rows = json.load(open(p, encoding='utf-8'))['rows']
        for r in rows:                      # ⭐ every row, not a score-ranked prefix
            v = total(r, b)
            if v is not None and (best is None or v > best[0]):
                best = (v, b, r)
        open(p, 'w').close()   # the mount permits truncation, not deletion (INDEX trap #5)
    return best


if __name__ == '__main__':
    os.environ.setdefault('MAX_FREE', '2')
    RV.MAX_FREE = 2
    RV.STATE = os.path.join(HERE, '_fb_tmp')
    os.makedirs(RV.STATE, exist_ok=True)
    t0 = time.time()
    base = search()
    v0, b0, r0 = base
    secs = r0['requirements'] + r0['electives'] + ([r0['chapel']] if r0['chapel'] != '-' else [])
    print(f"BASE: {v0:.2f} · defer {b0}")
    print(f"  {' '.join(secs)}\n")
    print("IF THIS SECTION IS GONE ON 8/25 — the best you can still do, and what it costs")
    print(f"  {'section':16s} {'cost':>7}  best fallback")
    out = {'base': dict(score=round(v0, 3), defer=b0, sections=secs), 'loss': {}}
    for c in secs:
        alt = search(exclude={c})
        if alt is None:
            print(f"  {c:16s} {'—':>7}  ⛔ NO legal timetable at all")
            out['loss'][c] = None
            continue
        v, b, r = alt
        aset = r['requirements'] + r['electives'] + ([r['chapel']] if r['chapel'] != '-' else [])
        gained = [x for x in aset if x not in secs]
        out['loss'][c] = dict(score=round(v, 3), cost=round(v0 - v, 3), defer=b, sections=aset)
        print(f"  {c:16s} {v0-v:7.2f}  {v:.2f} · defer {b} · swap in "
              f"{' '.join(gained) or '(same courses, different 분반)'}")
    json.dump(out, open(P('fallback.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    order = sorted((x for x in out['loss'].items() if x[1]), key=lambda t: -t[1]['cost'])
    print(f"\n⭐ CLICK ORDER on 8/25 — most costly to lose, first:")
    for i, (c, d) in enumerate(order, 1):
        print(f"   {i}. {c:16s} (losing it costs {d['cost']:.2f})")
    print(f"\n[{time.time()-t0:.0f}s]  wrote fallback.json")
