# -*- coding: utf-8 -*-
"""
ledger_nodm.py — the degree WITHOUT a double major, and what it does to the answer.

THE ASSUMPTION BEING TESTED (R238, tier 2.1)
`plan_model.ITEMS` encodes ME = 18 cr, `DM` = 12 units, `FREE` = 15 cr. All three follow from
**obtaining a double major** — a December, competitive decision made on Semesters 1–2 GPA,
i.e. decided partly by the very semester being planned. The failure branch is represented
nowhere, and `GPA_GATE_MULT` (which exists for exactly this feedback loop) sits at 1.0, inert.

THE ALTERNATIVE LEDGER, derived the same way the live one was
    single major  ->  ME back to 24 cr (R31: "Major credits will be reduced to 36 if a student
                      completes a double major" — so 36 without, of which MR is 18)
                  ->  DM disappears entirely (12 units, 36 cr)
                  ->  FREE is the residual, recomputed:
                      126 − 19.5 done − 19.5 CC − 18 MR − 24 ME = 45.0 cr = 15 courses

| item  | with a double major | without |
|-------|--------------------:|--------:|
| ME    | 6 units (18 cr)     | **8 units (24 cr)** |
| DM    | 12 units (36 cr)    | **0** |
| FREE  | 5 units (15 cr)     | **15 units (45 cr)** |

Both reconcile to 106.5 cr. The unit COUNT is identical (38) — what changes is the mix, and
with it two things that matter:

  1. **`DM` is the only 신촌-only bulk item.** Without it there is no structural pressure to
     spend semesters at 신촌 at all, so the campus plan is no longer forced.
  2. **`FREE` triples.** Since deferring a FREE costs ~0 (supply 422, no chart year — R236),
     a degree that is one third free electives is far easier to place, which is exactly what
     the deferral costs are measured against.
"""
import json, os, copy, collections

HERE = os.path.dirname(os.path.abspath(__file__))
import plan_model as PM


def items_nodm():
    """The ledger as it would be with a single major. Same shape, different counts."""
    out = []
    for it in PM.ITEMS:
        it = copy.deepcopy(it)
        if it['key'] == 'DM':
            continue                                  # no second major
        if it['key'] == 'ME':
            it['count'] = 8                           # 24 cr, R31
            it['note'] = ('[D] SINGLE-MAJOR branch: R31 reduces Major credits to 36 only WITH a '
                          'double major. Without one, ME is 24 cr = 8 courses.')
        if it['key'] == 'FREE':
            it['count'] = 15                          # residual, recomputed
            it['note'] = ('[D] RESIDUAL under a single major: 126 − 19.5 done − 19.5 CC − 18 MR '
                          '− 24 ME = 45.0 cr = 15 courses. Three times the double-major figure.')
        out.append(it)
    return out


def reconcile(items, label):
    cc = sum(i['credits'] * i['count'] for i in items
             if i['key'] in ('Chapel', 'LHP', 'Lang', 'SciRD', 'WCiv', 'Seminar'))
    mr = sum(i['credits'] * i['count'] for i in items
             if i['key'] in ('QRM1001', 'ECO1101', 'ECO2102', 'ECO2101', 'MR5', 'QRM3003'))
    me = sum(i['credits'] * i['count'] for i in items if i['key'] == 'ME')
    dm = sum(i['credits'] * i['count'] for i in items if i['key'] == 'DM')
    fr = sum(i['credits'] * i['count'] for i in items if i['key'] == 'FREE')
    tot = cc + mr + me + dm + fr
    need = PM.TOTAL_CREDITS - PM.DONE_CREDITS
    units = sum(i['count'] for i in items)
    print(f"  {label:24s} CC {cc:5.1f} · MR {mr:5.1f} · ME {me:5.1f} · DM {dm:5.1f} · "
          f"FREE {fr:5.1f}  = {tot:6.1f} vs {need:.1f}  {'MATCH' if abs(tot-need)<1e-9 else 'MISMATCH'}"
          f"   ({units} units)")
    return abs(tot - need) < 1e-9


if __name__ == '__main__':
    print("LEDGER RECONCILIATION — both branches must add to 106.5 cr")
    a = reconcile(PM.ITEMS, 'with a double major')
    b = reconcile(items_nodm(), 'WITHOUT (single major)')
    print()
    print("WHAT CHANGES")
    by_a = {i['key']: i['count'] for i in PM.ITEMS}
    by_b = {i['key']: i['count'] for i in items_nodm()}
    for k in sorted(set(by_a) | set(by_b)):
        if by_a.get(k, 0) != by_b.get(k, 0):
            print(f"  {k:9s} {by_a.get(k,0):3d}  ->  {by_b.get(k,0):3d} units")
    print()
    sin_a = sum(i['count'] for i in PM.ITEMS if i['campus'] == '신촌')
    sin_b = sum(i['count'] for i in items_nodm() if i['campus'] == '신촌')
    print(f"  units that MUST be taken at 신촌: {sin_a} -> {sin_b}")
    print("  ⇒ DM is the only bulk 신촌-only item. Without it the campus plan is barely forced,")
    print("    which is the assumption the entire 신촌-preference layer rests on (R126/R226).")
