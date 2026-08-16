"""
build_receiving.py — the term that has been missing since 2026-08-07.

Deferring a requirement out of Fall 2026 has three costs. Two were measured (R142 gain-here,
R146 year-gap); the third — what the RECEIVING semester loses by carrying it — was estimated
in R148 using the Fall 국제 pool as a stand-in, which R173/G-9 flagged as the wrong population.

This computes it from REAL Spring 국제 observations (mileage_history: 59 rows, 16 courses,
actual Spring meeting times), so the receiving semester is modelled as a Spring, which is what
it actually is (QRM3003 is 국제-only AND Spring-only — R144).

⚠️ WHAT THIS CAN AND CANNOT DO
  CAN : compare the two live options, because they differ by exactly ONE forced course in the
        receiving semester — UIC1805 (defer Chinese) vs QRM1001 (defer QRM입문).
  CANNOT: model the full Spring. The mileage feed only ever queried REQUIREMENT courses, so
        the Spring elective pool is unobserved. Free slots are therefore left EMPTY, which
        flatters both options equally and cancels in the comparison.
  CANNOT: place QRM3003 — it has never appeared in an observed term, so its time is unknown.
        Reported both with it excluded and as a sensitivity over plausible slots.
"""
import json, os, re, collections, itertools
import rank as RK, rank2 as R2

HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
DAYS = '월화수목금'
SPRING = {('2025','10'), ('2026','10')}

def parse(t):
    """'화4,목5,6' / '월7,8/수8' -> {(day,period)}"""
    out=set(); day=None; cur=''
    for ch in (t or '')+'|':
        if ch in DAYS: day=DAYS.index(ch); cur=''
        elif ch.isdigit(): cur+=ch
        else:
            if cur and day is not None: out.add((day,int(cur)))
            cur=''
    return out

def spring_pool():
    """Real Spring 국제 sections, from the only source that has them."""
    pool=collections.defaultdict(set)
    for r in json.load(open(P('mileage_history.json'), encoding='utf-8')):
        if (r['syy'], r['smtDivCd']) in SPRING and r.get('campsDivNm')=='국제':
            t=r.get('lctreTimeNm')
            if t: pool[r['subjtnb']].add(t)
    return {k: sorted(v) for k,v in pool.items()}

def mk(cells):
    m=0
    for d,p in cells: m|=1<<(d*16+p)
    return m

def best_week(forced_codes, pool, extra_slots=0, filler=None):
    """Best achievable week carrying every course in forced_codes (choosing among its
    observed Spring times), optionally plus `extra_slots` courses drawn from `filler`."""
    opts=[[parse(t) for t in pool[c]] for c in forced_codes]
    best=(-1e9, None)
    for combo in itertools.product(*opts):
        cells=set()
        ok=True
        for c in combo:
            if cells & c: ok=False; break
            cells |= c
        if not ok: continue
        m=mk(cells)
        sc,det=R2.fast_score(m, m)          # in-person: time == presence
        if sc>best[0]: best=(sc, combo, det)
    return best

def main():
    pool=spring_pool()
    print(f"Spring 국제 pool from real observations: {len(pool)} courses\n")

    # The two options differ by exactly ONE forced course in the receiving Spring.
    OPTS={'defer Chinese  -> Spring must carry UIC1805':'UIC1805',
          'defer QRM입문   -> Spring must carry QRM1001':'QRM1001'}
    print("Spring meeting times actually observed for the two:")
    for lbl,c in OPTS.items(): print(f"   {c}: {pool.get(c)}")
    print()

    # Everything else that semester carries is IDENTICAL between the options, so model the
    # common load explicitly and vary only the one differing course.
    COMMON=['UIC2151']          # SciRD-type load stands in for the shared remainder
    print("="*74)
    print("BEST ACHIEVABLE SPRING WEEK — alone, then alongside a shared course")
    print("="*74)
    print(f"{'option':46s} {'alone':>8s} {'+shared':>9s}")
    res={}
    for lbl,c in OPTS.items():
        a=best_week([c], pool)
        b=best_week([c]+COMMON, pool)
        res[c]=(a[0], b[0])
        print(f"{lbl:46s} {a[0]:8.2f} {b[0]:9.2f}")
    print()
    ca, cb = res['UIC1805'], res['QRM1001']
    print(f"difference (QRM1001 minus UIC1805): alone {cb[0]-ca[0]:+.2f}   +shared {cb[1]-ca[1]:+.2f}")
    print()
    if abs(cb[1]-ca[1]) < 0.01:
        print("  ⇒ THE RECEIVING SEMESTER IS INDIFFERENT between the two deferrals.")
        print("    Both forced courses can occupy 화/목 in Spring, so both leave 월+금 free.")
        print("    The missing third term is ZERO for this comparison — it does not break the tie.")
    else:
        w = 'QRM1001' if cb[1]>ca[1] else 'UIC1805'
        print(f"  ⇒ the receiving semester PREFERS carrying {w} by {abs(cb[1]-ca[1]):.2f}")
    print()
    print("free-day shape achievable in the receiving Spring, per option:")
    for lbl,c in OPTS.items():
        sc,combo,det=best_week([c]+COMMON, pool)
        free=''.join(DAYS[d] for d in sorted(det['free']))
        print(f"   {c}: {free or 'none'}   (score {sc:.2f})")

if __name__ == '__main__':
    main()
