# -*- coding: utf-8 -*-
"""
b1_receiving.py — B-1, FINALLY: what does a deferred requirement cost the semester that
                  RECEIVES it, measured over real sections at real hours?

WHY
---
`DECISIONS_NEEDED.md` B-1 has been the stated blocker since 2026-08-07: deferring a
requirement GAINS schedule quality in Fall 2026 (measured) and COSTS two things — the year
gap (computed, live) and the schedule quality lost in the receiving semester (**never
computed**). R226 then measured that the crowding proxy standing in for that second cost is
the ONLY term in V that moves the answer, while being the worst-evidenced thing in the
project. So it gets measured.

WHAT THIS COMPUTES
------------------
For each of the five deferrable requirements:
  1. ask `continuation.solve` where the deferred item actually lands, and what that
     semester must already carry;
  2. rebuild that semester from REAL SECTIONS (per-term evidence where it exists, Fall 2026
     catalogue as a flagged stand-in otherwise);
  3. score its best achievable week WITH the deferred course pinned, and WITHOUT it (one
     extra free slot), using `fast_score` — the same scorer Fall 2026 uses;
  4. report the damage as an INTERVAL over the choice of pinned sections, never a point.

K(u) = week_without(u) - week_with(u)  >= 0, in the same currency as the Fall 2026 week.

⭐ THE SEARCH BOUND IS REPLACED, AND THE REPLACEMENT IS PROVED
`semester_sim.best_week` prunes on `fast_score`, which R217 showed is not monotone — so the
shipped search can discard the true optimum (GAPS: "not fixed"). The sound bound is
`week_value`:

    fast_score(final) = week_value(final) + Σ day_pen(final)
                     <= week_value(final)        because day_pen <= 0
                     <= week_value(partial)      because week_value is monotone decreasing

  · day_pen <= 0 : verified EXHAUSTIVELY over all 65,536 day masks (0 exceptions).
  · week_value monotone : every component is non-increasing in occupancy — adding hours can
    only shorten the presence-free weekend run, remove a genuinely-empty weekday, or void
    the Friday bonus. Measured 0 violations / 20,000 random pairs, and the argument is a
    proof, not a sample.

So `week_value(partial)` is a valid upper bound on any completion and `fast_score(partial)`
is not. This file uses the former. Node budgets are reported; a truncated search yields a
LOWER bound on the week, which makes K an UPPER bound on damage — the arm that argues
against deferring (R190).
"""
import json, os, sys, itertools, statistics, collections, time

import rank2 as R2, difficulty as DIFF
R2.LANG = set(DIFF.LANG_ALL)
import rank3
from rank2 import fast_score, week_value
import semester_sim as SS
from continuation import solve
from defer_value2 import remainder_after, ALL_REQS
from plan_model import ITEMS

HERE = os.path.dirname(os.path.abspath(__file__))
by_key = {i['key']: i for i in ITEMS}

# requirement name (as the ranker uses it) -> ledger key it consumes
REQ_ITEM = {'MR': 'QRM1001', 'WCiv': 'WCiv', 'LHP': 'LHP',
            'SciRD': 'SciRD', 'Lang': 'Lang'}


def sound_best_week(pinned, n_filler, campus, cap=400000):
    """Best achievable week: pinned sections + n_filler free choices from the real pool.

    Branch and bound with the PROVED bound above. Returns (best, nodes, truncated)."""
    tm = pm = 0
    for s in pinned:
        if tm & s['tm']:
            return None, 0, False
        tm |= s['tm']; pm |= s['pm']
    pool = [f for f in SS.filler_pool(campus) if not (tm & f['tm'])]
    box = [-1e9]; nodes = [0]; trunc = [False]

    def rec(i, k, t, p):
        if nodes[0] >= cap:
            trunc[0] = True; return
        nodes[0] += 1
        ub, _ = week_value(p, t)              # ⭐ sound upper bound on any completion
        if ub <= box[0]:
            return
        if k == 0:
            sc, _ = fast_score(t, p)
            if sc > box[0]:
                box[0] = sc
            return
        for j in range(i, len(pool)):
            f = pool[j]
            if t & f['tm']:
                continue
            rec(j + 1, k - 1, t | f['tm'], p | f['pm'])

    rec(0, n_filler, tm, pm)
    return (box[0] if box[0] > -1e9 else None), nodes[0], trunc[0]


def receiving_semester(req):
    """Where does the deferred requirement land, and what shares that semester?"""
    d = frozenset([req])
    taken = [x for x in ALL_REQS if x not in d]
    rem = remainder_after(taken, [], chapel=True)
    for k in ('ME', 'ME'):                       # the elective pair the live #1 holds
        rem[k] = max(0, rem[k] - 1)
    v, plan = solve(rem)
    if plan is None:
        return None
    key = REQ_ITEM[req]
    sems = {s['label']: s for s in plan['sems']}
    for lab, keys in plan['placement'].items():
        if key in keys:
            s = sems[lab]
            return dict(label=lab, term=s['term'], year=s['year'],
                        campus=plan['campus'][lab], keys=list(keys))
    return None


def codes_for(item_key):
    """Real course codes a ledger item can be satisfied by. [] = abstract (filler)."""
    return list(by_key[item_key].get('codes') or [])


def measure(req, verbose=True):
    loc = receiving_semester(req)
    if loc is None:
        return None
    key = REQ_ITEM[req]
    others = [k for k in loc['keys'] if k != key]
    # split co-tenants into REAL (pinned, have codes) and ABSTRACT (become filler slots)
    pinned_keys = [k for k in others if codes_for(k)]
    n_filler = len(others) - len(pinned_keys)

    def pools_for(keys):
        pools, prov = [], {}
        for k in keys:
            best = None
            for c in codes_for(k):
                secs, src = SS.sections_for(c, loc['term'], loc['campus'])
                if secs:
                    best = (secs, f"{c}: {src} ({len(secs)} section(s))")
                    break
            if best:
                pools.append(best[0]); prov[k] = best[1]
            else:
                prov[k] = 'NO SECTION DATA -> treated as a free slot'
        return pools, prov

    base_pools, prov = pools_for(pinned_keys)
    dfr_pools, dprov = pools_for([key])
    extra_filler = n_filler + (0 if dfr_pools else 1)
    prov.update(dprov)

    def spread(pools, nfill):
        vals, tr = [], False
        combos = list(itertools.product(*pools)) if pools else [()]
        for combo in combos:
            v, nodes, t = sound_best_week(list(combo), nfill, loc['campus'])
            if v is not None:
                vals.append(v)
            tr = tr or t
        return vals, tr, len(combos)

    with_v, t1, n1 = spread(base_pools + dfr_pools, extra_filler)
    without_v, t2, n2 = spread(base_pools, extra_filler + (1 if dfr_pools else 0))
    if not with_v or not without_v:
        return None
    res = dict(req=req, item=key, loc=loc, provenance=prov,
               with_median=statistics.median(with_v), with_min=min(with_v), with_max=max(with_v),
               without_median=statistics.median(without_v),
               without_min=min(without_v), without_max=max(without_v),
               n_with=n1, n_without=n2, truncated=(t1 or t2))
    res['K_median'] = res['without_median'] - res['with_median']
    res['K_lo'] = res['without_min'] - res['with_max']       # optimistic: least damage
    res['K_hi'] = res['without_max'] - res['with_min']       # pessimistic: most damage
    return res


if __name__ == '__main__':
    only = sys.argv[1:] or list(REQ_ITEM)
    out = {}
    p = os.path.join(HERE, 'b1_receiving.json')
    if os.path.exists(p) and os.path.getsize(p):
        try: out = json.load(open(p, encoding='utf-8'))
        except Exception: out = {}
    for req in only:
        t0 = time.time()
        r = measure(req)
        if r is None:
            print(f"{req}: no placement / no data"); continue
        out[req] = r
        L = r['loc']
        print(f"\n=== {req}  ({r['item']}) ===")
        print(f"  lands in {L['label']} · {'Spring' if L['term']=='S' else 'Fall'} "
              f"· yr{L['year']} · {L['campus']}   sharing with: {' '.join(sorted(k for k in L['keys'] if k!=r['item']))}")
        for k, v in r['provenance'].items():
            print(f"    {k:9s} {v}")
        print(f"  week WITH    it: min {r['with_min']:8.3f}  median {r['with_median']:8.3f}  max {r['with_max']:8.3f}   ({r['n_with']} pinned combos)")
        print(f"  week WITHOUT it: min {r['without_min']:8.3f}  median {r['without_median']:8.3f}  max {r['without_max']:8.3f}   ({r['n_without']} pinned combos)")
        print(f"  ⭐ K({req}) = {r['K_median']:.3f}   bracket [{r['K_lo']:.3f}, {r['K_hi']:.3f}]"
              f"{'   ⚠ SEARCH TRUNCATED (K is an upper bound)' if r['truncated'] else ''}")
        print(f"  {time.time()-t0:.0f}s")
        json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"\nwrote b1_receiving.json ({len(out)} of 5 requirements)")
