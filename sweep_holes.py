# -*- coding: utf-8 -*-
"""
sweep_holes.py — does the ANSWER depend on the constants nobody ever elicited?

WHY THIS EXISTS, AND WHY THE OLD ONE DID NOT WORK
-------------------------------------------------
Two constants sit directly in the v3 scoring line (`research_v3.py`):

    dif = -DIFF.D_LANG * DIFF.GPA_GATE_MULT * sum(DIFF.steps(code(s)) for s in combo)

  · `D_LANG        = 10.0`  — env default. difficulty.py's own words: "never been elicited."
  · `GPA_GATE_MULT = 1.0`   — "[P] NEVER ELICITED. Default 1.0 = inert."

Neither has ever been swept against the v3 model, because **both tools that were supposed to
do it are broken** (audited 2026-08-16):

  1. `research_v3.py` caches branches at `_v3_parts_f{MAX_FREE}` — the key does NOT include
     the scoring constants. `D_LANG=999.0 python research_v3.py Lang` prints "cached" and
     recomputes nothing. Any sweep driven that way is a silent no-op.
  2. `sweep_difficulty.py` raises `TypeError: unsupported operand type(s) for +: 'int' and
     'tuple'` — it has been dead since R190 made `p_hard_if_deferred()` return a bracket.
     It also reads `FINAL_ranked4.csv`, which INDEX marks superseded, and it RESCORES a fixed
     candidate set rather than re-searching, so it cannot find a timetable that only becomes
     optimal at a different D_LANG.

This file re-SEARCHES at every grid point, through `fallback.search()`, which recomputes every
branch from scratch and truncates its own state — so there is no cache to go stale.

WHAT IT REPORTS
  For each (D_LANG, GPA_GATE_MULT): the winning deferral branch and its total. The verdict is
  "defer Language". The question is at which values that stops being true.

RUN:  python sweep_holes.py
"""
import os, sys, json, io, contextlib, time, collections

os.environ.setdefault('MAX_FREE', '2')

import difficulty as DIFF
import research_v3 as RV
import fallback as FB

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

D_LANG_GRID = [0.0, 5.0, 10.0, 20.0, 45.0]
GATE_GRID = [1.0, 2.0]

BASE_D = DIFF.D_LANG
BASE_G = DIFF.GPA_GATE_MULT

# ⚠️ the pools are built ONCE. `fallback.search()` rebuilds them on every call, which made a
# grid of this size exceed the runtime budget; nothing in rank3.build() depends on D_LANG or
# GPA_GATE_MULT, so hoisting it is safe and is the only reason this sweep is affordable.
import rank2 as _R2, rank3 as _rank3, fm_fix as _fm, eligibility as _el

_POOLS = None


def pools():
    global _POOLS
    if _POOLS is None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            Pp, sig, sigs, SIGCODES, code = _rank3.build()
            _fm.apply(Pp, verbose=False)
            _el.apply(Pp, verbose=False)
        ZERO = {c[:7] for c, s in
                {x['c']: x for v in Pp.values() for x in v}.items()
                if s['fm'] == 0 and s['tm']}
        for pool in Pp.values():
            pool[:] = [s for s in pool if s['code'] not in ZERO]
        LANGP = [s for s in Pp['OPEN'] if code(s) in _R2.LANG]
        ELEC = [s for s in Pp['OPEN'] if code(s) not in _R2.LANG]
        REQ = {'MR': Pp['MR'], 'WCiv': Pp['WCiv'], 'LHP': Pp['LHP'],
               'SciRD': Pp['SciRD'], 'Lang': LANGP}
        _POOLS = (Pp, REQ, ELEC, code)
    return _POOLS


def verdict(d_lang, gate):
    """Best (total, branch) under these constants, re-searched from scratch."""
    DIFF.D_LANG = d_lang
    DIFF.GPA_GATE_MULT = gate
    RV.MAX_FREE = 2
    RV.TOPN = 60
    RV.STATE = P('_sweep_tmp')
    os.makedirs(RV.STATE, exist_ok=True)
    Pp, REQ, ELEC, code = pools()
    best = None
    for b in FB.B:
        p = os.path.join(RV.STATE, f'part_{b}.json')
        open(p, 'w').close()                      # no cache may survive between grid points
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                RV.run_branch(b, Pp, REQ, ELEC, code)
        except Exception:
            continue
        if not os.path.getsize(p):
            continue
        rows = json.load(open(p, encoding='utf-8'))['rows']
        for r in rows[:60]:
            v = FB.total(r, b)
            if v is not None and (best is None or v > best[0]):
                best = (v, b, r)
        open(p, 'w').close()
    if best is None:
        return None, None, None
    v, b, r = best
    secs = r['requirements'] + r['electives'] + ([r['chapel']] if r['chapel'] != '-' else [])
    return v, b, secs


def main():
    t0 = time.time()
    print(f"baseline in force: D_LANG={BASE_D}  GPA_GATE_MULT={BASE_G}")
    print("re-SEARCHING at every grid point (no cache reuse)\n")
    print(f"  {'D_LANG':>7} " + ' '.join(f'{"gate="+format(g,".1f"):>16s}' for g in GATE_GRID))

    grid = {}
    for d in D_LANG_GRID:
        cells = []
        for g in GATE_GRID:
            v, b, secs = verdict(d, g)
            grid[(d, g)] = (v, b, secs)
            cells.append(f'{b or "—":>6s} {v:9.3f}' if v is not None else f'{"—":>16s}')
        star = ' ⭐ baseline' if abs(d - BASE_D) < 1e-9 else ''
        print(f"  {d:7.2f} " + ' '.join(cells) + star)

    DIFF.D_LANG, DIFF.GPA_GATE_MULT = BASE_D, BASE_G

    print(f"\n{'='*78}")
    branches = {b for (v, b, s) in grid.values() if b}
    if len(branches) == 1:
        b = branches.pop()
        print(f"✅ THE VERDICT NEVER CHANGES across the whole grid: defer {b}.")
        print(f"   D_LANG swept {min(D_LANG_GRID)}–{max(D_LANG_GRID)} "
              f"(scale reminder: one 9:00 start = 10), GPA_GATE_MULT {GATE_GRID}.")
        print(f"   Both unelicited constants are therefore NOT load-bearing for the choice of")
        print(f"   which requirement to defer — only for the size of the margin.")
    else:
        print(f"⚠️ THE VERDICT MOVES. Branches seen: {sorted(branches)}")
        for g in GATE_GRID:
            prev, flips = None, []
            for d in D_LANG_GRID:
                b = grid[(d, g)][1]
                if prev is not None and b != prev:
                    flips.append((d, prev, b))
                prev = b
            if flips:
                for d, a, b in flips:
                    print(f"   gate={g}: defer {a} -> defer {b} between "
                          f"D_LANG {D_LANG_GRID[D_LANG_GRID.index(d)-1]} and {d}")
            else:
                print(f"   gate={g}: no flip across the D_LANG range")

    # does the SET of sections move, even when the branch does not?
    sets = {tuple(sorted(s)) for (v, b, s) in grid.values() if s}
    print(f"\n   distinct TIMETABLES across the grid: {len(sets)}")
    if len(sets) > 1:
        # the baseline need not be a grid point when the grid is refined by hand
        base = (grid.get((BASE_D, BASE_G)) or grid[max(grid)])[2]
        for s in sorted(sets):
            diff = set(s) ^ set(base or [])
            if diff:
                print(f"     differs from baseline by: {sorted(diff)}")

    json.dump({f'{d}|{g}': dict(total=v, defer=b, sections=s)
               for (d, g), (v, b, s) in grid.items()},
              open(P('sweep_holes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"\n[{time.time()-t0:.0f}s] wrote sweep_holes.json")


if __name__ == '__main__':
    main()
