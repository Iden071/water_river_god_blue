# -*- coding: utf-8 -*-
"""
prof_compare.py — the two versions Iden asked for.

  "For other profs, just in case we have a better option, give two versions of keeping them
   at 0 (or the default), and then keeping them at the max score so we can visually see what
   changes."

    A.  PROF_UNRATED = 0.0   unrated professors add nothing
    B.  PROF_UNRATED = 1.0   every unrated professor is as good as the best possible

Both are FULL RE-SEARCHES, not rescorings — a section that only wins once its professor is
credited need not appear in version A's top 50 at all. (`sweep_difficulty.py` made exactly
that mistake and is retired for it.)

HOW TO READ THE OUTPUT
  · If A and B give the same timetable, no unrated professor can change the decision and the
    hand-rating work is DONE — whatever you would have written in the sheet, it does not
    matter.
  · If they differ, the professors listed in the diff are precisely the ones worth rating
    next. Everything not named there is irrelevant regardless of how you would rate it.

This is a TARGETING tool. Version B is not a scenario anyone believes; it is the upper bound
on how much unrated professors could possibly be worth.

RUN:  python prof_compare.py
"""
import os, io, json, time, contextlib, collections

os.environ.setdefault('MAX_FREE', '2')

import prof as PROF
import research_v3 as RV
import fallback as FB

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

_POOLS = None


def pools():
    """Built once — nothing in rank3.build() depends on the professor term."""
    global _POOLS
    if _POOLS is None:
        import rank2 as _R2, rank3 as _rank3, fm_fix as _fm, eligibility as _el
        with contextlib.redirect_stdout(io.StringIO()):
            Pp, sig, sigs, SIGCODES, code = _rank3.build()
            _fm.apply(Pp, verbose=False)
            _el.apply(Pp, verbose=False)
        ZERO = {c[:7] for c, s in {x['c']: x for v in Pp.values() for x in v}.items()
                if s['fm'] == 0 and s['tm']}
        for pool in Pp.values():
            pool[:] = [s for s in pool if s['code'] not in ZERO]
        LANGP = [s for s in Pp['OPEN'] if code(s) in _R2.LANG]
        ELEC = [s for s in Pp['OPEN'] if code(s) not in _R2.LANG]
        REQ = {'MR': Pp['MR'], 'WCiv': Pp['WCiv'], 'LHP': Pp['LHP'],
               'SciRD': Pp['SciRD'], 'Lang': LANGP}
        _POOLS = (Pp, REQ, ELEC, code)
    return _POOLS


def run(unrated, topn=50):
    PROF.UNRATED = unrated
    PROF.reset()
    RV.MAX_FREE = 2
    RV.TOPN = 3000
    RV.STATE = P('_profcmp_tmp')
    os.makedirs(RV.STATE, exist_ok=True)
    Pp, REQ, ELEC, code = pools()
    rows = []
    for b in FB.B:
        fp = os.path.join(RV.STATE, f'part_{b}.json')
        open(fp, 'w').close()
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                RV.run_branch(b, Pp, REQ, ELEC, code)
            except Exception:
                continue
        if not os.path.getsize(fp):
            continue
        for r in json.load(open(fp, encoding='utf-8'))['rows']:
            v = FB.total(r, b)
            if v is not None:
                rows.append((v, b, r))
        open(fp, 'w').close()
    rows.sort(key=lambda t: -t[0])
    return rows[:topn]


def secs(r):
    return ((r.get('requirements') or []) + (r.get('electives') or [])
            + ([r['chapel']] if r.get('chapel', '-') != '-' else []))


def main():
    t0 = time.time()
    rated = PROF.ratings()
    print(f"PROF_W = {PROF.PROF_W}   professors rated so far: {len(rated)}")
    if not rated:
        print("  (prof_ratings.csv is empty — so this is purely the UNRATED bracket)")
    print()

    A = run(0.0)
    B = run(1.0)
    PROF.UNRATED = 0.0
    PROF.reset()

    for nm, R in (('A  unrated = 0   (neutral)', A), ('B  unrated = +1  (max)', B)):
        v, b, r = R[0]
        print(f"{nm}\n   {v:8.3f}  defer {b}")
        for s in secs(r):
            print(f"     {s:16s} {PROF.prof_of(s)}")
        print()

    sa, sb = set(secs(A[0][2])), set(secs(B[0][2]))
    if sa == sb and A[0][1] == B[0][1]:
        print("=" * 74)
        print("✅ IDENTICAL TOP TIMETABLE UNDER BOTH.")
        print("   No unrated professor can change the #1 choice, at PROF_W =",
              PROF.PROF_W, "— so rating the rest cannot move it either.")
    else:
        print("=" * 74)
        print("⚠️ THE TOP TIMETABLE CHANGES. Sections that appear only when unrated")
        print("   professors are credited at maximum:")
        for s in sorted(sb - sa):
            print(f"     + {s:16s} {PROF.prof_of(s)}")
        for s in sorted(sa - sb):
            print(f"     − {s:16s} {PROF.prof_of(s)}")
        who = sorted({PROF.prof_of(s) for s in (sb - sa)} - set(rated))
        print(f"\n   ⭐ RATE THESE NEXT ({len(who)}): {', '.join(who)}")

    pa = collections.Counter(PROF.prof_of(s) for v, b, r in A for s in secs(r))
    pb = collections.Counter(PROF.prof_of(s) for v, b, r in B for s in secs(r))
    moved = sorted(((pb[k] - pa[k], k) for k in set(pa) | set(pb)),
                   key=lambda t: -abs(t[0]))[:10]
    print(f"\n   biggest movers across the top 50 (appearances B − A):")
    for d, k in moved:
        if d:
            print(f"     {d:+4d}  {k}   {'(rated)' if k in rated else ''}")

    json.dump({'A_unrated0': [dict(total=v, defer=b, sections=secs(r)) for v, b, r in A[:10]],
               'B_unrated1': [dict(total=v, defer=b, sections=secs(r)) for v, b, r in B[:10]],
               'PROF_W': PROF.PROF_W, 'rated': rated},
              open(P('prof_compare.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f"\n[{time.time()-t0:.0f}s] wrote prof_compare.json")


if __name__ == '__main__':
    main()
