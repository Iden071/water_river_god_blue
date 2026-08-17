# -*- coding: utf-8 -*-
import os, json, glob
import partition_solve as PS, partition_verdict as PV
d, val = PS.table()
rows = {}
for fp in glob.glob('_v3_parts_f2/part_*.json'):
    b = json.load(open(fp, encoding='utf-8')); rows[b['branch']] = b['rows']
print(f"  {'신촌 bonus':>10s}  {'winner':7s} {'margin':>8s}  campus plan (sems 3-8)")
for bonus in (2.0, 10.0, 30.0):
    PS.SINCHON_BONUS = bonus
    PS.solve.__wrapped__ if hasattr(PS.solve, '__wrapped__') else None
    out = []
    seen = {}
    for br in ('-', 'MR', 'WCiv', 'LHP', 'SciRD', 'Lang'):
        best = None
        # ⛔ RED-TEAM F5, sixth instance of truncate-then-maximise (R260, R269, R276, R295,
        # F3). This was `sorted(..., key=-score)[:5]` — rank by FALL WEEK, then maximise
        # `Fall + future`. R295 already established that the true argmax has a Fall week of
        # 19.890 and sits far below even the top 40, so it was never in this prefix at any
        # bonus. That made the bonus bracket, and therefore the entire campus plan, a
        # conclusion drawn from five rows the model has since declared wrong. Scan every row.
        for r in (rows.get(br) or []):
            rem = PV.remainder(br, r)
            key = (tuple(sorted(rem.items())), bonus)
            if key not in seen:
                seen[key] = PS.solve(rem, val, d['base'])
            fut, plan = seen[key]
            if fut < -1e17: continue
            t = r['score'] + fut
            if best is None or t > best[0]: best = (t, br, plan)
        if best: out.append(best)
    out.sort(reverse=True)
    if len(out) < 2: continue
    t, br, plan = out[0]
    intl = sum(1 for p in plan if p[1] == '국제')
    print(f"  {bonus:10.1f}  {br:7s} {t-out[1][0]:8.3f}  {intl} 국제 / {len(plan)-intl} 신촌")
