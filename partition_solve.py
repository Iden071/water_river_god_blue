# -*- coding: utf-8 -*-
"""
partition_solve.py — the DP over partitions.  R285's objective, solved.

    maximise   Σ_{s = 3..8}  best_week( obligations assigned to s , 6−|S| free , pool(s) )

Equivalent to minimising Σ discomfort, but stated as a maximisation so it never needs the
6-free-slot baseline — 신촌|S's OOMs at every node cap tried, and depending on it would inject
a BOUND into every 신촌 Spring entry (R289).

WHY A DP AND NOT A SEARCH
The state that matters is only *how many of each item remain*, not which semester they came
from. Counts are (Chapel 2, Seminar 2, QRM1001 1, ECO2102 1, ECO2101 1, MR5 1, QRM3003 1,
ME 5) -> 3·3·2·2·2·2·2·6 = 1,728 reachable states. Six semesters, two campus choices each, and
~117 obligation subsets per (campus, season). That is a few million transitions — trivial once
the cost table exists, which is why all the cost went into building the table.

CONSTRAINTS, all sourced
  · QRM3003 — 국제 only, Spring only, chart-year 3  =>  semester 5 or 7, campus 국제 (R144)
  · ECO2101 — 신촌 only (68 observed sections, zero at 국제)                        (R288)
  · >= 2 국제 semesters overall, semester 2 already being one                       (R144)
  · <= 3 obligations per semester (the table's MAX_PIN; 14 units / 6 semesters = 2.33)
  · year-gap: taking an item before its chart year is penalised, not forbidden (R145)

RUN:  python partition_solve.py            # solve for the current remaining ledger
      python partition_solve.py --branches # re-derive the Fall verdict on this objective
"""
import json, os, sys, itertools, collections, functools, hashlib

import plan_model as PM
import partition as PT
from rank2 import year_gap_pen, QRM_CHART_YEAR

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

# semester -> (season, academic year). Springs 3/5/7, Falls 4/6/8 (R144).
REM = [(3, 'S', 2), (4, 'F', 2), (5, 'S', 3), (6, 'F', 3), (7, 'S', 4), (8, 'F', 4)]
CAMPUSES = ('국제', '신촌')
MAX_OBLIG = 3

# ⛔ R292. THE 신촌 PREFERENCE WAS DROPPED. R126: Iden calls a 신촌 semester "much much much
# more preferable", strong enough that one was said to outrank the entire weekly-schedule
# range. `continuation.SINCHON_SEMESTER_VALUE = 96.0` carried it — but it was INERT there
# (PURPOSE_CHECK §C: +480 identically to all 7,200 candidates, because campus count never
# varied between candidates). In the partition it DOES vary, so it becomes live — and this
# solver had no term for it, choosing 6 국제 / 2 신촌 when the forced minimum is 2 국제.
# Swept, not guessed: R200 measured the plan flipping to 2 국제 / 5 신촌 at a bonus of 30.
SINCHON_BONUS = float(os.environ.get('SINCHON_BONUS', 0.0))


def table():
    d = json.load(open(P('partition.json'), encoding='utf-8'))
    val = {}
    for k, v in d['cost'].items():
        camp, sea, combo = k.split('|', 2)
        if v[0] is None:
            continue
        val[(camp, sea, tuple(sorted(combo.split('+'))))] = v[0]
    return d, val


# ⛔ RED-TEAM F2 / third recurrence of R250. `_future_cache.json` was keyed on the remainder
# ALONE, and shared by three programs running at two different bonuses: render_v3_top50 and
# partition_clickorder set SINCHON_BONUS=30, partition_verdict never set it and ran at the 0.0
# default — then read the renderer's 30.0 values out of the same file. INDEX's own arithmetic
# shows the gap: the six semester values sum to 182.679 but the shipped "rest of degree" is
# 332.679, a difference of exactly 150.000 = 5 신촌 semesters x 30. A cached future is only
# comparable to another if BOTH the bonus and the cost table behind it are identical, so both
# now go in the key. Any change to either invalidates the cache instead of silently mixing.
def table_fingerprint(d):
    h = hashlib.sha1()
    for k in sorted(d.get('cost', {})):
        h.update(f"{k}={d['cost'][k][0]}\n".encode())
    return h.hexdigest()[:12]


def cache_key(rem, d):
    return json.dumps([sorted(rem.items()), round(SINCHON_BONUS, 6), table_fingerprint(d)],
                      ensure_ascii=False, sort_keys=True)


def item_year(key):
    for i in PM.ITEMS:
        if i['key'] == key:
            ys = [QRM_CHART_YEAR[c] for c in (i.get('codes') or []) if c in QRM_CHART_YEAR]
            return min(ys) if ys else 1
    return 1


def solve(counts, val, base, verbose=True):
    """counts: {item: n}. Returns (total_value, plan) maximising Σ best_week."""
    items = sorted(counts)
    YR = {k: item_year(k) for k in items}

    # legal obligation subsets per (campus, season), respecting availability and the table
    subsets = collections.defaultdict(list)
    for camp in CAMPUSES:
        for sea in ('S', 'F'):
            for r in range(0, MAX_OBLIG + 1):
                for combo in itertools.combinations_with_replacement(items, r):
                    c = collections.Counter(combo)
                    if any(c[k] > counts[k] for k in c):
                        continue
                    if r == 0:
                        subsets[(camp, sea)].append(((), base.get(f'{camp}|{sea}', [0])[0]))
                        continue
                    if any(PT.availability(k, camp, sea) != 'OK' for k in c):
                        continue
                    v = val.get((camp, sea, tuple(sorted(combo))))
                    if v is None:
                        continue
                    subsets[(camp, sea)].append((combo, v))

    start = tuple(counts[k] for k in items)

    @functools.lru_cache(maxsize=None)
    def best(i, state, n_intl):
        if i == len(REM):
            # every unit placed, and the campus rule satisfied (sem 2 counts as one 국제)
            return (0.0, ()) if sum(state) == 0 and n_intl + 1 >= 2 else (-1e18, ())
        sem, sea, yr = REM[i]
        out = (-1e18, ())
        for camp in CAMPUSES:
            for combo, v in subsets[(camp, sea)]:
                c = collections.Counter(combo)
                ns = list(state)
                ok = True
                pen = 0.0
                for k, need in c.items():
                    j = items.index(k)
                    if ns[j] < need:
                        ok = False; break
                    ns[j] -= need
                    if YR[k] > yr:                      # taken before its chart year
                        pen += need * year_gap_pen(yr, YR[k])
                if not ok:
                    continue
                if 'QRM3003' in c and not (camp == '국제' and sea == 'S' and yr >= 3):
                    continue                             # R144, hard
                sub, plan = best(i + 1, tuple(ns), n_intl + (1 if camp == '국제' else 0))
                tot = v + pen + sub + (SINCHON_BONUS if camp == '신촌' else 0.0)
                if tot > out[0]:
                    out = (tot, ((sem, camp, sea, combo, round(v, 3), round(pen, 3)),) + plan)
        return out

    return best(0, start, 0)


def report(counts, tag=''):
    d, val = table()
    tot, plan = solve(counts, val, d['base'])
    if tot < -1e17:
        print(f"  {tag}: NO FEASIBLE PARTITION")
        return None
    print(f"  {tag}  Σ week value = {tot:9.3f}")
    for sem, camp, sea, combo, v, pen in plan:
        lab = '+'.join(combo) if combo else '(free electives only)'
        p = f'  year-pen {pen:+.2f}' if pen else ''
        print(f"     sem {sem}  {camp} {sea}   {lab:34s} value {v:8.3f}{p}")
    return tot


if __name__ == '__main__':
    counts = {k: n for k, _c, n in PT.units()}
    print(f"remaining ledger: {counts}   total {sum(counts.values())} units over {len(REM)} semesters\n")
    report(counts, 'CURRENT (Fall defers QRM1001)')
