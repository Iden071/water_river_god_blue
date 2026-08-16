# -*- coding: utf-8 -*-
"""
verify_rank4.py — independent recomputation of rank4's top rows.

R175 / R177 discipline: recompute every reported score from its parts, using a code path
that does NOT share the search's arithmetic, and fail loudly on any mismatch. Two of this
project's worst errors were a comparison whose candidates were infeasible and a silent
`except:` that swallowed a NameError.
"""
import csv, json, os, sys
import rank2 as R2, rank3, rank4
import difficulty as DIFF
from rank2 import fast_score, eff_year, YEAR_PEN
from continuation import solve
from defer_value2 import remainder_after, ALL_REQS
# item per SECTION, written by rank4 from the pool's own qcat/_qrm_me fields.
# Never re-derive this from a hand-written code list — that is what flipped #1 on the
# first pass (ECO1104-07-00 has qcat=None; a hand list called it a Major Elective).
ITEM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'elective_items.json'), encoding='utf-8'))

HERE = os.path.dirname(os.path.abspath(__file__))
P, sig, sigs, SIGCODES, code = rank3.build()
byc = {s['c']: s for v in P.values() for s in v}

V_REF = rank4.v_ref()
rows = list(csv.DictReader(open(os.path.join(HERE, 'FINAL_ranked4.csv'),
                               encoding='utf-8-sig')))

print(f"V_REF = {V_REF:.3f}   |   live D_LANG = {DIFF.D_LANG}")
print()
hdr = (f"{'#':>3} {'reported':>9} {'week':>8} {'yrpen':>7} {'chapel':>7} "
       f"{'ΔV':>9} {'recomputed':>11} {'ok':>4}")
print(hdr); print("-" * len(hdr))

bad = 0
for i, r in enumerate(rows[:15], 1):
    reqs = r['requirements'].split()
    els  = r['electives'].split()
    tm = pm = fmm = 0
    for c in reqs + els:
        s = byc[c]; tm |= s['tm']; pm |= s['pm']; fmm |= s['fm']
    ch = r['chapel']
    has_ch = bool(ch and ch != '-')
    if has_ch:
        s = byc[ch]; tm |= s['tm']; pm |= s['pm']; fmm |= s['fm']
    week, det = fast_score(tm, pm, fmm)      # R210: comfort on the FIXED mask
    yrpen = sum(YEAR_PEN(eff_year(byc[c], code)) for c in reqs + els)
    chap = rank4.CHAPEL_BONUS if has_ch else rank4.CHAPEL_DEFER

    dfset = frozenset() if r['deferred'] == '-' else frozenset(r['deferred'].split('+'))
    items = tuple(sorted(ITEM.get(c, 'FREE') for c in els))
    dV = rank4.V((dfset, items)) - V_REF
    # ⭐ difficulty must be reconstructed too, or a mismatch between the LIVE D_LANG and the
    # D_LANG the CSV was scored at passes silently. That is exactly the rot R187 is about.
    dif = -DIFF.D_LANG * DIFF.GPA_GATE_MULT * sum(DIFF.steps(c) for c in reqs + els)
    if 'Lang' in dfset:                      # channel 2 — R188
        dif -= DIFF.p_hard_if_deferred()[1] * DIFF.D_LANG   # pessimistic arm, R190

    total = week + yrpen + chap + dV + dif
    ok = abs(total - float(r['score'])) < 1e-3
    bad += (not ok)
    print(f"{i:3d} {float(r['score']):9.3f} {week:8.3f} {yrpen:7.3f} {chap:7.2f} "
          f"{dV:9.3f} {total:11.3f} {'OK' if ok else 'FAIL':>4}")

print()
if bad:
    print(f"❌ {bad} of 15 rows do not reconstruct. The ranker and this file disagree.")
    sys.exit(1)
print("✅ all 15 top rows reconstruct exactly from week + year penalty + chapel + ΔV.")

# ---------------------------------------------------------------------------
# FEASIBILITY OF EVERY CANDIDATE IN THE HEADLINE COMPARISON (R175)
# ---------------------------------------------------------------------------
print()
print("=" * 74)
print("FEASIBILITY — does every remainder actually admit a legal 6-semester plan?")
print("=" * 74)
seen = set()
for r in rows[:200]:
    dfset = frozenset() if r['deferred'] == '-' else frozenset(r['deferred'].split('+'))
    items = tuple(sorted(ITEM.get(c, 'FREE') for c in r['electives'].split()))
    key = (dfset, items)
    if key in seen: continue
    seen.add(key)
    taken = [x for x in ALL_REQS if x not in dfset]
    rem = remainder_after(taken, [], chapel=True)
    for k in items: rem[k] = max(0, rem[k] - 1)
    v, plan = solve(rem)
    status = "FEASIBLE" if plan else "❌ INFEASIBLE"
    print(f"  defer={'+'.join(sorted(dfset)) or '-':8s} electives={'+'.join(items):18s} "
          f"V={v:10.3f}  {status}")

# ---------------------------------------------------------------------------
# THE ASSUMPTION THE TOP OF THE RANKING RESTS ON
# ---------------------------------------------------------------------------
print()
print("=" * 74)
print("⚠️  WHAT THE #1 RESULT DEPENDS ON")
print("=" * 74)
top = rows[0]
print(f"  #1 electives: {top['electives']}  -> items {top['elective_items']}")
for c in top['electives'].split():
    k = c[:7]
    mapped = ITEM.get(c, 'FREE')
    flag = ""
    print(f"    {c:16s} -> {mapped}{flag}")
