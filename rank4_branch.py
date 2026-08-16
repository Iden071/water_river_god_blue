# -*- coding: utf-8 -*-
"""
rank4_branch.py — run the rank4 search ONE DEFERRAL BRANCH AT A TIME, resumably.

WHY
---
Widening the language pool from 2 courses to R166's 10 (`difficulty.py`) multiplies the
requirement product by ~2.5 and pushes a single full search past the wall-clock limit of one
run. Splitting by deferral branch is exact — the branches partition the search space — and
the branch-and-bound incumbent is carried between runs through `incumbent.json`, so nothing
is lost by stopping and resuming. Running the branches in a worse order only costs time.

USAGE
  python rank4_branch.py reset                 # clear partial state
  python rank4_branch.py '-'                   # the 'defer nothing' branch
  python rank4_branch.py MR                    # the 'defer MR' branch   ... etc
  python rank4_branch.py merge                 # -> FINAL_ranked4.csv

ALL branches must be run before `merge`, and `merge` refuses if any is missing.
"""
import json, os, sys, csv, collections, itertools, time, heapq
import rank2 as R2
import difficulty as DIFF

# ⭐ WIDEN THE LANGUAGE POOL BEFORE ANYTHING IMPORTS IT (R166 / G-10).
# rank3.build() execs rank2's SOURCE, but rank3/rank4 select the language pool with
# `R2.LANG` — the live module attribute — so this override reaches the ranker without
# editing rank2.py, which cannot be safely modified above its exec marker (INDEX trap #1).
R2.LANG = set(DIFF.LANG_ALL)

import rank3, rank4
from rank2 import fast_score, YEAR_PEN, eff_year, week_value

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, '_rank4_parts')
os.makedirs(STATE, exist_ok=True)
INC = os.path.join(STATE, 'incumbent.json')
# ⭐ R214 — Iden: "why were the branches biased? Every possibility should just be numerically
# computed, not predecided." This was a hand-written list of the six 0-or-1 deferral cases.
# It is now the POWERSET, generated: 32 branches, every subset of the five requirements.
# ⛔ R219 (revert). The powerset run is KEPT but is no longer the default. Under V_SIM the
# continuation collapsed to 70 distinct values over 416 states — a step function, i.e. the
# counting proxy R208 condemned, wearing new clothes — and the ranker, left with a flat V,
# maximised the week and walked straight into R218's zero-cost 동영상 loophole. Neither the
# powerset nor V_SIM is wrong in principle; both are unusable until V discriminates.
# POWERSET=1 restores the 32-branch enumeration. Default is the six 0-or-1 deferral branches.
_REQ_NAMES = ['MR', 'WCiv', 'LHP', 'SciRD', 'Lang']
BRANCHES = (['-'] + ['+'.join(c)
                     for k in range(1, 6)
                     for c in itertools.combinations(_REQ_NAMES, k)]
            if os.environ.get('POWERSET') == '1' else ['-'] + _REQ_NAMES)
TOPN_PER_BRANCH = 1200


def _read_json(path):
    """None if absent, empty or unparseable. The mount permits truncation but not
    deletion, so `reset` leaves ZERO-BYTE files behind — treat those as 'not run'."""
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return None
        return json.load(open(path, encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None


def load_incumbent():
    d = _read_json(INC)
    return d['best'] if d else -1e9


def save_incumbent(v):
    cur = load_incumbent()
    if v > cur:
        json.dump({'best': v}, open(INC, 'w'))


def run_branch(name):
    P, sig, sigs, SIGCODES, code = rank3.build()
    LANGP = [s for s in P['OPEN'] if code(s) in R2.LANG]
    ELEC = [s for s in P['OPEN'] if code(s) not in R2.LANG]
    REQ = {'MR': P['MR'], 'WCiv': P['WCiv'], 'LHP': P['LHP'],
           'SciRD': P['SciRD'], 'Lang': LANGP}
    names = list(REQ)
    print(f"language pool now {len({code(s) for s in LANGP})} courses / "
          f"{len(LANGP)} sections", flush=True)

    rank4.V_REF = rank4.v_ref()
    V_REF = rank4.V_REF
    ITEM_BY_SECTION = {s['c']: rank4.item_of_section(s, code) for s in ELEC}
    json.dump(ITEM_BY_SECTION, open(os.path.join(HERE, 'elective_items.json'), 'w'))

    esig = collections.defaultdict(list)
    for s in ELEC:
        esig[(s['tm'], s['pm'], s['fm'], YEAR_PEN(eff_year(s, code)), s['cr'],
              ITEM_BY_SECTION[s['c']])].append(s)
    # ⛔ R219. RESTORED VERBATIM. R214 rewrote `gains` to use this branch's own nslots-sized
    # states, and rewrote VMAX/the bounds along with it. Every one of those edits was defended
    # as sound or tighter, and together they made the search MISS candidates it used to find:
    # the 'defer nothing' branch dropped from 149.548 to 76.116 with ONE row kept. The scoring
    # is provably intact (dV for the old #1 still reconstructs to 136.687), so the loss is in
    # the search. When a rewrite of a search's bounds cannot be shown correct, it goes back.
    gains = {k: rank4.V((frozenset(), (k, 'FREE'))) - V_REF
             for k in ('FREE', 'ECO1101', 'ME')}
    ekeys = sorted(esig, key=lambda g: -(g[3] + gains.get(g[5], 0.0)))
    ECODES = {g: {code(s) for s in esig[g]} for g in ekeys}

    # ⭐ R212 — Iden: "the scorer doesn't treat the two like C doesn't exist? (both
    # defer / both keep)". BRANCHES held only the SIX single-deferral cases, so 'defer two'
    # was not merely unranked, it was outside the enumeration entirely. A branch name may
    # now be a '+'-joined SET, which is what the CSV already writes on the way out.
    defer = () if name == '-' else tuple(name.split('+'))
    dset = frozenset(defer)
    # ⭐ CHANNEL 2 (R188). Deferring Language does not avoid the hard tier — it makes it
    # PROBABLE. From 2학년 Iden bids mileage for a 2-seat 분반 of the easy tier, won only at
    # the 36 cap in 9 of 13 observed 국제 sections. Charging only the courses actually taken
    # left this out of the ranker entirely, so FINAL_ranked4.csv overstated 'defer Lang' by
    # P_hard x D_LANG. sweep_difficulty.py had both channels; the ranker had one.
    # R190: p_hard_if_deferred now returns a BRACKET. Take the PESSIMISTIC arm — it is the
    # arm that argues against deferring, so if 'defer Language' still wins under it, it wins
    # across the whole bracket. Never take the arm that flatters the incumbent.
    _ph_lo, _ph_hi = DIFF.p_hard_if_deferred()
    defer_dif = -(_ph_hi * DIFF.D_LANG) if 'Lang' in dset else 0.0
    taken = [n for n in names if n not in defer]
    nslots = rank4.N_ACADEMIC - len(taken)

    # ⚠️ R212. The starting incumbent is a GLOBAL bound: it prunes any partial timetable that
    # cannot beat the best score seen in ANY branch. That is correct when the goal is the
    # single winner, and WRONG when the goal is each branch's own top-N — a branch whose
    # ceiling is below the incumbent keeps nothing and `out[0]` raises. NO_INCUMBENT=1 runs
    # the branch on its own merits, which is what a like-for-like branch comparison needs.
    # BRANCH_FLOOR raises the bound deliberately: the pair branches are only needed for their
    # BEST row, and a higher floor prunes far harder. Anything it discards is, by
    # construction, scored below the floor — recorded in the part file so nothing is silent.
    # ⭐ R214. 276.0 was a stand-in ceiling for the weekly score and it is wildly loose.
    # fast_score is monotone decreasing in occupancy (the prune proved in _crowd_curve and
    # reused in semester_sim), so the EMPTY week is its maximum — a real, computed bound.
    # Every branch-and-bound bound below uses it, which is sound and far tighter.
    best = [-1e9 if os.environ.get('NO_INCUMBENT') == '1' else
            float(os.environ.get('BRANCH_FLOOR') or load_incumbent())]
    heap, cnt = [], [0]
    print(f"branch defer={name}  starting incumbent {best[0]:.3f}", flush=True)

    def push(sc, key, det):
        if sc > best[0]:
            best[0] = sc
        if len(heap) < TOPN_PER_BRANCH or sc > heap[0][0]:
            it = (sc, cnt[0], key, det); cnt[0] += 1
            heapq.heappush(heap, it) if len(heap) < TOPN_PER_BRANCH else heapq.heapreplace(heap, it)

    t0 = time.time()
    for ch in P['Chapel'] + [None]:
        ch_t = ch['tm'] if ch else 0
        ch_p = ch['pm'] if ch else 0
        ch_f = ch['fm'] if ch else 0
        ch_c = rank4.CHAPEL_BONUS if ch else rank4.CHAPEL_DEFER
        opts = ('FREE', 'ECO1101', 'ME')
        VMAX = [max(rank4.V((dset, tuple(sorted(t))))
                    for t in itertools.product(opts, repeat=k))
                for k in range(nslots + 1)]
        if ch_c + (VMAX[nslots] - V_REF) + 276.0 < best[0]:
            continue
        for combo in itertools.product(*[REQ[n] for n in taken]):
            tm, pm, fmm, ok = ch_t, ch_p, ch_f, True
            for s in combo:
                if tm & s['tm']:
                    ok = False; break
                tm |= s['tm']; pm |= s['pm']; fmm |= s['fm']
            if not ok:
                continue
            base_codes = {code(s) for s in combo}
            if len(base_codes) < len(combo):
                continue
            cr = sum(s['cr'] for s in combo)
            pen = sum(YEAR_PEN(eff_year(s, code)) for s in combo)
            # ⭐ DIFFICULTY, priced at D_LANG per tier step (difficulty.py). At the default
            # D_LANG = 0 this is identically zero and the model is unchanged — the axis is
            # PRESENT and sweepable rather than absent.
            # GPA gate (R153): difficulty TAKEN THIS SEMESTER is multiplied, because Fall
            # 2026 grades decide December's double-major admission. Deferred difficulty is
            # not, because it lands after the gate. Default multiplier 1.0 => inert.
            dif = (-DIFF.D_LANG * DIFF.GPA_GATE_MULT
                   * sum(DIFF.steps(code(s)) for s in combo)) + defer_dif
            cand = [g for g in ekeys if not (tm & g[0]) and (ECODES[g] - base_codes)]
            bestb = [0.0] * (nslots + 1)
            bb = sorted((g[3] for g in cand), reverse=True)
            for k in range(1, nslots + 1):
                bestb[k] = (sum(bb[:k]) if bb else 0.0) + (VMAX[k] - V_REF)

            def rec(i, k, t, p, f, c, b, used, chosen):
                # ⛔ R217/R219. Two attempts to tighten this ceiling both went wrong:
                # `fast_score` is NOT monotone (hole-filling), and `week_value` — which IS
                # monotone — still cost the search candidates it previously found. The loose
                # constant stands until a replacement is verified against a known ranking.
                wub = 276.0
                if b + bestb[k] + pen + dif + ch_c + wub < best[0]:
                    return
                if k == 0:
                    if not (17.0 <= c <= 21.0):
                        return
                    items = tuple(sorted(g[5] for g in chosen))
                    sc, det = fast_score(t, p, f)
                    sc += b + pen + dif + ch_c + (rank4.V((dset, items)) - V_REF)
                    push(sc, (tuple(s['c'] for s in combo), ch['c'] if ch else None,
                              tuple(chosen), defer), det)
                    return
                for j in range(i, len(cand)):
                    g = cand[j]
                    if b + g[3] + bestb[k - 1] + pen + dif + ch_c + wub < best[0]:
                        break
                    if t & g[0]:
                        continue
                    if not (ECODES[g] - used):
                        continue
                    if c + g[4] + 3.0 * (k - 1) > 21.0:
                        continue
                    rec(j + 1, k - 1, t | g[0], p | g[1], f | g[2], c + g[4], b + g[3],
                        used | ECODES[g], chosen + (g,))
            rec(0, nslots, tm, pm, fmm, cr, 0.0, base_codes, ())

    save_incumbent(best[0])
    out = sorted(heap, key=lambda x: -x[0])
    if not out:
        # R212: with a global incumbent as the floor, a branch whose CEILING is below it
        # legitimately keeps nothing. Say so and write an empty part rather than IndexError.
        json.dump({'D_LANG': DIFF.D_LANG, 'rows': [], 'floor': best[0]},
                  open(os.path.join(STATE, f'part_{name}.json'), 'w'))
        print(f"branch defer={name}: EMPTY — ceiling below the floor {best[0]:.3f}", flush=True)
        return
    rec_out = []
    DN = '월화수목금'
    for sc, _n, key, det in out:
        req, chp, el, df = key
        rec_out.append(dict(score=round(sc, 3), deferred='+'.join(df) or '-',
                            chapel=chp or '-', requirements=list(req),
                            electives=[esig[g][0]['c'] for g in el],
                            elective_items=[g[5] for g in el],
                            free_days=''.join(DN[d] for d in sorted(det['free'])),
                            # restored 2026-08-09: dropping these made R174 uncheckable
                            # (test_retired.py reported 'cannot be checked' for a whole
                            # session). An output that loses a column silently disables a
                            # test that depends on it.
                            early1=det.get('e1'), lunch_fail=det.get('lf'),
                            dinner_fail=det.get('df', det.get('dinner', 0)),
                            late=det.get('late'),
                            runs='+'.join(map(str, det.get('runs', []))),
                            holes='+'.join(map(str, det.get('holes', []))),
                            credits=sum(g[4] for g in el) + 3.0 * len(req)))
    json.dump({'D_LANG': DIFF.D_LANG, 'rows': rec_out},
              open(os.path.join(STATE, f'part_{name}.json'), 'w'), ensure_ascii=False)
    print(f"branch defer={name}: {len(rec_out)} kept, best {out[0][0]:.3f}, "
          f"{time.time()-t0:.0f}s", flush=True)


def merge():
    # ⛔ R216. An EMPTY part is legitimate (a branch whose ceiling is under the incumbent),
    # which is exactly why an empty part must be LOUD. A timed-out re-run of the winning
    # branch left `rows: []` behind, merge accepted it without a word, and the global optimum
    # silently vanished from FINAL_ranked4.csv — #1 reverted to a branch scoring 37 points
    # lower. Every merge now prints the row count and best score of every branch, and flags
    # any branch that is empty while claiming a floor below the merged winner.
    allr = []
    missing = [b for b in BRANCHES
               if _read_json(os.path.join(STATE, f'part_{b}.json')) is None]
    if missing:
        print(f"❌ REFUSING TO MERGE — branches not run: {missing}")
        sys.exit(1)
    dls = set()
    _report = []
    for b in BRANCHES:
        part = _read_json(os.path.join(STATE, f'part_{b}.json'))
        dls.add(part['D_LANG'])
        allr += part['rows']
        _report.append((b, len(part['rows']),
                        max((r['score'] for r in part['rows']), default=None),
                        part.get('floor')))
    if len(dls) > 1:
        print(f"❌ REFUSING TO MERGE — branches scored at different D_LANG: {sorted(dls)}")
        sys.exit(1)
    print(f"all branches scored at D_LANG = {dls.pop()}")
    allr.sort(key=lambda r: -r['score'])
    _win = allr[0]['score'] if allr else float('-inf')
    print(f"{'branch':22s} {'rows':>5} {'best':>9}  {'floor':>9}")
    for b, n, bs, fl in _report:
        warn = ''
        if n == 0 and fl is not None and fl < _win - 1e-9:
            warn = '   ⛔ EMPTY BUT ITS FLOOR IS BELOW THE WINNER — re-run this branch'
        print(f"  {b:20s} {n:5d} {('%9.3f' % bs) if bs is not None else '        -'}"
              f"  {('%9.3f' % fl) if fl is not None else '        -'}{warn}")
    with open(os.path.join(HERE, 'FINAL_ranked4.csv'), 'w', newline='',
              encoding='utf-8-sig') as f:
        wr = csv.writer(f)
        wr.writerow(['rank', 'score', 'deferred', 'chapel', 'requirements', 'electives',
                     'elective_items', 'credits', 'free_days', 'early1', 'lunch_fail',
                     'dinner_fail', 'late', 'runs', 'holes'])
        for i, r in enumerate(allr, 1):
            wr.writerow([i, r['score'], r['deferred'], r['chapel'],
                         ' '.join(r['requirements']), ' '.join(r['electives']),
                         ' '.join(r['elective_items']), r['credits'], r['free_days'],
                         r.get('early1'), r.get('lunch_fail'), r.get('dinner_fail'),
                         r.get('late'), r.get('runs'), r.get('holes')])
    print(f"merged {len(allr)} rows -> FINAL_ranked4.csv")
    for i, r in enumerate(allr[:6], 1):
        print(f"  {i} {r['score']:8.3f} defer={r['deferred']:6s} {r['free_days']:5s} | "
              f"{' '.join(c[:7] for c in r['requirements'])} | "
              f"{' '.join(c[:7] for c in r['electives'])}")


if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else 'merge'
    if a == 'reset':
        for f in os.listdir(STATE):
            open(os.path.join(STATE, f), 'w').close()   # truncate; rm is not permitted
        print("state cleared (files truncated)")
    elif a == 'merge':
        merge()
    else:
        run_branch(a)
