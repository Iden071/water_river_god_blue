# -*- coding: utf-8 -*-
"""Does #1 survive if ECO1103/1104 do NOT count as QRM Major Electives?
VERIFY item 22 has been open since the first session and the new #1 rests on it."""
import csv, importlib
import rank4, defer_value2

for mod in (rank4, defer_value2):
    for k in ('ECO1103', 'ECO1104'):
        mod.ELECTIVE_TO_ITEM.pop(k, None)
rank4._VC.clear()
print("ECO1103 / ECO1104 demoted to plain free electives.\n", flush=True)
out = rank4.main(TOPN=200)
rows = out[:6]
print("\nTOP 6 WITHOUT THE ECO1104 ASSUMPTION")
for i, (sc, _n, key, det) in enumerate(rows, 1):
    req, ch, el, df = key
    print(f"  {i}  {sc:8.3f}  defer={'+'.join(df) or '-':6s} | {' '.join(req)} | "
          f"{' '.join(g[4] for g in el)}")
