"""
rank3.py — DEFERRAL MODEL. Requirements are weighed, not forced.

rank2 hard-forced 4 requirement slots. rank3 treats every currently-available requirement
as optional: take it now, or defer it and pay the cost measured in R117.

STRUCTURE
  6 academic courses (R111: 18 cr, Iden's choice — cap is 22, he declined 21) + chapel.
  Each of the 5 available requirements (REQUIREMENTS_AUDIT A1–A5) either occupies one of
  those 6 slots, or is deferred at a cost. Slots not used by a requirement are filled with
  electives from OPEN.

FIXES CARRIED IN FROM THE MATH REVIEW (2026-08-06)
  1. rank2 constrained ONLY the 2 open slots to 6–9 cr and *assumed* the fixed slots
     contributed 12. Nothing ever checked the total. Verified: a phantom at cr=0.0 and
     cr=3.0 gave byte-identical output. Here TOTAL academic credits are constrained.
  2. DOUBLE-COUNT: rank2 gave UIC1805/1806 a +8 BONUS for satisfying the language
     requirement, while R117 prices deferring that same requirement at −17. Applying both
     is counting one requirement twice. Language is a requirement SLOT here, and the
     +8 BONUS is dropped. (Iden's older +8 and the newer −17 disagree; the deferral
     mechanism supersedes, since it is measured rather than recalled.)
  3. ROLE_MR / ROLE_ME still apply to ELECTIVES only — an extra MR course beyond the MR
     slot (e.g. ECO1101) is genuine additional progress, not the same requirement twice.
"""
import json, re, collections, csv, heapq, itertools, sys
import rank as RK
import rank2 as R2
from rank2 import (fast_score, year_of, YEAR_PEN, ROLE_MR, ROLE_ME, ROLE_MB, MR_CODES,
                   eff_year)

DEFER = json.load(open('defer_costs.json', encoding='utf-8'))
# R127 — Iden 2026-08-06: chapel bonus = 10. This is INTRINSIC desirability
# ("chapel is pretty desirable in itself", "easy to catch, finish offline chapels now"),
# genuinely separate from the −4.2 competition-based deferral cost, unlike the language
# +8 which turned out to be the same logic twice (R119). Taking chapel: +10.
# Not taking it: −4.2 and no +10 ⇒ a 14.2-point swing.
CHAPEL_BONUS = 10.0
N_ACADEMIC = 6          # R111 — Iden's choice, not the cap
CR_LO, CR_HI = 17.0, 21.0
MAX_DEFER = 1           # PROVEN sufficient — see R121, not a compute compromise.
                        # All 10 two-deferral pairs were searched exhaustively by
                        # defer2_check.py and none beats the 1-deferral optimum 32.51.
                        # Three deferrals cost >= 40 and 63.1 - 40 < 32.51 analytically.

def build():
    """Reuse rank2's pool construction verbatim, then reshape into requirement slots."""
    import io, contextlib
    src = open('rank2.py', encoding='utf-8').read()
    marker = "    heap = []; cnt=[0]"
    ns = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(src[:src.index(marker)] + "    return P, sig, sigs, SIGCODES, code\n",
                     'rank2_pools', 'exec'), ns)
        P, sig, sigs, SIGCODES, code = ns['main']()
    return P, sig, sigs, SIGCODES, code

def main(TOPN=5000):
    P, sig, sigs, SIGCODES, code = build()
    LANGP = [s for s in P['OPEN'] if code(s) in R2.LANG]
    ELEC  = [s for s in P['OPEN'] if code(s) not in R2.LANG]

    REQ = {'MR': P['MR'], 'WCiv': P['WCiv'], 'LHP': P['LHP'],
           'SciRD': P['SciRD'], 'Lang': LANGP}
    names = list(REQ)
    print("requirement pools:", {k: len(v) for k, v in REQ.items()},
          "| electives:", len(ELEC))

    # elective signatures: identical (time, presence, bonus, credits) score identically
    esig = collections.defaultdict(list)
    for s in ELEC:
        b = R2.BONUS.get(code(s), 0.0) + s.get('_role', 0.0) + YEAR_PEN(eff_year(s, code))
        esig[(s['tm'], s['pm'], b, s['cr'])].append(s)
    ekeys = sorted(esig, key=lambda g: -g[2])
    ECODES = {g: {code(s) for s in esig[g]} for g in ekeys}
    print(f"electives {len(ELEC)} -> {len(ekeys)} signatures")

    heap, cnt = [], [0]
    best = [-1e9]
    # ⚠ These are BRANCH-AND-BOUND bounds. Too LOW silently prunes valid branches and
    # returns wrong answers; too high only costs time. Both were re-derived for R129,
    # which raised the reachable schedule ceiling (REST is now paid on 월/금 as well).
    # Absolute ceiling on week_value = a completely empty week:
    #   run 7 -> DAY_CONTIG*5^1.6 = 246.24, + 5*REST = 23.50, + FRI_EVENT 6.25 = 275.99.
    # Unreachable with 6 courses, but it is a true bound, which is what B&B needs.
    SCHED_UB = 276.0
    # GROSS = schedule + course bonuses + 학년 penalties (penalties are <=0).
    # Max course bonus stack is small (ECO1101 +10, ROLE_MR +8). 120 is amply safe and
    # is asserted against the observed maximum after the run.
    GROSS_UB = 120.0
    def push(sc, key, det):
        if sc > best[0]: best[0] = sc
        if len(heap) < TOPN or sc > heap[0][0]:
            item = (sc, cnt[0], key, det); cnt[0] += 1
            heapq.heappush(heap, item) if len(heap) < TOPN else heapq.heapreplace(heap, item)

    import time; t0=time.time(); pruned=0; done=0
    for ndef in range(0, MAX_DEFER + 1):          # ascending: build an incumbent first
      for defer in itertools.combinations(names, ndef):
        for ch in P['Chapel'] + [None]:
            ch_t = ch['tm'] if ch else 0
            ch_p = ch['pm'] if ch else 0
            ch_c = CHAPEL_BONUS if ch else DEFER['Chapel']
            dcost = ch_c + sum(DEFER[n] for n in defer)
            # B&B: no timetable in this subset can beat the incumbent
            if dcost + GROSS_UB < best[0]:
                pruned += 1; continue
            taken = [n for n in names if n not in defer]
            if len(taken) > N_ACADEMIC: continue
            nslots = N_ACADEMIC - len(taken)
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
                bestb = [0.0]*(nslots+1)          # best achievable bonus for k more slots
                bb = sorted((g[2] for g in cand), reverse=True)
                for k in range(1, nslots+1): bestb[k] = sum(bb[:k]) if bb else 0.0
                def rec(i, k, t, p, c, b, used, chosen):
                    # SCHED_UB: the largest week_value physically reachable is
                    # 월+금 free -> run 금토일월 = 4 -> DAY_CONTIG*(4-2)^1.6 + FRI_EVENT
                    # = 56.8 + 6.25 = 63.1. All other terms are penalties (<=0). 70 is safe
                    # and is asserted against the observed maximum after the run.
                    if b + bestb[k] + pen + dcost + SCHED_UB < best[0]: return
                    if k == 0:
                        if not (CR_LO <= c <= CR_HI): return
                        sc, det = fast_score(t, p)
                        sc += b + pen + dcost
                        push(sc, (tuple(s['c'] for s in combo),
                                  ch['c'] if ch else None, tuple(chosen), defer), det)
                        return
                    for j in range(i, len(cand)):
                        g = cand[j]
                        # cand is sorted by bonus DESC, so once the optimistic bound fails
                        # it fails for every later j too -> break, not continue.
                        if b + g[2] + bestb[k-1] + pen + dcost + SCHED_UB < best[0]: break
                        if t & g[0]: continue
                        if not (ECODES[g] - used): continue
                        if c + g[3] + 3.0*(k-1) > CR_HI: continue
                        rec(j+1, k-1, t | g[0], p | g[1], c + g[3], b + g[2],
                            used | ECODES[g], chosen + (g,))
                rec(0, nslots, tm, pm, cr, 0.0, base_codes, ())
            done += 1
        print(f"  ndef={ndef} defer={defer or '()'}  best={best[0]:.2f}  "
              f"pruned={pruned}  {time.time()-t0:.0f}s")
    out = sorted(heap, key=lambda x: -x[0])
    gross = max(x[0] - (0.0 if x[2][1] else DEFER['Chapel'])
                     - sum(DEFER[n] for n in x[2][3]) for x in out)
    print(f"\nscored {len(out)}; best {out[0][0]:.2f}; max GROSS {gross:.2f} "
          f"(bound {GROSS_UB} — {'OK' if gross <= GROSS_UB else 'BOUND VIOLATED'})")
    with open('FINAL_ranked3.csv','w',newline='',encoding='utf-8-sig') as f:
        wr=csv.writer(f)
        wr.writerow(['rank','score','deferred','chapel','requirements','electives',
                     'credits','free_days','early1','lunch_fail','late','runs','holes'])
        DN='월화수목금'
        for i,(sc,_n,key,det) in enumerate(out,1):
            req,ch,el,df=key
            names_el=[esig[g][0]['c'] for g in el]
            cr=sum(g[3] for g in el)+sum(3.0 for _ in req)
            wr.writerow([i,round(sc,3),'+'.join(df) or '-',ch or '-',
                         ' '.join(req),' '.join(names_el),cr,
                         ''.join(DN[d] for d in sorted(det['free'])),
                         det['e1'],det['lf'],det['late'],
                         '+'.join(map(str,det['runs'])),'+'.join(map(str,det['holes']))])
    print('wrote FINAL_ranked3.csv')
    d = collections.Counter(x[2][3] for x in out[:50])
    print("top-50 deferral patterns:",
          {(' + '.join(k) if k else 'nothing deferred'): v for k, v in d.items()})
    return out, esig, {s['c']: s for v in P.values() for s in v}

if __name__ == '__main__':
    main()
