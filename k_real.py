# -*- coding: utf-8 -*-
"""
k_real.py — K re-measured against REAL per-(campus, season, year) catalogues.

Replaces two substitutions at once:
  · the filler pool is now the right campus in the right SEASON (G-9 retired for the branches
    that were affected), and per-YEAR rather than unioned, because a single future semester
    offers one year's catalogue, not three years stacked;
  · the deferred requirement's own geometry is drawn from what was actually observed at that
    campus in that season across 2024/2025/2026.

The spread across the three observed years IS the year-to-year uncertainty, measured rather
than assumed. Every value is exact (the b1_curve engine); truncation is reported, not hidden.
"""
import json, os, sys, time, statistics, collections
import pools_past as PP
import b1_curve as B
import difficulty as DIFF

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'k_real.json')
YEARS = ('2024', '2025', '2026')
LOADS = (3, 4, 5)

# requirement -> (codes, receiving campus, receiving season)
CASES = {
    'MR':        (['QRM1001'], '국제', 'S'),
    'WCiv':      (['UIC1561'], '국제', 'S'),
    'LHP':       (['UIC1551', 'UIC1251', 'UIC1501'], '신촌', 'F'),
    'SciRD':     (['UIC2151'], '신촌', 'F'),
    'Lang·easy': (sorted(DIFF.LANG_EASY), '국제', 'S'),
    'Lang·hard': (sorted(DIFF.LANG_HARD), '신촌', 'F'),
}


def load():
    if os.path.exists(OUT) and os.path.getsize(OUT):
        try:
            return json.load(open(OUT, encoding='utf-8'))
        except Exception:
            pass
    return {'base': {}, 'k': {}}


def save(d):
    json.dump(d, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def geometries(codes, campus, season, year=None):
    """Distinct (tm,pm) this requirement was observed with, at that campus/season."""
    got = {}
    for c in codes:
        for lab, sigs in PP.course_geometries(c, campus, season).items():
            if year and not lab.startswith(year):
                continue
            for g in sigs:
                got.setdefault(g, set()).add(lab)
    return got


# ---------------------------------------------------------------------------
# R268 — the node cap is a PARAMETER, not a constant.
# It was hardcoded at 30_000_000. Once R264's parser fix enlarged the pools
# (신촌 F 2026: 147 -> 175 signatures) a full run was Killed by the OOM killer partway
# through 신촌. 4_000_000 completes and still returns exact=True on every geometry measured,
# so the old cap was oversized rather than necessary.
NODE_CAP = int(os.environ.get('NODE_CAP', 4_000_000))

# ---------------------------------------------------------------------------
# R267 — `disp` HAD NO PRODUCER. It is read by fallback.py / render_v3.py /
# render_v3_top50.py via unit_cost(), and was written by nothing in the repo, so it could not
# be regenerated after the parser fix. This is that producer.
#
# WHAT `disp` MEANS, and how it differs from `k` (they are NOT the same mechanism):
#   k[item]     cost of DEFERRING a requirement out of this semester. Only the five things
#               that can be a deferral branch have one: MR, WCiv, LHP, SciRD, Lang.
#   disp[item]  the deferral cost SAVED by discharging a ledger UNIT now instead of later —
#               a CREDIT, applied to electives. Only ledger items an elective can actually
#               be assigned to need one: ECO1101 and ME. (FREE is 0 by R236 — it is the
#               unconstrained residual; DM has no course identity until December, R225.)
# Both are measured the same way: pin the item's observed geometry into a receiving semester
# and take the comfort lost against that semester's baseline.
DISP_CASES = {
    'ECO1101': ['ECO1101'],
    'ME': None,          # filled from plan_model at call time — the ME course pool
}
DISP_RECV = (('국제', 'S'), ('신촌', 'F'))


def disp_codes(name):
    if DISP_CASES.get(name):
        return DISP_CASES[name]
    from plan_model import ITEMS
    for i in ITEMS:
        if i['key'] == name:
            return list(i.get('codes') or [])
    return []


def build_disp(d, budget=150, t0=None):
    """Regenerate d['disp'] — keys `item|campus+season|year`, same units as k."""
    t0 = t0 if t0 is not None else time.time()
    d.setdefault('disp', {})
    for name in DISP_CASES:
        codes = disp_codes(name)
        if not codes:
            continue
        for camp, sea in DISP_RECV:
            for y in YEARS:
                kk = f"{name}|{camp}{sea}|{y}"
                if kk in d['disp']:
                    continue
                pool, _src = PP.pool(camp, sea, years=[y])
                if not pool:
                    continue
                bk = f"{camp}|{sea}|{y}|5"
                if bk not in d['base']:
                    v, _nd, ok = B.best_week([], 5, pool, node_cap=NODE_CAP)
                    d['base'][bk] = [v, ok]; save(d)
                b, okb = d['base'][bk]
                geos = geometries(codes, camp, sea, year=None)
                vals = []
                for g in geos:
                    v, _nd, ok = B.best_week([g], 4, pool, node_cap=NODE_CAP)
                    if v is not None:
                        vals.append((round(b - v, 3), bool(ok and okb)))
                if vals:
                    # min over geometries, matching kdefer's convention for the credit side
                    best = min(vals, key=lambda t: t[0])
                    d['disp'][kk] = [best[0], best[1], len(geos)]
                    save(d)
                    print(f"  disp {kk}: {best[0]:8.3f} "
                          f"{'exact' if best[1] else 'BOUND'} over {len(geos)} geoms "
                          f"[{time.time()-t0:.0f}s]", flush=True)
                if time.time() - t0 > budget:
                    print("  … budget reached, resumable", flush=True)
                    return d
    return d


def main(only=None, budget=150):
    d = load()
    t0 = time.time()
    for name, (codes, camp, sea) in CASES.items():
        if only and name not in only:
            continue
        for y in YEARS:
            pool, _src = PP.pool(camp, sea, years=[y])
            if not pool:
                continue
            # baseline: n+1 free courses, no requirement pinned
            for n in LOADS:
                bk = f"{camp}|{sea}|{y}|{n+1}"
                if bk not in d['base']:
                    v, _nd, ok = B.best_week([], n + 1, pool, node_cap=NODE_CAP)
                    d['base'][bk] = [v, ok]
                    save(d)
                    print(f"  base {bk}: {v:8.3f} {'exact' if ok else 'BOUND'} "
                          f"[{time.time()-t0:.0f}s]", flush=True)
                if time.time() - t0 > budget:
                    print("  … budget reached, resumable"); return d
            geos = geometries(codes, camp, sea)
            for g, seen in geos.items():
                for n in LOADS:
                    kk = f"{name}|{y}|{PP.show(g[0])}|{n}"
                    if kk in d['k']:
                        continue
                    v, _nd, ok = B.best_week([g], n, pool, node_cap=NODE_CAP)
                    b, okb = d['base'][f"{camp}|{sea}|{y}|{n+1}"]
                    d['k'][kk] = [None if v is None else round(b - v, 3),
                                  bool(ok and okb), sorted(seen)]
                    save(d)
                    if time.time() - t0 > budget:
                        print(f"  … budget reached at {kk}, resumable", flush=True)
                        return d
            print(f"{name:10s} {y}: {len(geos)} geometries done [{time.time()-t0:.0f}s]",
                  flush=True)
    return d


def report():
    d = load()
    print("=" * 100)
    print("K AGAINST REAL PER-YEAR CATALOGUES — spread across years IS the uncertainty")
    print("=" * 100)
    rows = collections.defaultdict(dict)
    for k, v in d['k'].items():
        name, y, geo, n = k.split('|')
        rows[(name, geo)][(y, int(n))] = v
    for (name, geo), cells in sorted(rows.items()):
        ns = sorted({n for _, n in cells})
        line = f"  {name:10s} {geo:22s}"
        for n in ns:
            vals = [cells[(y, n)][0] for y in YEARS if (y, n) in cells
                    and cells[(y, n)][0] is not None]
            if not vals:
                continue
            line += (f"  n={n}: {statistics.median(vals):6.2f}"
                     f" [{min(vals):6.2f},{max(vals):6.2f}]")
        seen = sorted({t for c in cells.values() for t in c[2]})
        print(line + f"   seen {','.join(seen)}")


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('-')]
    if '--report' in sys.argv:
        report()
    else:
        _d = main(only=a or None)
        build_disp(_d)
        report()
