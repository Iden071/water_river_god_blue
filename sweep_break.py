# -*- coding: utf-8 -*-
"""
sweep_break.py — does a 휴학 for 병역, or a 계절학기, change the 8/25 decision?

Iden confirmed 2026-08-09 that he expects a leave for military service at some point, and
wants 계절학기 modelled as an escape valve. Neither had ever been mentioned in this project.

The point of this file is NOT to guess when the leave happens. It is to check whether the
Fall 2026 answer is INVARIANT to it. If it is, the unknown can be parked with evidence
rather than a shrug. If it is not, the break point becomes a real input.

Method: hold the candidate set fixed (the top of FINAL_ranked4.csv) and rescore it under
every configuration, since only ΔV changes — the week, the year penalties and the chapel
term are all properties of Fall 2026 and cannot move.
"""
import csv, json, os, itertools, time
import rank3, rank2 as R2, rank4
from rank2 import fast_score, eff_year, YEAR_PEN
import continuation

HERE = os.path.dirname(os.path.abspath(__file__))
P = rank3.build()[0]
byc = {s['c']: s for v in P.values() for s in v}
code = lambda s: s['code']
ITEM = json.load(open(os.path.join(HERE, 'elective_items.json'), encoding='utf-8'))
rows = list(csv.DictReader(open(os.path.join(HERE, 'FINAL_ranked4.csv'),
                                encoding='utf-8-sig')))
N = 800                      # deep enough to catch a reorder at the top
from defer_value2 import remainder_after, ALL_REQS


def fall_parts(r):
    """week + year penalty + chapel — everything that CANNOT depend on the future."""
    reqs, els = r['requirements'].split(), r['electives'].split()
    tm = pm = 0
    for c in reqs + els:
        s = byc[c]; tm |= s['tm']; pm |= s['pm']
    ch = r['chapel']; has = bool(ch and ch != '-')
    if has:
        s = byc[ch]; tm |= s['tm']; pm |= s['pm']
    week, _ = fast_score(tm, pm)
    yr = sum(YEAR_PEN(eff_year(byc[c], code)) for c in reqs + els)
    chap = rank4.CHAPEL_BONUS if has else rank4.CHAPEL_DEFER
    df = frozenset() if r['deferred'] == '-' else frozenset(r['deferred'].split('+'))
    items = tuple(sorted(ITEM.get(c, 'FREE') for c in els))
    return week + yr + chap, df, items


PARTS = [fall_parts(r) for r in rows[:N]]
STATES = sorted({(df, it) for _, df, it in PARTS})
print(f"{len(PARTS)} candidates, {len(STATES)} distinct remainder states\n", flush=True)


def rescore(**kw):
    cache = {}
    for df, it in STATES:
        taken = [x for x in ALL_REQS if x not in df]
        rem = remainder_after(taken, [], chapel=True)
        for k in it:
            rem[k] = max(0, rem[k] - 1)
        cache[(df, it)] = continuation.solve(rem, **kw)[0]
    ref = cache.get((frozenset(), ('FREE', 'FREE')))
    if ref is None:
        rem = remainder_after(ALL_REQS, [], chapel=True)
        for k in ('FREE', 'FREE'):
            rem[k] = max(0, rem[k] - 1)
        ref = continuation.solve(rem, **kw)[0]
    out = []
    for (base, df, it), r in zip(PARTS, rows[:N]):
        out.append((base + cache[(df, it)] - ref, r))
    out.sort(key=lambda x: -x[0])
    return out


def label(r):
    return (f"defer={r['deferred']:6s} | {' '.join(c[:7] for c in r['requirements'].split())}"
            f" | {' '.join(c[:7] for c in r['electives'].split())}")


if __name__ == '__main__':
    t0 = time.time()
    configs = [("no break, no summer", dict())]
    for k in (2, 3, 4, 5, 6):
        for rt in ('S', 'F'):
            configs.append((f"휴학 after sem {k}, return in {'Spring' if rt=='S' else 'Fall'}",
                            dict(break_after=k, return_term=rt)))
    configs.append(("계절학기 available (no break)", dict(summers=True)))
    configs.append(("계절학기 + 휴학 after sem 4, return Fall",
                    dict(break_after=4, return_term='F', summers=True)))

    baseline_top = None
    print(f"{'configuration':44s} {'#1 score':>9}  {'#1 is':>7}  top-5 identical?")
    print("-" * 92)
    for name, kw in configs:
        res = rescore(**kw)
        top5 = [label(r) for _, r in res[:5]]
        if baseline_top is None:
            baseline_top = top5
        same = "yes" if top5 == baseline_top else "❌ NO"
        same1 = "same" if top5[0] == baseline_top[0] else "❌ CHANGED"
        print(f"{name:44s} {res[0][0]:9.3f}  {same1:>7}  {same}    [{time.time()-t0:.0f}s]",
              flush=True)
    print()
    print("BASELINE #1:", baseline_top[0])
