# -*- coding: utf-8 -*-
"""
partition_clickorder.py — what to click first on 8/25, on the PARTITION objective.

`fallback.py` computed this on the old K objective and is superseded (R297). Same method —
leave-one-out — but scored the way everything else now is:

    cost(section) = best total WITH it  −  best total WITHOUT it

`total` is `Fall week + best Σ best_week over semesters 3-8 of the remainder`, so losing a
section is priced against the whole degree, not against this semester minus a proxy.

⚠️ Cost is what losing a section COSTS, so it is >= 0 by construction. A negative value means
the search did not find the optimum (R269) and is an alarm, not a curiosity.

RUN:  SINCHON_BONUS=30 python partition_clickorder.py
"""
import json, os, glob, collections

import partition_solve as PS
import partition_verdict as PV

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
PS.SINCHON_BONUS = float(os.environ.get('SINCHON_BONUS', 30.0))

d, val = PS.table()
_FUT = {}
_fp = P('_future_cache.json')
if os.path.exists(_fp) and os.path.getsize(_fp):
    _FUT = dict(json.load(open(_fp, encoding='utf-8')))


def future(branch, row):
    rem = PV.remainder(branch, row)
    key = PS.cache_key(rem, d)             # RED-TEAM F2
    if key not in _FUT:
        _FUT[key] = PS.solve(rem, val, d['base'], verbose=False)[0]
    return _FUT[key]


rows = {}
for fp in glob.glob(P('_v3_parts_f2/part_*.json')):
    b = json.load(open(fp, encoding='utf-8'))
    rows[b['branch']] = b['rows']


def best_overall(exclude=frozenset()):
    """Highest total over every branch and row, with `exclude` sections unavailable."""
    best = None
    for b, rs in rows.items():
        for r in rs:
            secs = r['requirements'] + r['electives'] + \
                   ([r['chapel']] if r['chapel'] != '-' else [])
            if exclude & set(secs):
                continue
            f = future(b, r)
            if f < -1e17:
                continue
            t = r['score'] + f
            if best is None or t > best[0]:
                best = (t, b, r, secs)
    return best


raw = json.load(open(P('raw_2026F.json'), encoding='utf-8'))
raw = raw if isinstance(raw, list) else list(raw.values())[0]
idx = {f"{x.get('subjtnb')}-{x.get('corseDvclsNo')}-{x.get('prctsCorseDvclsNo')}": x for x in raw}

base = best_overall()
t0, b0, r0, secs0 = base
print(f"BASE {t0:.3f} · defer {b0}")
for c in secs0:
    print(f"   {c:16s} {str(idx.get(c,{}).get('subjtNm'))[:34]}")
print()
print("IF THIS SECTION IS GONE ON 8/25 — best still reachable, and what it costs")
out = {'base': dict(total=round(t0, 3), defer=b0, sections=secs0), 'loss': {}}
for c in secs0:
    alt = best_overall(frozenset({c}))
    if alt is None:
        print(f"   {c:16s}      —   NO legal timetable at all")
        out['loss'][c] = None
        continue
    t, b, r, secs = alt
    gained = [x for x in secs if x not in secs0]
    out['loss'][c] = dict(total=round(t, 3), cost=round(t0 - t, 3), defer=b, sections=secs)
    print(f"   {c:16s} {t0-t:7.3f}  -> {t:.2f} · defer {b} · swap in {' '.join(gained) or '(same courses)'}")

order = sorted((x for x in out['loss'].items() if x[1]), key=lambda t: -t[1]['cost'])
print("\n⭐ CLICK ORDER on 8/25 — most costly to lose, first:")
for i, (c, v) in enumerate(order, 1):
    nm = str(idx.get(c, {}).get('subjtNm'))[:30]
    print(f"   {i}. {c:16s} {nm:32s} costs {v['cost']:.2f}")
neg = [c for c, v in out['loss'].items() if v and v['cost'] < -1e-6]
print(f"\n   negative costs (soundness alarm): {neg or 'none'}")
json.dump(out, open(P('partition_clickorder.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
