# -*- coding: utf-8 -*-
"""
continuation_sim.py — V computed from REAL SECTIONS, by local search. Replaces the counting
proxy in `continuation.solve()`.

WHY THE OPTIMISER HAD TO CHANGE TOO
-----------------------------------
`continuation.solve()` uses a Hungarian assignment, which requires the cost to be SEPARABLE:
cost(item, semester) must not depend on what else is in that semester. Scoring a semester
from real sections breaks that immediately — a course's damage depends on which other
courses share its days. So the assignment problem stops being an assignment problem.

This file keeps the same feasibility rules and swaps the optimiser for a **local search**
seeded from the old solution: start where the Hungarian left off, then move and swap items
between semesters, keeping any change that improves the simulated value. Local search cannot
prove optimality, which is stated in the output rather than papered over — but it optimises
the RIGHT objective, and R208 showed the old optimiser was solving the wrong one exactly.

WHAT IS SCORED
--------------
    plan value = Σ_sem  semester_week(real sections, that term, that campus)
               + Σ_item year_gap_pen(semester year, chart year)
               + SINCHON_SEMESTER_VALUE × (number of 신촌 semesters)

with the SAME `fast_score` Fall 2026 uses (R208's seam closed), the SAME feasibility rules as
`continuation.solve()`, and the R210 fixed-hour mask throughout.
"""
import os, json, itertools, statistics, collections, random

import continuation as C
import risk as RISK
import semester_sim as SIM
from plan_model import ITEMS, build_semesters, MIN_INTL_SEMESTERS
from rank2 import year_gap_pen

HERE = os.path.dirname(os.path.abspath(__file__))
BY_KEY = {i['key']: i for i in ITEMS}

# Items that resolve to real course codes get PINNED at real times.
# DM and FREE have no codes — they behave as filler, which is correct: they are the items
# Iden can place anywhere, and R206 showed the model has no opinion about where they go.
FILLER_KEYS = {'DM', 'FREE'}

_WEEK = {}


_EMPTY = {}


def empty_week(campus):
    """The week with nothing in it — the zero point for damage."""
    if campus not in _EMPTY:
        _EMPTY[campus] = SIM.best_week([], 0, campus)
    return _EMPTY[campus]


def semester_week(item_keys, term, campus, quantile=0.5):
    """Simulated week DAMAGE for one semester (<= 0). Memoised.

    ⛔ TWO BUGS THE FIRST VERSION HAD, both visible in its own output:

    1. **A course with no section data vanished.** Items like QRM3003 and MR5 have course
       codes but no observed times anywhere, so they landed in `pinned`, contributed no
       sections, and then occupied NO SLOT and cost NOTHING. A 국제 Spring holding four
       requirements scored 114.58 — the number for an almost-empty semester. Fixed: an item
       with no resolvable section is still a COURSE. It becomes filler — it takes a slot, we
       simply do not know its hours.

    2. **Empty semesters were REWARDED.** Scoring the raw week means a semester with nothing
       in it earns the maximum (163.07), so the search happily emptied semesters — B's plan
       had a completely empty Spring 2029. Nothing in the model forces a minimum load.
       Fixed by scoring DAMAGE relative to the empty week, so an empty semester is worth
       exactly 0 and every course costs. This also restores comparability with the old V.
    """
    pinned, n_filler = [], 0
    for k in item_keys:
        if k == 'Chapel':
            continue                      # cap-exempt, 0.5cr, schedule-neutral (R36)
        codes = BY_KEY[k].get('codes') or []
        secs = []
        if k not in FILLER_KEYS and codes:
            secs, _src = SIM.sections_for(codes[0], term, campus)
        if secs:
            pinned.append(codes[0])
        else:
            n_filler += 1                 # a course we cannot time still occupies a slot
    pinned.sort()
    key = (tuple(pinned), n_filler, term, campus, quantile)
    if key in _WEEK:
        return _WEEK[key]
    # ⛔ R215. THE POISONED-STATE BUG. `SIM.semester_week` returns None when EVERY choice of
    # the pinned sections conflicts, and this used to score that -1e6 — poisoning the state.
    # 145 of the 417 table entries came back poisoned, a THIRD of the continuation.
    # The inference was wrong. Two courses colliding is a fact about the FALL 2026 catalogue
    # standing in for a future term (semester_sim flags exactly this as 'stand-in ⚠️'), not a
    # fact about 2028. Treating it as impossible-forever both invents a hard constraint the
    # data cannot support and hands the search a -1e6 cliff to fall off.
    # Correct handling is the rule already in this function: a course we cannot TIME is still
    # a course. Demote pinned courses to filler until the semester resolves.
    p, r, demoted = list(pinned), None, 0
    while True:
        r = SIM.semester_week(p, n_filler + demoted, term, campus)
        if r is not None or not p:
            break
        p.pop(); demoted += 1                 # deterministic: pinned is sorted
    if r is None:
        val = -1e6                            # genuinely nothing fits, even as pure filler
    else:
        raw = r['median'] if quantile == 0.5 else r['min']
        val = raw - empty_week(campus)    # DAMAGE: empty semester == 0
    _WEEK[key] = val
    return val


def feasible(assign, sems, pattern):
    """The SAME rules as continuation.solve(). Kept in one place so they cannot drift."""
    if not any(c == '국제' and s['term'] == 'S' and s['kind'] == 'sem'
               for c, s in zip(pattern, sems)):
        return False                                            # QRM3003 needs a 국제 Spring
    me_sinchon = 0
    for si, keys in assign.items():
        s, camp = sems[si], pattern[si]
        if len(keys) > s['slots']:
            return False
        for k in keys:
            it = BY_KEY[k]
            if it['campus'] != 'any' and it['campus'] != camp:
                return False
            if s['kind'] == 'summer':
                return False                                    # summers off for this build
            if s['term'] not in it['terms']:
                return False
            if k == 'ME' and camp == '신촌':
                me_sinchon += 1
        if sum(1 for k in keys if k == 'Chapel') > 1:
            return False
        bids = C.semester_bids([BY_KEY[k] for k in keys])
        if not RISK.budget_check(bids)[0]:
            return False
    return me_sinchon <= C.KOREAN_ME_COURSE_CAP


def value(assign, sems, pattern, quantile=0.5):
    tot = 0.0
    for si, keys in assign.items():
        s, camp = sems[si], pattern[si]
        tot += semester_week(keys, s['term'], camp, quantile)
        for k in keys:
            tot += year_gap_pen(s['year'], BY_KEY[k]['chart_year'])
    tot += C.SINCHON_SEMESTER_VALUE * sum(
        1 for c, s in zip(pattern, sems) if c == '신촌' and s['kind'] == 'sem')
    return tot


def seed_from_hungarian(remaining):
    """Start where the old optimiser stopped — a good, feasible, legal placement."""
    v, plan = C.solve(remaining)
    if plan is None:
        return None, None, None
    sems = [s for s in plan['sems'] if s['kind'] == 'sem']
    pattern = [plan['campus'][s['label']] for s in sems]
    assign = {i: list(plan['placement'].get(s['label'], [])) for i, s in enumerate(sems)}
    return assign, sems, pattern


def _neighbours(assign):
    """Every single MOVE and SWAP, as fresh dicts. Generated from a snapshot, so the caller
    may replace `assign` freely without corrupting the iteration — the bug the first version
    had: it mutated `assign` mid-loop and then tried to .remove() from a stale list."""
    idx = list(assign)
    for a in idx:
        for k in list(assign[a]):
            for b in idx:
                if b == a:
                    continue
                t = {i: list(v) for i, v in assign.items()}
                t[a].remove(k); t[b].append(k)
                yield t
    for a, b in itertools.combinations(idx, 2):
        for ka in list(assign[a]):
            for kb in list(assign[b]):
                if ka == kb:
                    continue
                t = {i: list(v) for i, v in assign.items()}
                t[a].remove(ka); t[b].remove(kb)
                t[a].append(kb); t[b].append(ka)
                yield t


def minimal_intl_patterns(sems):
    """Campus patterns using the FEWEST 국제 semesters.

    ⛔ THE COMPARISON BUG. The first version inherited the campus pattern from the Hungarian
    seed and never changed it — the local search moves items only. So two candidates were
    compared under DIFFERENT patterns (A got 2 국제, B got 3), and at
    SINCHON_SEMESTER_VALUE = 96 per semester that difference alone dwarfed everything the
    simulation was measuring. Same class as the filler-pool bug: an unfair baseline.

    With the 신촌 bonus at 96, the optimum always takes the minimum 국제 count, and R144 fixes
    that minimum at 2 (Fall 2026 + one 국제 Spring for QRM3003). So exactly ONE of sems 3-8 is
    국제, and it must be a Spring: three candidate patterns, all enumerated, none assumed.
    """
    out = []
    for i, s in enumerate(sems):
        if s['term'] != 'S' or s['kind'] != 'sem':
            continue
        out.append(['국제' if j == i else '신촌' for j in range(len(sems))])
    return out


def local_search(remaining, quantile=0.5, rounds=8, pattern=None):
    """Steepest-ascent from the Hungarian solution. Returns None if no feasible start."""
    assign, sems, seed_pattern = seed_from_hungarian(remaining)
    if assign is None:
        return None
    if pattern is not None:
        pattern = list(pattern)
        # re-seed: park every item in the first semester that can legally hold it
        items = [k for keys in assign.values() for k in keys]
        assign = {i: [] for i in range(len(sems))}
        for k in sorted(items, key=lambda k: (BY_KEY[k]['campus'] == 'any', k)):
            for i, s in enumerate(sems):
                if len(assign[i]) >= s['slots']:
                    continue
                it = BY_KEY[k]
                if it['campus'] != 'any' and it['campus'] != pattern[i]:
                    continue
                if s['term'] not in it['terms']:
                    continue
                assign[i].append(k)
                if feasible(assign, sems, pattern):
                    break
                assign[i].pop()
            else:
                return None                      # cannot place this item at all
    else:
        pattern = seed_pattern
    best = value(assign, sems, pattern, quantile)
    it, evals = 0, 0
    while it < rounds:
        it += 1
        champion, champ_val = None, best
        for t in _neighbours(assign):
            if not feasible(t, sems, pattern):
                continue
            evals += 1
            v = value(t, sems, pattern, quantile)
            if v > champ_val + 1e-9:
                champion, champ_val = t, v
        if champion is None:
            break                      # local optimum
        assign, best = champion, champ_val
    return dict(value=best, assign=assign, sems=sems, pattern=pattern,
                rounds=it, evals=evals)


def best_plan(remaining, quantile=0.5):
    """Search item placement over EVERY minimal-국제 campus pattern, and take the best.
    Both candidates are then measured on the same footing."""
    seed = seed_from_hungarian(remaining)
    if seed[0] is None:
        return None
    sems = seed[1]
    best = None
    for pat in minimal_intl_patterns(sems):
        r = local_search(remaining, quantile=quantile, pattern=pat)
        if r and (best is None or r['value'] > best['value']):
            best = r
    return best


def describe(res):
    if not res:
        return "INFEASIBLE"
    TERM = {'S': 'Spring', 'F': 'Fall  '}
    out = [f"simulated V = {res['value']:.3f}   (local search, {res['rounds']} rounds)"]
    n_intl = 1 + sum(1 for c in res['pattern'] if c == '국제')
    out.append(f"  {n_intl} 국제 / {7 - n_intl} 신촌")
    for i, s in enumerate(res['sems']):
        keys = res['assign'][i]
        w = semester_week(keys, s['term'], res['pattern'][i])
        out.append(f"  {s['label']:8s} {TERM[s['term']]} yr{s['year']} {res['pattern'][i]}"
                   f"  week {w:8.2f}   " + " ".join(sorted(keys)))
    return "\n".join(out)


if __name__ == '__main__':
    from defer_value2 import remainder_after
    import time
    print("=" * 78)
    print("V RECOMPUTED FROM REAL SECTIONS — the two live candidates")
    print("=" * 78)
    cases = {
        'A  defer Intro to QRM (live #1)': (['WCiv', 'LHP', 'SciRD', 'Lang'], ['ME', 'ME']),
        'B  defer Language': (['MR', 'WCiv', 'LHP', 'SciRD'], ['ECO1101', 'ME']),
    }
    res = {}
    for name, (taken, els) in cases.items():
        rem = remainder_after(taken, [], chapel=True)
        for k in els:
            rem[k] = max(0, rem[k] - 1)
        t0 = time.time()
        r = best_plan(rem)
        res[name] = r
        print(f"\n### {name}    [{time.time()-t0:.0f}s]")
        print(describe(r))
    a, b = res['A  defer Intro to QRM (live #1)'], res['B  defer Language']
    if a and b:
        print("\n" + "=" * 78)
        print(f"  simulated V:   A {a['value']:9.3f}    B {b['value']:9.3f}"
              f"    B - A = {b['value'] - a['value']:+.3f}")
        print("  ⚠️ local search — a lower bound on each, not a proof of optimality.")
