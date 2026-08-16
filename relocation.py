# -*- coding: utf-8 -*-
"""
relocation.py — K measured against the REAL remaining obligations, not free-choice fillers.

THE DEFECT (R285, Iden 2026-08-16)
----------------------------------
    "For all courses, we don't know if we're applying a penalty to this semester that will
     just be pushed over to the next one. For required components especially, this is
     important."

Every ledger item must be taken eventually, so a schedule penalty on a required course cannot
be AVOIDED — only RELOCATED. `k_real.py` measures the cost of deferring a requirement by
pinning its geometry into a semester of **free-choice filler courses**, which can dodge every
penalty. A real future semester is full of other obligations that cannot dodge anything.

So `K` systematically misprices deferral, and the sign of the error depends on interaction:
  · a clean filler semester makes a deferred course look EXPENSIVE (it breaks a pristine week)
  · a semester already carrying an unavoidable penalty makes it look CHEAP (measured: a second
    금 course costs −2.321 once 금 is already broken, vs +8.137 in a clean semester)

WHAT THIS DOES
--------------
Rebuilds the filler pool out of the sections that actually remain on the degree ledger, then
recomputes K for every deferral branch against it. Same `b1_curve` engine, same exactness
reporting — only the pool changes, so the delta isolates the defect.

⚠️ This is a FIRST CORRECTION, not the full model. The complete formulation optimises the
partition of all remaining units across all remaining semesters (Σ discomfort per semester).
This measures the same marginal K against a realistic semester instead of a fictional one,
which removes the largest part of the error without the combinatorics.

RUN:  NODE_CAP=1200000 python relocation.py
"""
import json, os, sys, time, collections

import pools_past as PP
import b1_curve as B
import plan_model as PM
import difficulty as DIFF

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
NODE_CAP = int(os.environ.get('NODE_CAP', 1_200_000))
OUT = P('relocation.json')

# what Fall 2026 consumes under the current recommendation, so the rest is what remains
TAKEN_FALL = {'WCiv', 'LHP', 'SciRD', 'Lang', 'ECO1101', 'ME', 'Chapel'}

CASES = {
    'MR':        (['QRM1001'], '국제', 'S'),
    'WCiv':      (['UIC1561'], '국제', 'S'),
    'LHP':       (['UIC1551', 'UIC1251', 'UIC1501'], '신촌', 'F'),
    'SciRD':     (['UIC2151'], '신촌', 'F'),
    'Lang·hard': (sorted(DIFF.LANG_HARD), '신촌', 'F'),
}
MAP = {'WCiv': 'WCiv', 'LHP': 'LHP', 'SciRD': 'SciRD', 'Lang': 'Lang·hard', 'MR': 'MR'}


def remaining_units():
    """Ledger items still owed after Fall 2026, with their observed course codes."""
    out = []
    for i in PM.ITEMS:
        codes = i.get('codes') or []
        n = i['count'] - (1 if i['key'] in TAKEN_FALL else 0)
        if n > 0 and codes:
            out.append((i['key'], codes, n))
    return out


def obligation_pool(campus, season, exclude=()):
    """Filler pool built from what is actually still OWED, not from the whole catalogue.

    Each remaining ledger item contributes the (tm, pm) geometries it was observed with at
    this campus/season. That is the honest stand-in for 'the other courses in that semester'.
    """
    got = set()
    for key, codes, n in remaining_units():
        if key in exclude:
            continue
        for c in codes:
            for _lab, sigs in PP.course_geometries(c, campus, season).items():
                for g in sigs:
                    got.add(g)
    return sorted(got)


def main():
    t0 = time.time()
    d = {}
    if os.path.exists(OUT) and os.path.getsize(OUT):
        try:
            d = json.load(open(OUT, encoding='utf-8'))
        except Exception:
            d = {}
    d.setdefault('K_real', {})
    d.setdefault('K_oblig', {})
    d.setdefault('pools', {})

    print(f"NODE_CAP = {NODE_CAP}\n")
    print("remaining ledger after Fall 2026:")
    for key, codes, n in remaining_units():
        print(f"   {key:9s} x{n}  {','.join(codes)[:52]}")
    print()

    kr = json.load(open(P('k_real.json'), encoding='utf-8'))
    live = {}
    for k, v in kr['k'].items():
        nm, y, g, nn = k.split('|')
        if y == '2026' and int(nn) == 4 and v[0] is not None:
            live.setdefault(nm, {})[g] = v[0]

    print(f"  {'branch':11s} {'free-choice pool':>17s} {'obligation pool':>17s} {'K free':>9s} "
          f"{'K oblig':>9s} {'delta':>8s}")
    for b, nm in MAP.items():
        codes, camp, sea = CASES[nm]
        # the receiving semester should NOT be filled with the very item being deferred
        pool = obligation_pool(camp, sea, exclude={b})
        free_pool, _src = PP.pool(camp, sea, years=['2026'])
        d['pools'][b] = [len(free_pool), len(pool)]
        if not pool:
            print(f"  {b:11s} {len(free_pool):17d} {0:17d}   (no remaining obligations here)")
            continue
        bk = f'{b}|base'
        if bk not in d['K_oblig']:
            v, _n, ok = B.best_week([], 5, pool, node_cap=NODE_CAP)
            d['K_oblig'][bk] = [v, ok]
            json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        base, okb = d['K_oblig'][bk]

        geos = {}
        for c in codes:
            for _lab, sigs in PP.course_geometries(c, camp, sea).items():
                for g in sigs:
                    geos[PP.show(g[0])] = g
        vals = []
        for lab, g in geos.items():
            kk = f'{b}|{lab}'
            if kk not in d['K_oblig']:
                v, _n, ok = B.best_week([g], 4, pool, node_cap=NODE_CAP)
                d['K_oblig'][kk] = [None if v is None else round(base - v, 3), bool(ok and okb)]
                json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            if d['K_oblig'][kk][0] is not None:
                vals.append(d['K_oblig'][kk][0])
            if time.time() - t0 > 150:
                print("  … budget reached, resumable")
                json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
                return
        if not vals:
            continue
        k_new = min(vals)
        k_old = min(live.get(nm, {}).values()) if live.get(nm) else float('nan')
        d['K_real'][b] = k_old
        print(f"  {b:11s} {len(free_pool):17d} {len(pool):17d} {k_old:9.3f} {k_new:9.3f} "
              f"{k_new-k_old:+8.3f}")

    json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"\n[{time.time()-t0:.0f}s] wrote relocation.json")


if __name__ == '__main__':
    main()
