"""
rank.py — final scorer for Fall 2026. All weights traceable to Iden's answers.
Data: canonical_2026F.json (R51/R52/R54)  |  Eligibility: R61  |  Chapel: R58
TRIP value uses the PRESENCE mask; REST value uses the TIME mask (R129, supersedes D-10).
Free-day value is CYCLIC (R57): week = Z7, weekend always free.
NOTE: run_value()/score() below are LEGACY (rank2.week_value is the live scorer).
"""
import json, re, collections, csv

# ---------------- WEIGHTS (anchor: one 1교시 day = 10 penalty points) ----------------
W_E1      = -10.0   # day starts 1교시            [elicited: anchor]
W_E2      =  -5.0   # day starts 2교시            [provisional, never re-elicited]
W_LUNCH   =  -6.0   # day with 3·4·5교시 all busy  [fitted: lunch+marathon=13.75]
# Consecutive-class run of L periods (= L hours, R72). Iden: "convex-like but generally
# all lower than steady; 4h = −8 still holds."  steady would be −8·(L−3); this curve is
# convex yet stays below it for every L up to 13 (the longest observed run).
MARATHON  = lambda L: -(8.0 + 0.8*(L-4)**2) if L >= 4 else 0.0
# How late a day ENDS. Iden 2026-08-05, revised: "17:50 should start at −1, 21:50
# should be −10, 22:50 bigger than −10."  Solve −(L−8)^p through those two points:
# p = log10/log5 = 1.4307.  Threshold moves to 9교시 (ends 17:50).
LATE      = lambda last: -((last - 8) ** 1.4307) if last >= 9 else 0.0
#   9교시(17:50) −1 · 10(18:50) −2.7 · 11(19:50) −4.7 · 12(20:50) −7.1
#   · 13(21:50) −10.0 · 14(22:50) −13.2
# Missing DINNER, by symmetry with lunch (3·4·5 = 11:00–13:50):
# dinner window = 9·10·11교시 = 17:00–19:50. Iden: "slightly bigger than missing lunch".
W_DINNER  =  -8.0   # lunch is −6
HOLE      = lambda L: -10.0*(L/4.0)**2   # dead block of L periods [4-hole == one 9am]
# R142 (elicitation 2026-08-07). E2: "a free Friday = two 9am starts", and E9 confirms he
# was pricing TRIP + BLANK DAY (not the events bonus). With REST=7 -> trip(1 day) = 13.0.
# Cross-checks against the older elicited ratio "월 = 금의 75%" (R45/R57): Monday = DAY_CONTIG,
# Friday = DAY_CONTIG + FRI_EVENT, so FRI_EVENT = DAY_CONTIG/3. Both hold simultaneously.
DAY_CONTIG=  13.00  # value of one weekend-attached free day  [Mon = 75% of Fri]
# R142: bracketed, not pinned. Iden could not quantify further ("can't quantify tbh").
#   V(2)/V(1) "about twice or slightly more" -> exponent ~1.2   (1.2 gives 2.30)
#   V(3)/V(2) "more than twice"              -> exponent >1.6   (1.6 gives 1.91, still <2)
# His two answers pull opposite ways; the honest bracket is [1.2, 1.6], midpoint 1.4.
# Direction (convex, >1) is solidly [E]; magnitude remains [P]. See the sensitivity check
# in DECISIONS_NEEDED D-2 before spending any more of his effort on this.
RUN_EXP   =   float(__import__('os').environ.get('RUN_EXP', 1.4))
# ⛔ CONTRADICTS R141 (external audit F4). Measured increments per extra free weekday at
# 1.4: 13.00 -> 21.31 -> 26.21 -> 30.02, i.e. INCREASING. Iden (R141): "2->3 is bigger than
# 3->4" — DECREASING — and R141's own conclusion agrees: "the fourth day is the least
# valuable as an increment". The code implements the curvature he retracted.
# ✅ Swept 0.8 -> 1.6: #1 is unchanged at every point, so this does not move the decision.
# ⚠️ The old bracket [1.2, 1.6] could not express concavity at all. Widened to [0.8, 1.6]
# so a sweep can state the arm that argues AGAINST the incumbent.
RUN_EXP_BRACKET = (0.8, 1.6)
# ---- R129 (Iden 2026-08-07): TRIP and REST are TWO GOODS, not one -------------------
# The whole free-day model was elicited under "commute to campus". Iden LIVES at 국제
# (dorm, auto-assigned). 신촌 is the campus he would commute to, from home. So the good
# was never "commutes avoided" — it is "can I go home?", and home is ~2h away (HANDOFF §1).
#   TRIP: needs days with NO CAMPUS PRESENCE, CONNECTED TO THE WEEKEND. An online class
#         does NOT block it — he can attend from home. Scales sharply in the day count.
#         -> DAY_CONTIG * (run-2)^RUN_EXP, run measured on the PRESENCE mask.
#   REST: needs a GENUINELY free day — no class of any kind holding a fixed hour.
#         Iden: "rest should apply to every single weekday (genuinely free days)."
#         Equal for every weekday, attached or not. -> REST, on the TIME mask.
# This reconciles two of Iden's statements that were resolved separately and never met:
#   R57 "nothing on Wednesday still feels good"  -> an EMPTY Wednesday is rest.
#   R91 "I still put in effort to listen to it"  -> a Wednesday with an online class
#                                                   is work, so it is not rest.
# R140: bracketed by THREE independent comparisons against fixed anchors —
#   > 6  (worse to lose than a missed lunch)   < 8  (better than a missed dinner)
#   < 10 (better than a 9am start).            Bracket (6,8) -> midpoint.
# Supersedes the old 4.70, which was "25% of a weekend-attached day" from R57/R114 and
# described an ISOLATED WEDNESDAY ONLY. R129 made this a different quantity.
REST      =   7.00  # one genuinely-free weekday, any weekday
ISOLATED  =   7.00  # DEPRECATED alias for REST
FRI_EVENT =   4.333 # Friday-only bonus, school events  [= 25% of Friday's value]
# Iden 2026-08-06: that bonus exists FOR the events, so it is void if fixed-time class
# sits in the event window. "Online still occupies time" -> 실시간온라인 and
# 동영상(중복수강불가) void it; 동영상콘텐츠 does NOT (no fixed hour, watch it later).
# Event window: 6~11교시 = 14:00–19:50 (afternoon–evening).
EVENT_WINDOW = range(6, 12)
# Course bonus — Iden's accepted exception to "no per-course points" (R64/R66/R69).
#   ECO1101  = QRM MR **and** Econ 2nd-major 필수, one slot   [elicited: 10]
#   ECO1103/1104/STA1002 = Econ 2nd-major 필수 only            [elicited:  5]
# Per R65, these are NET values: Iden assigns them knowing that a penalty which recurs
# every semester is not a real cost of taking the course now.
# ⛔ DEAD (R162). These per-course bonuses are NOT applied by the live scorer — rank3 reads
# rank2.BONUS, not this. Kept only because gen_weights.py documents the history. If anything
# ever imports and applies this dict, ECO1101 would silently receive +10 ON TOP of ROLE_MR
# +8, which is exactly the per-course thumb on the scale Iden's R64/R66/R69 rules out.
BONUS     = {}   # was {'ECO1101':10, 'ECO1103':5, 'ECO1104':5, 'STA1002':5} — superseded by
                 # the pool-role formula (R149): ECO1101 gets ROLE_MR 8.00 by measurement.
ECON2ND   = {'ECO1101','ECO1103','ECO1104','STA1002'}   # Econ 이중전공 필수, at 국제

def run_value(free):
    """⛔ REMOVED (R157). This implemented the PRE-R129 single-good free-day model — one
    value covering both 'going home' and 'a day off', keyed off the presence mask only.
    R129 split those into TRIP and REST. Leaving a working copy of a superseded model in
    the tree is how document-vs-code drift starts, so it now refuses to run.
    The live scorer is rank2.week_value()."""
    raise NotImplementedError(
        "rank.run_value is the pre-R129 model. Use rank2.week_value(pm, tm).")
    week = [d in free for d in range(5)] + [True, True]   # Mon..Fri, Sat, Sun
    best, cur = 0, 0
    for i in range(14):                      # two laps to catch wrap-around runs
        if week[i % 7]:
            cur += 1; best = max(best, min(cur, 7))
        else:
            cur = 0
    v = DAY_CONTIG * (best - 2) ** RUN_EXP if best > 2 else 0.0
    # free days not part of the maximal weekend-attached run count as isolated
    attached = set()
    for d in (4, 3, 2, 1, 0):                # walk back from Friday
        if d in free: attached.add(d)
        else: break
    for d in (0, 1, 2, 3, 4):                # walk forward from Monday
        if d in free: attached.add(d)
        else: break
    v += ISOLATED * len(free - attached)
    if 4 in free: v += FRI_EVENT
    return v

def score(time_mask, pres_mask, codes):
    """⛔ REMOVED (R157) — depends on run_value above. Live scorer: rank2.fast_score()."""
    raise NotImplementedError("rank.score is the pre-R129 model. Use rank2.fast_score(tm, pm).")
    sc, det = 0.0, dict(e1=0, e2=0, lf=0, df=0, late=0, mar=0, holes=[], runs=[])
    for day in range(5):
        dp = (time_mask >> (day*16)) & 0xffff
        if not dp: continue
        first = (dp & -dp).bit_length() - 1
        last  = dp.bit_length() - 1
        if   first == 1: sc += W_E1; det['e1'] += 1
        elif first == 2: sc += W_E2; det['e2'] += 1
        if all((dp >> p) & 1 for p in (3, 4, 5)): sc += W_LUNCH; det['lf'] += 1
        if last >= 9: sc += LATE(last); det['late'] += 1
        if all((dp >> p) & 1 for p in (9, 10, 11)): sc += W_DINNER; det['df'] = det.get('df',0)+1
        run = gap = 0
        for p in range(first, last + 2):          # +1 so a run ending at `last` closes
            if p <= last and (dp >> p) & 1:
                if gap: sc += HOLE(gap); det['holes'].append(gap); gap = 0
                run += 1
            else:
                if run >= 4: sc += MARATHON(run); det['runs'].append(run)
                run = 0
                if p <= last: gap += 1
    free = {d for d in range(5) if not ((pres_mask >> (d*16)) & 0xffff)}
    sc += run_value(free)
    det['free'] = free
    for c in codes: sc += BONUS.get(c, 0.0)
    return sc, det

# ---------------- DATA ----------------
def main():
    d = json.load(open('canonical_2026F.json', encoding='utf-8'))
    code = lambda s: s['c'].split('-')[0]
    SCILIT_FOR_ENG = {'UIC1541','UIC1918','UIC1502','UIC1920','UIC1751','MAT1001',
        'PHY1001','CHE1001','BIO1001','MAT1002','PHY1002','CHE1002','BIO1002'}
    LHPCODES_FOR_ENG = {'UIC1251','UIC1351','UIC1401','UIC1501','UIC1551','ASP2022','ASP2033'}
    BLOCK = [re.compile(x) for x in (r'LSBT|ISED', r'이학|생명시스템',
             r'UIC-ICU|LearnUs program', r'Senior students only', r'CDM first major')]
    # R92: every one of Iden's 7 completed CC courses was 언어='10' (English), incl. the
    # 대학교양-coded 통계학입문. The guide states no language rule anywhere, so per Iden's
    # own decision rule the default is: **CC courses must be English**.
    ENGONLY = {'UIC1561'} | LHPCODES_FOR_ENG | {'UIC2151'} | SCILIT_FOR_ENG
    def ok(s):                      # eligible to register at all
        return not any(p.search(s['note']) for p in BLOCK)
    def cc_ok(s):                   # may it FILL a CC requirement slot? (R92: English)
        return s['lang'] == '10'
    SC = {'UIC1541','UIC1918','UIC1502','UIC1920','UIC1751','MAT1001','PHY1001',
          'CHE1001','BIO1001','MAT1002','PHY1002','CHE1002','BIO1002'}
    WCIV = {'UIC1561'}          # R80: UCB1103/YCE1253 are 대학교양 lookalikes, NOT the CC course
    LHP = re.compile(r'WORLD (HISTORY|LITERATURE)')
    DONE = {'UIC2101','UIC1581','UIC1101','UIC1901','UCR1007','STA1001',
            'YCA1101','YCA1102','YCA1103','YCA1006'}
    SKIP = re.compile(r'사회참여|RC자기주도활동|RC심화|체육과건강')
    # period 0 = individually-scheduled research/thesis (수강편람: 개인별 지도).
    # No fixed meeting time -> occupies neither time nor campus presence.
    for s in d:
        s['time'] = [b for b in s['time'] if b[1] >= 1]
        s['pres'] = [b for b in s['pres'] if b[1] >= 1]
    ZERO = {'SED4001','NSE4001','ASP4009','SIT3010','SIT4308'}
    P = collections.defaultdict(list)
    for s in d:
        if not ok(s): continue
        c = code(s)
        if c in ZERO: continue          # senior research/thesis, individually scheduled
        if   c == 'QRM1001': P['MR'].append(s)
        elif c in WCIV and cc_ok(s): P['WCiv'].append(s)
        elif LHP.search(s['n'].upper()) and c != 'UIC1653' and s['dept'].startswith('언더우드국제대학 공통교과과정'): P['LHP'].append(s)
        elif (c == 'UIC2151' or c in SC) and cc_ok(s): P['SciRD'].append(s)
        elif s['c'] in ('YCA1006-01-00','YCA1006-02-00'): P['Chapel'].append(s)
        elif c == 'UIC1805': P['Lang'].append(s)
        elif c == 'UIC1806': pass                       # identical-grid fallback (D-4)
        elif c in DONE or SKIP.search(s['dept']) or s['cr'] < 1: pass
        else: P['SIXTH'].append(s)                      # ECO1101 / 원론 / ME / ELEC
    def mk(bl):
        m = 0
        for day, per in bl: m |= 1 << (day*16 + per)
        return m
    for v in P.values():
        for s in v: s['tm'] = mk(s['time']); s['pm'] = mk(s['pres'])
    print({k: len(v) for k, v in sorted(P.items())})

    rows = []
    for m in P['MR']:
     for w in P['WCiv']:
      if m['tm'] & w['tm']: continue
      for ch in P['Chapel']:
       if (m['tm']|w['tm']) & ch['tm']: continue
       t2, p2 = m['tm']|w['tm']|ch['tm'], m['pm']|w['pm']|ch['pm']
       for sr in P['SciRD']:
        if t2 & sr['tm']: continue
        t3, p3 = t2|sr['tm'], p2|sr['pm']
        for lh in P['LHP']:
         if t3 & lh['tm']: continue
         t4, p4 = t3|lh['tm'], p3|lh['pm']
         for la in P['Lang']:
          if t4 & la['tm']: continue
          t5, p5 = t4|la['tm'], p4|la['pm']
          for x in P['SIXTH']:
           if t5 & x['tm']: continue
           if code(x) in (code(sr), code(lh), code(w)): continue
           secs = (m, w, lh, sr, ch, la, x)
           sc, det = score(t5|x['tm'], p5|x['pm'], [code(s) for s in secs])
           rows.append((sc, secs, det))
    print(f"scored: {len(rows):,}")
    rows.sort(key=lambda r: (-r[0], tuple(s['c'] for s in r[1])))
    DN = '월화수목금'
    with open('FINAL_ranked.csv', 'w', newline='', encoding='utf-8-sig') as f:
        wr = csv.writer(f)
        wr.writerow(['rank','score','6th_course_type','QRM1001','WestCiv','LHP','SciRD',
                     'Chapel','Chinese','6th','free_days','early1','early2','lunch_fail',
                     'late','runs_hours','holes'])
        for i, (sc, secs, det) in enumerate(rows[:5000], 1):
            c6 = code(secs[6])
            typ = ('MR+Econ2nd' if c6=='ECO1101' else
                   'Econ2nd' if c6 in ECON2ND else
                   'ME' if c6.startswith('QRM') else 'ELEC')
            fmt = lambda x: f"{x['c']} {x['n'][:26]} [{x['t']}] {x['p']}"
            wr.writerow([i, round(sc,2), typ] + [fmt(s) for s in secs] +
                        [''.join(DN[d] for d in sorted(det['free'])), det['e1'], det['e2'],
                         det['lf'], det['late'], '+'.join(map(str,det['runs'])), '+'.join(map(str, det['holes']))])
    json.dump([[round(sc,3), [s['c'] for s in secs]] for sc, secs, _ in rows[:5000]],
              open('FINAL_top5000.json','w'))
    return rows

if __name__ == '__main__':
    rows = main()
    import collections as C
    code = lambda c: c.split('-')[0]
    top = rows[:5000]
    print("\ntop-50 6th-course mix:",
          dict(C.Counter(code(r[1][6]['c']) for r in rows[:50])))
    print("top-5000 6th-course mix:",
          dict(C.Counter(code(r[1][6]['c']) for r in top).most_common(8)))
    print("top-50 free days:",
          dict(C.Counter(''.join('월화수목금'[d] for d in sorted(r[2]['free'])) or 'none'
                         for r in rows[:50])))
    print("score range:", round(rows[0][0],2), "..", round(rows[-1][0],2))
    for sc, secs, det in rows[:3]:
        print(f"\n--- {sc:.2f}  free={''.join('월화수목금'[d] for d in sorted(det['free']))} "
              f"e1={det['e1']} lf={det['lf']} mar={det['mar']} holes={det['holes']}")
        for s in secs: print(f"    {s['c']:16s} {s['n'][:34]:34s} {s['t']}")
