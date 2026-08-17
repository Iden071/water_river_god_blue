# -*- coding: utf-8 -*-
"""
partition_verdict.py — Stage 4. Re-derive the Fall 2026 verdict on the PARTITION objective.

    total(branch) = max over Fall timetables in that branch of
                      [ Fall week score  +  best Σ best_week over semesters 3–8
                                            of whatever units that timetable leaves ]

There is no `K` anywhere in this. The old model asked "what does deferring this one course
cost a hypothetical semester"; this asks "given this Fall, how good can the whole remaining
degree be". That is R285's objective, and the two differ whenever a penalty is relocated
rather than avoided — which for a required course is always.

⚠️ JOINT, NOT SEQUENTIAL. The Fall timetable and the partition are chosen together: which
electives Fall burns changes which units remain, which changes the best partition. So each
candidate Fall row is scored against its OWN remainder, not against a fixed one.

RUN:  python partition_verdict.py
"""
import json, os, sys, glob, collections

import plan_model as PM
import partition as PT
import partition_solve as PS

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

# the five requirement items a Fall branch may defer, and the ledger key each maps to
REQ_ITEMS = {'MR': 'QRM1001', 'WCiv': 'WCiv', 'LHP': 'LHP', 'SciRD': 'SciRD', 'Lang': 'Lang'}
# ⛔ R295. This was `sorted(rs, key=-score)[:40]` — rank by Fall week, then maximise
# `Fall + future`. The FOURTH instance of truncate-then-maximise (R260 rows[:60],
# R269 TOPN=3000, R276 rows[:400]). Caught by the renderer, which scans everything and found
# 352.569 against the verdict's 347.467 — the true argmax has a Fall week of 19.890, far
# below the top 40. With the future values disk-cached this is now cheap, so: every row.
TOPN = int(os.environ.get('VERDICT_TOPN', 0)) or None
# ⛔ RED-TEAM F2. This module never set SINCHON_BONUS, so it ran at partition_solve's 0.0
# default while reading a cache the renderer had filled at 30.0 — and reported the result as
# its own. Same default as the other two consumers now, and the bonus is in the cache key.
PS.SINCHON_BONUS = float(os.environ.get('SINCHON_BONUS', 30.0))


def full_ledger():
    return {i['key']: i['count'] for i in PM.ITEMS if i.get('codes')}


def remainder(branch, row):
    """What is still owed after this Fall timetable, for this deferral branch."""
    left = full_ledger()
    # Fall takes every requirement except the deferred one
    for b, key in REQ_ITEMS.items():
        if b == branch:
            continue
        if key in left:
            left[key] -= 1
    if 'Chapel' in left and row.get('chapel', '-') != '-':
        left['Chapel'] -= 1
    for it in row.get('items') or []:          # the ledger units the electives discharge
        if it in left:
            left[it] -= 1
    return {k: v for k, v in left.items() if v > 0}


def main():
    d, val = PS.table()
    rows = {}
    for fp in glob.glob(P('_v3_parts_f2/part_*.json')):
        blob = json.load(open(fp, encoding='utf-8'))
        rows[blob['branch']] = blob['rows']

    print(f"scoring the top {TOPN} Fall rows per branch against their OWN remainder\n")
    print(f"  {'branch':7s} {'Fall week':>10s} {'Σ future':>10s} {'TOTAL':>10s}   remaining after Fall")
    out = []
    # reuse the renderer's disk cache — the DP is the expensive part and it is already solved
    seen = {}
    fp = P('_future_cache.json')
    if os.path.exists(fp) and os.path.getsize(fp):
        try:
            for k, v in json.load(open(fp, encoding='utf-8')).items():
                seen[k] = (v, ())
        except Exception:
            pass
    print(f"  {len(seen)} remainders pre-solved from cache")
    for b in ('-', 'MR', 'WCiv', 'LHP', 'SciRD', 'Lang'):
        rs = rows.get(b) or []
        best = None
        for r in (sorted(rs, key=lambda x: -x['score'])[:TOPN] if TOPN else rs):
            rem = remainder(b, r)
            key = PS.cache_key(rem, d)
            if key not in seen:
                seen[key] = PS.solve(rem, val, d['base'], verbose=False)
            fut, plan = seen[key]
            if fut < -1e17:
                continue
            t = r['score'] + fut
            if best is None or t > best[0]:
                best = (t, r, fut, rem, plan)
        if best is None:
            print(f"  {b:7s} {'—':>10s} {'—':>10s} {'NO FEASIBLE PARTITION':>10s}")
            continue
        t, r, fut, rem, plan = best
        out.append((t, b, r, fut, rem, plan))
        print(f"  {b:7s} {r['score']:10.3f} {fut:10.3f} {t:10.3f}   {rem}")

    out.sort(reverse=True)
    print()
    if len(out) >= 2:
        print(f"⭐ PARTITION VERDICT: defer {out[0][1]}  ({out[0][0]:.3f}), "
              f"2nd {out[1][1]} {out[1][0]:.3f}, margin {out[0][0]-out[1][0]:.3f}")
    t, b, r, fut, rem, plan = out[0]
    if not plan:
        _t, plan = PS.solve(rem, val, d['base'], verbose=False)
    print(f"\nFall 2026 under the winner:")
    secs = r['requirements'] + r['electives'] + ([r['chapel']] if r['chapel'] != '-' else [])
    print('   ' + ' '.join(secs))
    print(f"\nand the plan for the rest (Σ {fut:.3f}):")
    for sem, camp, sea, combo, v, pen in plan:
        lab = '+'.join(combo) if combo else '(free electives only)'
        p = f'  year-pen {pen:+.2f}' if pen else ''
        print(f"   sem {sem}  {camp} {sea}  {lab:32s} {v:8.3f}{p}")

    json.dump({'verdict': [(round(x[0], 3), x[1]) for x in out]},
              open(P('partition_verdict.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
