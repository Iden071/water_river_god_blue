# -*- coding: utf-8 -*-
"""
semester_sim.py — THE FIX for R208. Score a future semester from REAL SECTIONS, not a count.

THE PROBLEM IT REPLACES
-----------------------
`continuation.py` scores a future semester with a one-dimensional summary: *how many
low-supply courses does it hold*. R208 proved that summary is not sufficient —

  · within a SINGLE requirement pool (identical `supply`, identical ledger item) the week
    damage of one section ranges over **67.6 points**;
  · the same course at its Fall slot vs its Spring slot differs by **25.6** (QRM1001,
    목4,5,6 vs 금1,2,3 — R207);
  · and the curve uses the exhaustive BEST arrangement, where a typical semester is ~69
    points worse.

So Fall 2026 is scored over real sections at real times, while the continuation is scored by
counting. Deferring moves a course across that seam — out of measurement and into an
optimistic proxy. **The objective systematically flatters deferral.**

THE FIX
-------
Stop summarising. For a given semester (its item list, term and campus):

  1. Every item that maps to REAL COURSE CODES contributes its ACTUAL sections.
     ⭐ Where direct evidence exists for that TERM it is used; otherwise the Fall 2026
     catalogue stands in and the substitution is REPORTED, never silent.
  2. Abstract items (ME / DM / FREE) draw from the real catalogue for that campus.
  3. The week is computed with `fast_score` — the same function Fall 2026 uses.
     **Both halves of the objective now run through one scorer.**
  4. The pinned requirements are enumerated; the filler is optimised, because that is what
     Iden would actually do. The spread across pinned choices is the honest uncertainty.

WHAT IT DOES NOT DO
-------------------
It does not invent a Spring 2027 catalogue. Where a term has no evidence it says so, and the
Fall stand-in is flagged in the output. The point is not to predict 2027; it is to stop
scoring the future with a statistic that provably cannot represent it.
"""
import json, os, itertools, statistics, collections, random

import rank2 as R2, difficulty as DIFF
R2.LANG = set(DIFF.LANG_ALL)
import rank3
from rank2 import fast_score

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# SECTION POOLS — real times, per campus, with per-term evidence where it exists
# ---------------------------------------------------------------------------
_P = rank3.build()[0]
_INTL = {}
for _v in _P.values():
    for _s in _v:
        _INTL.setdefault(_s['c'], _s)

_raw = json.load(open(os.path.join(HERE, 'raw_2026F.json'), encoding='utf-8'))
_raw = _raw if isinstance(_raw, list) else list(_raw.values())[0]
_mh = json.load(open(os.path.join(HERE, 'mileage_history.json'), encoding='utf-8'))

PERIOD = {str(i): i for i in range(1, 16)}
DAY = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}


def parse_time(t):
    """'화5,6,목4' or '수7,8/금7' -> (time mask, set of weekdays). Mirrors build_canonical.

    ⛔ REWRITTEN 2026-08-16 (R264). It did NOT mirror `build_canonical` — it was the same
    split-on-comma parser as the old `pools_past.parse`, and it dropped or fabricated hours
    on any parenthesised block: `수6,7(수8,9)` -> `수6,9`. Measured over `raw_2026F.json`:
    **194 of 775 신촌 sections (25%) mis-parsed.**

    The asymmetry was the dangerous part. `semester_sim._INTL` is built from `rank3.build()`,
    i.e. from `canonical_2026F.json`, which went through the CORRECT parser — 0 of 341
    국제 sections mismatched. `_SIN` is built from `raw_2026F.json` through this function.
    So 국제 was parsed correctly and 신촌 was not, and 신촌 is exactly where `Lang·hard`,
    `LHP` and `SciRD` are received.
    """
    if not t:
        return 0, set()
    try:
        from build_canonical import seg_blocks
        blocks = seg_blocks(str(t))
    except Exception:
        blocks = set()
        day, num = None, ''
        for ch in str(t) + '#':
            if ch.isdigit():
                num += ch
                continue
            if num:
                if day is not None:
                    blocks.add((day, int(num)))
                num = ''
            if ch in DAY:
                day = DAY[ch]
    tm, days = 0, set()
    for d, p in blocks:
        if 1 <= p <= 15 and d < 7:
            tm |= 1 << (d * 16 + p)
            if d < 5:
                days.add(d)
    return tm, days


def sinchon_sections():
    out = {}
    for r in _raw:
        if r.get('campsDivNm') != '신촌':
            continue
        tm, _ = parse_time(r.get('lctreTimeNm'))
        if tm:
            out.setdefault(f"{r.get('subjtnb')}-{r.get('corseDvclsNo')}",
                           dict(code=str(r.get('subjtnb')), tm=tm, pm=tm))
    return out


_SIN = sinchon_sections()


def term_evidence(code, term, campus):
    """Sections for `code` observed in THAT term at THAT campus. [] if none."""
    want = '10' if term == 'S' else '20'
    out = []
    for r in _mh:
        if r.get('subjtnb') != code or r.get('campsDivNm') != campus:
            continue
        if str(r.get('smtDivCd')) != want:
            continue
        tm, _ = parse_time(r.get('lctreTimeNm'))
        if tm:
            out.append(dict(code=code, tm=tm, pm=tm,
                            src=f"{r.get('_syy')}-{'1' if want=='10' else '2'} observed"))
    return out


def sections_for(code, term, campus):
    """Real sections for a course code, preferring direct evidence for that term.

    Returns (list_of_sections, provenance_string).

    ⛔ FIXED 2026-08-10 (R229). Historical evidence used to outrank the CURRENT catalogue
    unconditionally, so asking for Fall at 국제 returned QRM1001 at 금1,2,3 (from 2025-2)
    while the Fall 2026 catalogue plainly shows 목4,5,6. Right for an unknown future term,
    wrong whenever the present one is known. The live catalogue IS the newest observation of
    its own term, so it now wins for that term.
    """
    CURRENT_TERM = 'F'          # raw_2026F.json / canonical_2026F.json are Fall 2026
    if term == CURRENT_TERM:
        src = _INTL if campus == '국제' else _SIN
        cur = [dict(code=code, tm=s['tm'], pm=s.get('pm', s['tm']),
                    src='Fall 2026 catalogue (current term — outranks history, R229)')
               for c, s in src.items() if s['code'] == code]
        if cur:
            return cur, cur[0]['src']
    ev = term_evidence(code, term, campus)
    if ev:
        return ev, ev[0]['src']
    if campus == '국제':
        got = [dict(code=code, tm=s['tm'], pm=s['pm'], src='Fall 2026 catalogue')
               for c, s in _INTL.items() if s['code'] == code]
    else:
        got = [dict(code=code, tm=s['tm'], pm=s['pm'], src='Fall 2026 catalogue')
               for c, s in _SIN.items() if s['code'] == code]
    return got, ('Fall 2026 stand-in ⚠️' if got and term == 'S' else
                 'Fall 2026 catalogue' if got else 'NO DATA')


_FP = {}


def filler_pool(campus, n=200):
    """Real sections to fill unconstrained slots, from the right campus.

    ⛔ FIXED: an earlier version shuffled RANDOMLY and truncated. That made branches
    incomparable — a pinned course could be lighter than anything surviving in the pool, so
    adding a constraint appeared to IMPROVE the week, which is impossible. Caught by the
    monotonicity sanity check, not by inspection.
    Keep the LIGHTEST distinct time-masks: an optimiser would use exactly those, so the
    truncation is now aligned with what the search wants instead of fighting it.
    """
    if campus in _FP:
        return _FP[campus]
    src = _INTL if campus == '국제' else _SIN
    seen, out = set(), []
    for c, sec in src.items():
        k = (sec['tm'], sec.get('pm', sec['tm']))
        if k in seen:
            continue
        seen.add(k)
        out.append(dict(code=sec['code'], tm=sec['tm'], pm=sec.get('pm', sec['tm'])))
    out.sort(key=lambda f: bin(f['tm']).count('1'))     # lightest first
    _FP[campus] = out[:n]
    return _FP[campus]


# ---------------------------------------------------------------------------
# THE SCORER — one function, the same `fast_score` Fall 2026 uses
# ---------------------------------------------------------------------------
def best_week(pinned_sections, n_filler, campus, cap=60000):
    """Best achievable week given PINNED sections plus n_filler free choices.

    Uses the monotonicity prune proved in `_crowd_curve.py`: fast_score never improves as
    the occupied mask grows, so a partial timetable already below the incumbent cannot win.
    """
    tm = pm = 0
    for s in pinned_sections:
        if tm & s['tm']:
            return None          # the pinned set itself conflicts
        tm |= s['tm']; pm |= s['pm']
    pool = [f for f in filler_pool(campus) if not (tm & f['tm'])]
    box = [-1e9]
    budget = [cap]

    def rec(i, k, t, p):
        if budget[0] <= 0:
            return
        budget[0] -= 1
        sc, _ = fast_score(t, p)
        if sc <= box[0]:
            return
        if k == 0:
            box[0] = max(box[0], sc)
            return
        for j in range(i, len(pool)):
            f = pool[j]
            if t & f['tm']:
                continue
            rec(j + 1, k - 1, t | f['tm'], p | f['pm'])

    rec(0, n_filler, tm, pm)
    return box[0] if box[0] > -1e9 else None


def semester_week(item_codes, n_filler, term, campus):
    """Distribution of the best achievable week over the choices of the pinned courses.

    item_codes: list of course codes that MUST be in this semester.
    Returns dict with min/median/max and the provenance of each pinned course.
    """
    pools, prov = [], {}
    for code in item_codes:
        secs, src = sections_for(code, term, campus)
        prov[code] = f"{src} ({len(secs)} section(s))"
        if not secs:
            continue
        pools.append(secs)
    vals = []
    for combo in itertools.product(*pools) if pools else [()]:
        v = best_week(list(combo), n_filler, campus)
        if v is not None:
            vals.append(v)
    if not vals:
        return None
    return dict(min=min(vals), median=statistics.median(vals), max=max(vals),
                n=len(vals), provenance=prov)


if __name__ == '__main__':
    print("=" * 78)
    print("THE FIX, DEMONSTRATED ON THE CASE THAT EXPOSED THE PROBLEM")
    print("=" * 78)
    print("\nThe 국제 Spring that receives QRM1001 if it is deferred (plus QRM3003), 4 filler:")
    r = semester_week(['QRM1001', 'QRM3003'], 4, 'S', '국제')
    if r:
        for k, v in r['provenance'].items():
            print(f"    {k}: {v}")
        print(f"    -> week  min {r['min']:.2f}   median {r['median']:.2f}   "
              f"max {r['max']:.2f}   over {r['n']} pinned combinations")
    print("\nThe same semester if QRM1001 is taken NOW instead (only QRM3003 pinned):")
    r2 = semester_week(['QRM3003'], 5, 'S', '국제')
    if r2:
        for k, v in r2['provenance'].items():
            print(f"    {k}: {v}")
        print(f"    -> week  min {r2['min']:.2f}   median {r2['median']:.2f}   "
              f"max {r2['max']:.2f}   over {r2['n']} pinned combinations")
    if r and r2:
        print(f"\n  ⭐ measured cost of DEFERRING QRM1001 into that semester: "
              f"{r['median'] - r2['median']:+.2f} (median)")
