# -*- coding: utf-8 -*-
"""
rank4.py — the ranker with a COMPUTED continuation value instead of fitted constants.

WHAT CHANGED FROM rank3
-----------------------
rank3 scored a timetable as:
      week  +  Σ role bonuses  +  Σ year penalties  +  DEFER[deferred requirement]
where `role` (8.0 / 2.29 / 0.36) and `DEFER` (7 values) were static numbers — the first
a substitutability ratio, the second R117's fit to two anchors on a superseded scale.

rank4 scores it as:
      week  +  Σ year penalties  +  [ V(remainder) − V(reference) ]

`V` is computed by continuation.py: the best feasible placement of everything Fall 2026
leaves undone into the six semesters that follow, given campus, term, year and credit
constraints. Both `role` and `DEFER` are GONE — not retuned, removed. Their two jobs
(quota progress is worth something; deferring costs something) are now one quantity, and
it is derived rather than set.

⚠️ THE SCALE IS NOT COMPARABLE TO rank3's. A rank3 score of 21.795 and a rank4 score are
different objects (DESIGN_v2 §5). Never put them in the same column.

WHY A NEW FILE
--------------
`rank2.py` cannot be reordered or reformatted above the line `    heap = []; cnt=[0]`,
because rank3.build() execs its source text up to that literal string (INDEX trap #1).
rank4 imports rank3.build() and leaves both files untouched.
"""
import json, collections, csv, heapq, itertools, time, os, functools
import rank as RK
import rank2 as R2
import rank3
import difficulty as _DIFF

# ⭐ F3 (external audit): the widened language pool (R166/R187) reached the ranker ONLY
# because rank4_branch.py set R2.LANG at runtime. `rank2.py:27` still holds the 2-course
# literal, so ANY consumer importing rank2 without that override silently got the narrow
# pool — convention, not construction. Setting it here means importing rank4 is enough.
R2.LANG = set(_DIFF.LANG_ALL)

from rank2 import fast_score, year_of, YEAR_PEN, eff_year

from continuation import solve
from defer_value2 import remainder_after, ALL_REQS, ELECTIVE_TO_ITEM

HERE = os.path.dirname(os.path.abspath(__file__))

CHAPEL_BONUS = 10.0     # R127 — intrinsic desirability, genuinely separate from placement
CHAPEL_DEFER = -4.2     # R117's chapel term; chapel is not in the continuation ledger as
                        # a scarcity (3 passes over 6 semesters never binds), so its value
                        # stays elicited. Flagged in MODEL.md.
N_ACADEMIC = 6
CR_LO, CR_HI = 17.0, 21.0
# ⛔ R214. This was `1`, on the strength of R121's proof — which says of itself: "this proof
# is incumbent-dependent and must be re-run whenever the pool or the optimum changes."
# The objective has changed TWICE since (rank4's computed V, then R208's simulated V), so the
# proof expired and the cap became a PREDECISION. Iden: "Every possibility should just be
# numerically computed, not predecided." Default is now the full 5.
MAX_DEFER = int(os.environ.get('MAX_DEFER', 5))

# --- continuation value, memoised -------------------------------------------------
_VC = {}
_VSIM = None


def _vsim_table():
    """⭐ R214. The SIMULATED continuation (continuation_sim), precomputed per STATE.

    Iden: "are you saying you didn't implement the logic yet? Because #1 shows up as A".
    Correct — and the reason I thought it could not be wired in was wrong. V is memoised on
    (deferral subset, elective item multiset), and the items take only three values, so the
    key space is 417 states, not thousands of candidates. One local search per state,
    cached to disk by build_vsim_table.py, and the ranker optimises the CORRECTED objective.

    V_SIM=1 turns it on. A missing key RAISES — it must never fall back to the proxy
    silently, which is the failure mode that let FINAL_ranked4.csv disagree with the model.
    """
    global _VSIM
    if _VSIM is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vsim_table.json')
        _VSIM = (json.load(open(p, encoding='utf-8'))
                 if os.environ.get('V_SIM') == '1' and os.path.exists(p) else {})
    return _VSIM


def V(state):
    """state = (frozenset deferred requirement names, tuple of sorted elective item keys)"""
    if state in _VC:
        return _VC[state]
    tab = _vsim_table()
    if tab:
        k = ('+'.join(sorted(state[0])) or '-') + '|' + '+'.join(state[1])
        if k not in tab:
            raise KeyError(f"V_SIM=1 but state {k} is not in vsim_table.json — "
                           f"re-run build_vsim_table.py. Refusing to fall back to the proxy.")
        _VC[state] = tab[k]
        return tab[k]
    defer, ekeys = state
    taken = [r for r in ALL_REQS if r not in defer]
    rem = remainder_after(taken, [], chapel=True)
    for k in ekeys:
        rem[k] = max(0, rem[k] - 1)
    v, _plan = solve(rem)
    _VC[state] = v
    return v


# ⭐ R214. The reference state is an additive constant — any FIXED state works, provided the
# SAME one is used everywhere. ('FREE','FREE') is not a reachable state under V_SIM (defer
# nothing leaves ONE elective slot, not two), and continuation_sim correctly reports it
# INFEASIBLE (-1e6). Under V_SIM the reference is the reachable ('FREE',); the proxy keeps its
# historical ('FREE','FREE') so old numbers stay comparable.
REF_STATE = ((frozenset(), ('FREE',)) if os.environ.get('V_SIM') == '1'
             else (frozenset(), ('FREE', 'FREE')))


def v_ref():
    return V(REF_STATE)

# ⛔ 2026-08-09 — DO NOT map electives to ledger items from a hand-written code list.
# I did exactly that on the first pass: `ELECTIVE_TO_ITEM` claimed ECO1103/ECO1104 were
# QRM Major Electives, which OVERRODE the authoritative field. The pool says
# ECO1104-07-00 has qcat=None and _qrm_me=False — QRM does not list that section — and the
# hand list silently promoted it, manufacturing a #1 that deferred Intro to QRM. That is
# R102's error run backwards (using another department's view instead of QRM's own), and
# VERIFY 22b had it parked as an OPEN question the whole time.
# The item a section advances is READ FROM THE SECTION.
# ⭐ THE SECOND-MAJOR CHANNEL (R185, the half R183 did NOT close).
# R183 correctly demoted ECO1103/ECO1104 as QRM Major Electives — QRM does not list those
# sections. But R64 records that 원론 are 경제학 이중전공 필수 IN THEIR OWN RIGHT. If Iden
# double-majors in Economics they advance the 36-credit DM quota, which the ledger carries
# as 12 abstract 신촌 courses. Same for ECO1101, whose BONUS_ECON2ND was deleted with the
# role bonuses and never re-expressed inside V.
#
# The major is a DECEMBER decision, so DM_MAJOR is None and this is currently inert — the
# mechanism exists and the model is numerically unchanged, exactly as with difficulty.D_LANG
# before it was elicited. Set it to 'ECO' to see the consequence.
DM_MAJOR = None          # None | 'ECO' | 'MATH' | 'CS'   ⏳ decided in December (R147)
DM_ADVANCING = {
    'ECO': {'ECO1103', 'ECO1104', 'ECO1101'},   # 경제학 이중전공 필수 (R64)
}


def item_of_section(s, code):
    """Which ledger item does taking this section advance? Data, not a guess."""
    c0 = code(s)
    if DM_MAJOR and c0 in DM_ADVANCING.get(DM_MAJOR, ()) and c0 != 'ECO1101':
        return 'DM'                            # advances the second major, not ME
    if c0 == 'ECO1101':
        return 'ECO1101'                       # MR, and reachable at 국제 this Fall
    if s.get('qcat') == 'MR' or c0 in R2.MR_CODES:
        return 'ECO1101' if c0 == 'ECO1101' else 'FREE'   # no other MR is reachable now
    if s.get('qcat') == 'ME' or s.get('_qrm_me'):
        return 'ME'
    return 'FREE'

# reference point: all five requirements taken, both spare slots on free electives.
# Only DIFFERENCES matter, exactly as with the week score (MODEL.md §0).
V_REF = None


def main(TOPN=5000):
    global V_REF
    P, sig, sigs, SIGCODES, code = rank3.build()
    LANGP = [s for s in P['OPEN'] if code(s) in R2.LANG]
    ELEC  = [s for s in P['OPEN'] if code(s) not in R2.LANG]
    REQ = {'MR': P['MR'], 'WCiv': P['WCiv'], 'LHP': P['LHP'],
           'SciRD': P['SciRD'], 'Lang': LANGP}
    names = list(REQ)
    print("requirement pools:", {k: len(v) for k, v in REQ.items()},
          "| electives:", len(ELEC), flush=True)

    V_REF = v_ref()
    print(f"V_REF = {V_REF:.3f}   (all 5 requirements taken, 1 spare slot free elective)")

    # how much continuation value each elective ITEM class is worth, measured once
    gains = {}
    for k in ('FREE', 'ECO1101', 'ME'):
        gains[k] = V((frozenset(), (k, 'FREE'))) - V_REF
    print("continuation gain by elective class:",
          {k: round(v, 3) for k, v in gains.items()}, flush=True)
    MAX_EGAIN = max(gains.values())

    # elective signatures — role bonus REMOVED (it is now inside V); year penalty kept
    global ITEM_BY_SECTION
    ITEM_BY_SECTION = {s['c']: item_of_section(s, code) for s in ELEC}
    json.dump(ITEM_BY_SECTION, open(os.path.join(HERE, 'elective_items.json'), 'w'))
    _n = collections.Counter(ITEM_BY_SECTION.values())
    print("elective -> ledger item, read from the pool:", dict(_n), flush=True)

    esig = collections.defaultdict(list)
    for s in ELEC:
        b = YEAR_PEN(eff_year(s, code))
        esig[(s['tm'], s['pm'], b, s['cr'], ITEM_BY_SECTION[s['c']])].append(s)
    ekeys = sorted(esig, key=lambda g: -(g[2] + gains.get(g[4], 0.0)))
    ECODES = {g: {code(s) for s in esig[g]} for g in ekeys}
    print(f"electives {len(ELEC)} -> {len(ekeys)} signatures", flush=True)

    heap, cnt, best = [], [0], [-1e9]
    SCHED_UB = 276.0
    YEAR_UB = 0.0            # year penalties are <= 0
    def push(sc, key, det):
        if sc > best[0]: best[0] = sc
        if len(heap) < TOPN or sc > heap[0][0]:
            item = (sc, cnt[0], key, det); cnt[0] += 1
            heapq.heappush(heap, item) if len(heap) < TOPN else heapq.heapreplace(heap, item)

    t0 = time.time(); pruned = 0
    for ndef in range(0, MAX_DEFER + 1):
      for defer in itertools.combinations(names, ndef):
        dset = frozenset(defer)
        for ch in P['Chapel'] + [None]:
            ch_t = ch['tm'] if ch else 0
            ch_p = ch['pm'] if ch else 0
            ch_c = CHAPEL_BONUS if ch else CHAPEL_DEFER
            taken = [n for n in names if n not in defer]
            if len(taken) > N_ACADEMIC: continue
            nslots = N_ACADEMIC - len(taken)
            # optimistic: every spare slot takes the best-paying elective class
            # exact best continuation reachable from this branch: try every item tuple
            import itertools as _it
            _opts = ('FREE', 'ECO1101', 'ME')
            VMAX = [max(V((dset, tuple(sorted(t)))) for t in _it.product(_opts, repeat=k))
                    for k in range(nslots + 1)]
            vmax = VMAX[nslots]
            if ch_c + (vmax - V_REF) + SCHED_UB + YEAR_UB < best[0]:
                pruned += 1; continue
            # (A recursive conflict-pruned combo builder was tried here and was ~1.8x
            #  SLOWER — the requirement pools rarely conflict, so the generator overhead
            #  per combo exceeded what the pruning saved. itertools.product stands.)
            for combo in itertools.product(*[REQ[n] for n in taken]):
                tm = ch_t; pm = ch_p; ok = True
                for s in combo:
                    if tm & s['tm']: ok = False; break
                    tm |= s['tm']; pm |= s['pm']
                if not ok: continue
                base_codes = {code(s) for s in combo}
                if len(base_codes) < len(combo): continue
                cr = sum(s['cr'] for s in combo)
                pen = sum(YEAR_PEN(eff_year(s, code)) for s in combo)
                cand = [g for g in ekeys if not (tm & g[0]) and (ECODES[g] - base_codes)]
                bestb = [0.0]*(nslots+1)
                bb = sorted((g[2] for g in cand), reverse=True)
                for k in range(1, nslots+1):
                    # tight: the exact best continuation reachable with k slots left,
                    # not MAX_EGAIN*k, which ignores the convexity of the crowding term
                    bestb[k] = (sum(bb[:k]) if bb else 0.0) + (VMAX[k] - V_REF)
                def rec(i, k, t, p, c, b, used, chosen):
                    if b + bestb[k] + pen + ch_c + SCHED_UB < best[0]: return
                    if k == 0:
                        if not (CR_LO <= c <= CR_HI): return
                        items = tuple(sorted(g[4] for g in chosen))
                        v = V((dset, items)) - V_REF
                        sc, det = fast_score(t, p)
                        sc += b + pen + ch_c + v
                        push(sc, (tuple(s['c'] for s in combo),
                                  ch['c'] if ch else None, tuple(chosen), defer), det)
                        return
                    for j in range(i, len(cand)):
                        g = cand[j]
                        if b + g[2] + bestb[k-1] + pen + ch_c + SCHED_UB < best[0]: break
                        if t & g[0]: continue
                        if not (ECODES[g] - used): continue
                        if c + g[3] + 3.0*(k-1) > CR_HI: continue
                        rec(j+1, k-1, t | g[0], p | g[1], c + g[3], b + g[2],
                            used | ECODES[g], chosen + (g,))
                rec(0, nslots, tm, pm, cr, 0.0, base_codes, ())
        print(f"  ndef={ndef} defer={defer or '()'}  best={best[0]:.2f}  "
              f"pruned={pruned}  {time.time()-t0:.0f}s", flush=True)

    out = sorted(heap, key=lambda x: -x[0])
    with open(os.path.join(HERE, 'FINAL_ranked4.csv'), 'w', newline='',
              encoding='utf-8-sig') as f:
        wr = csv.writer(f)
        wr.writerow(['rank','score','deferred','chapel','requirements','electives',
                     'elective_items','credits','free_days','early1','lunch_fail','late',
                     'runs','holes'])
        DN = '월화수목금'
        for i, (sc, _n, key, det) in enumerate(out, 1):
            req, ch, el, df = key
            names_el = [esig[g][0]['c'] for g in el]
            cr = sum(g[3] for g in el) + sum(3.0 for _ in req)
            wr.writerow([i, round(sc,3), '+'.join(df) or '-', ch or '-',
                         ' '.join(req), ' '.join(names_el),
                         ' '.join(g[4] for g in el), cr,
                         ''.join(DN[d] for d in sorted(det['free'])),
                         det['e1'], det['lf'], det['late'],
                         '+'.join(map(str, det['runs'])), '+'.join(map(str, det['holes']))])
    print(f"\nscored {len(out)}; best {out[0][0]:.3f}; wrote FINAL_ranked4.csv")
    print(f"V cache: {len(_VC)} distinct remainder states")
    d = collections.Counter(x[2][3] for x in out[:50])
    print("top-50 deferral patterns:",
          {(' + '.join(k) if k else 'nothing deferred'): v for k, v in d.items()})
    return out


if __name__ == '__main__':
    main()
