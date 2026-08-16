"""
rank2.py — language slot is NO LONGER fixed (Iden, 2026-08-05: "let the timetable decide").

Structure: 4 required-now CC/MR courses + chapel (exempt) + **2 open slots**.
  fixed : QRM1001 · WestCiv · LHP · SciRD · Chapel
  open  : any eligible course incl. Chinese/Japanese, ECO1101, 원론, ME, ELEC
Bonuses: ECO1101 10 > Chinese/Japanese 8 > 원론/STA1002 5   (Iden: ECO1101 "slightly
higher than Chinese", "give Chinese/Japanese a bonus too")
At most ONE language course (both would satisfy the same requirement once).

Speed: open sections are collapsed by (time, presence, bonus) signature; identical
signatures score identically, so we enumerate signature pairs and expand afterwards.
"""
import json, re, collections, csv, heapq
import rank as RK
from rank import BONUS as _B     # R157: run_value no longer imported — pre-R129 model

# R103 (Iden 2026-08-06): "Scrap every single double major bonus for now."
# Only things that count for IDEN's actual degree are scored. The Econ-2nd-major
# bonuses were a bet on an undecided choice; they are removed until the double major
# is settled. What survives: QRM role bonuses (MR/ME) + the language requirement.
# ⛔ UNREACHABLE in the live path (R162). rank3 pulls language sections OUT of ELEC into
# REQ['Lang'] and scores them as a requirement slot, so this dict is never consulted — which
# is correct, and is exactly what R119 intended (the +8 and the −17 deferral cost are ONE
# logic, not two). Emptied so it cannot be silently re-activated.
BONUS = {}   # was {'UIC1805': 8.0, 'UIC1806': 8.0} — see R119/R162
LANG = {'UIC1805','UIC1806'}

# ---- ROLE bonuses (Iden 2026-08-06) ----------------------------------------
# "apply a bonus to MR and ME, MR slightly higher than ME, but both lower than 10 —
#  I don't want them to win over the minus from taking 2nd-year recommended classes."
# The 학년-2 penalty is −10, so both stay strictly below it: a 학년-2 ME course nets
# 6 − 10 = −4, i.e. still discouraged, exactly as asked.
ROLE_MR = 8.0     # fills one of QRM's six MR slots
# R150 (Iden 2026-08-07) — RETIRED his own 6.0 in favour of the measured value:
#   "although I said MR is slightly higher than ME, I don't think that holds. The timing I
#    said that was before the sophisticated 4-year plan implementation. I naturally thought
#    MEs (I have many selections) would be easier to get than MRs (fixed), but if the numbers
#    contradict that, then the numbers are probably right."
# His intuition and the formula were measuring the SAME thing — how hard a pool is to satisfy
# later. The formula just measures it properly. 6.0 -> 1.71.
# R152: the 84 cr supply was WRONG — it ignored the Korean-course cap (R105 / QRM grad table:
# "Of the QRM courses taken from the School of Economics and Department of Applied Statistics,
#  which are taught in Korean, only up to 4 courses (12 credits) can be counted as Major
#  Credits"). The cap attaches to the SECTION's offering department, not the course code:
#   QRM-dept ME courses (14)                    -> 42 cr, uncapped
#   ECO/STA codes with a UIC/QRM-offered section ->  9 cr, uncapped (ECO1103·ECO1104·STA2102)
#   ECO/STA reachable only from 상경대학/응용통계 -> min(12, 33) = 12 cr, CAPPED
# Corrected supply 63 cr, ratio 18/63 = 0.286.
ROLE_ME = 2.29    # MEASURED: 8 * (18 cr needed / 63 cr reachable) — R152
# R149 — pool roles MEASURED as 8 * min(1, credits-needed / reachable-supply), the same
# scale on which Iden set ROLE_MR. Independent check: MR needs 18 cr from exactly 18 cr of
# named courses -> ratio 1.00 -> 8.00, reproducing Iden's elicited +8 exactly.
#   MR 1.00 -> 8.00 (elicited 8 ✓)   ME 0.21 -> 1.71 (elicited 6 — CONFLICT, his value kept)
#   Seminar 0.04 -> 0.36             Free elective 0.01 -> 0.06 (i.e. the live 0.0 is right)
ROLE_SEMINAR = 0.36
ROLE_MB = 0.0     # R103: REMOVED. MB is not a QRM bucket at all — the only MB labels
                  # reaching Iden's courses came from 상경대학/경제학's view, i.e. they
                  # scored a double major he has not chosen. Restore only if/when Econ
                  # or Applied Stats is confirmed as the 2nd major.
# QRM's MR courses, by code (R18/R63/R99). NOTE ECO1101 is tagged **MB** in the
# catalogue — MB is its category for UIC-Economics — but QRM's requirement table names
# it as MR, and the MB courses 상경대학 calls 전필 are exactly ECO1101/2101/2102 (R99).
# So MR membership must come from QRM's list, not from the catalogue tag.
# ⚠ R101: six MR *requirements* but SEVEN codes — requirement 5 is a DISJUNCTION
# ("MATHEMATICAL STATISTICS **or** REGRESSION ANALYSIS"). The old set had 6 elements,
# which matched "6 MR requirements" and so looked correct while missing QRM3004.
MR_CODES = {'QRM1001', 'ECO1101', 'ECO2101', 'ECO2102',
            'QRM3003', 'QRM3004', 'QRM3005'}
BONUS_ECON2ND = 0.0   # R103: removed with the rest of the double-major layer.

# ---- 학년 (target-year) penalty. Iden 2026-08-05: penalise 학년 2/3/4, lowest listed
# year decides ("3,4" -> 3), null/0 -> no penalty, "scale pretty sharply".
# 학년 is ADVISORY not a gate (R1), so this is a PENALTY, never a filter.
# Anchored so 학년 2 costs one 9am morning; convex from there.
def year_of(yr):
    n = [int(x) for x in re.findall(r'\d+', yr or '') if x != '0']
    return min(n) if n else 0
# R128: rescaled. The SHAPE was already "years early" — only the first step was wrong.
# −10 for ONE year early is heavy when QRM's own chart calls those YR-2 courses and Iden
# is one semester from being 학년 2. Rescaled 10 -> 4, convexity untouched:
#   1 yr early −4 · 2 yrs −22.6 · 3 yrs −62.4
# Senior courses stay unreachable; next-year courses become competitive.
# R145 (Iden 2026-08-07): the penalty is TWO-SIDED. Being EARLY = "I'm not ready for it".
# Being LATE = off-sequence, and everything downstream slides with it. Iden: taking a 학년 3
# course at 학년 1 is penalised, "but taking a 학년 1 [course] at 학년 3..? Also not too
# desirable."  Elicited 2026-08-07:
#   asymmetry — "early is somewhat worse" = "roughly half again as bad"  -> EARLY/LATE = 1.5
#   late scaling — "sharply worse"        = same convex shape as the early arm (exp 2.5)
EARLY_K = 4.0            # R128, unchanged
LATE_K  = EARLY_K / 1.5  # = 2.667
YEAR_EXP = 2.5
def year_gap_pen(taken_in_year, chart_year):
    """Penalty for sitting a chart-year-`chart_year` course in academic year `taken_in_year`."""
    if not chart_year: return 0.0
    d = taken_in_year - chart_year
    if d == 0: return 0.0
    return -(EARLY_K if d < 0 else LATE_K) * abs(d) ** YEAR_EXP
# Iden is in academic year 1. Taking a course NOW therefore has gap (1 - chart_year), which is
# <= 0 — the late arm never fires on a course taken this semester. It fires on DEFERRED ones,
# which is precisely why it replaces the R117 deferral table (see R146).
YEAR_PEN = lambda y: year_gap_pen(1, y)

# R128b: for QRM-pool courses use QRM'S OWN curriculum year (대학요람 pp.246-7), not the
# registrar's 학년. The registrar labels ECO1103/1104 학년 2 from ECONOMICS' perspective;
# QRM's chart places them at YR 1. Penalising Iden for another major's classification is
# the same category error as R102.
QRM_CHART_YEAR = {
 'STA1001':1,'QRM1001':1,'ECO1101':1,'ECO1103':1,'ECO1104':1,
 'QRM2001':2,'QRM2002':2,'QRM2004':2,'QRM2100':2,'QRM2101':2,'QRM2102':2,
 'ECO2101':2,'ECO2102':2,'STA2102':2,'STA2104':2,'STA2105':2,'ECO1105':2,
 'QRM3001':3,'QRM3002':3,'QRM3003':3,'QRM3004':3,'QRM3005':3,'QRM3007':3,
 'ECO3104':3,'ECO3127':3,'ECO3130':3,'ECO3134':3,
 'QRM4001':4,'QRM4807':4,'QRM4808':4,'QRM4809':4,'STA4103':4,
 'ECO4115':4,'ECO4862':4,'ECO4865':4,
}
def eff_year(sec, code_of):
    """QRM's chart year if the course is in QRM's curriculum, else the registrar's 학년."""
    c = code_of(sec)
    if c in QRM_CHART_YEAR: return QRM_CHART_YEAR[c]
    return year_of(sec.get('yr'))
#   학년 2 -> −10 · 학년 3 -> −56.6 · 학년 4 -> −155.9

# ---- day-level memoisation: a day's penalty depends only on that day's 16-bit mask ----
_DAY = {}
def day_pen(dp):
    """(penalty, e1, e2, lf, late, runs, holes) for one day's bitmask."""
    v = _DAY.get(dp)
    if v is not None: return v
    sc = 0.0; e1 = e2 = lf = df = late = 0; runs = []; holes = []
    if dp:
        first = (dp & -dp).bit_length() - 1
        last = dp.bit_length() - 1
        if   first == 1: sc += RK.W_E1; e1 = 1
        elif first == 2: sc += RK.W_E2; e2 = 1
        if all((dp >> p) & 1 for p in (3, 4, 5)): sc += RK.W_LUNCH; lf = 1
        if last >= 9: sc += RK.LATE(last); late = 1
        if all((dp >> p) & 1 for p in (9, 10, 11)): sc += RK.W_DINNER; df = 1
        run = gap = 0
        for p in range(first, last + 2):
            if p <= last and (dp >> p) & 1:
                if gap: sc += RK.HOLE(gap); holes.append(gap); gap = 0
                run += 1
            else:
                if run >= 4: sc += RK.MARATHON(run); runs.append(run)
                run = 0
                if p <= last: gap += 1
    v = (sc, e1, e2, lf, late, tuple(runs), tuple(holes), df)
    _DAY[dp] = v
    return v

_FREE = {}

def week_value(pm, tm=0):   # `tm` here is the FIXED-hour mask (R210)
    """R129 (Iden 2026-08-07) — TWO INDEPENDENT GOODS, previously conflated into one.

    Iden lives at 국제 (dorm). The old model priced 'commutes avoided'; the real good is
    'can I go home?', and home is ~2h away. So:

      TRIP  — going home. Needs days with NO CAMPUS PRESENCE that are CONNECTED TO THE
              WEEKEND, and scales sharply in how many. An online class does NOT block it:
              he can attend from home.  -> PRESENCE mask.
      REST  — a day off. Needs a GENUINELY free day: nothing holding a fixed hour.
              Iden: "rest should apply to every single weekday (genuinely free days)."
              Equal for every weekday, weekend-attached or not.  -> TIME mask.

    Consequences vs the old model:
      * an isolated mid-week day whose only class is online now scores 0, not +4.70
        (it is neither a trip nor rest — R91: "I still put in effort to listen to it");
      * a genuinely empty 월/금 now earns REST **on top of** its trip value, which the
        old model never paid;
      * a mid-week run not touching the weekend no longer earns trip value.

    Friday events bonus is still VOID if fixed-time class occupies 14:00–19:50 (R91).
    """
    pres_free = [not ((pm >> (d*16)) & 0xffff) for d in range(7)]

    # ---- TRIP: the weekend-connected run, measured on PRESENCE
    run = 0
    if pres_free[5] and pres_free[6]:            # weekend intact -> walk outwards
        run = 2
        for d in (4, 3, 2, 1, 0):
            if pres_free[d]: run += 1
            else: break
        if run < 7:
            for d in (0, 1, 2, 3, 4):
                if pres_free[d]: run += 1
                else: break
        run = min(run, 7)
    v = RK.DAY_CONTIG * (run - 2) ** RK.RUN_EXP if run > 2 else 0.0

    # ---- REST: every genuinely-empty weekday, measured on TIME
    v += RK.REST * sum(1 for d in range(5) if not ((tm >> (d*16)) & 0xffff))

    # ---- Friday school-events bonus (R91)
    if pres_free[4]:
        fri = (tm >> (4*16)) & 0xffff
        if not any((fri >> p) & 1 for p in RK.EVENT_WINDOW):
            v += RK.FRI_EVENT
    return v, {d for d in range(5) if pres_free[d]}

def fast_score(tm, pm, fm=None):
    # R210: comfort is scored on the FIXED-hour mask, not the nominal one. `fm=None` keeps
    # every existing caller correct (fm falls back to tm = the old behaviour).
    if fm is None: fm = tm
    sc = 0.0; e1 = e2 = lf = df = late = 0; runs = []; holes = []
    for day in range(7):                          # includes 토/일
        r = day_pen((fm >> (day*16)) & 0xffff)
        if r[0] or r[5] or r[6]:
            sc += r[0]; e1 += r[1]; e2 += r[2]; lf += r[3]; late += r[4]; df += r[7]
            runs.extend(r[5]); holes.extend(r[6])
    v = _FREE.get((pm, fm))
    if v is None: v = _FREE[(pm, fm)] = week_value(pm, fm)
    sc += v[0]
    return sc, dict(e1=e1, e2=e2, lf=lf, df=df, late=late, runs=runs, holes=holes, free=v[1])

def main(TOPN=5000):
    d = json.load(open('canonical_2026F.json', encoding='utf-8'))
    code = lambda s: s['c'].split('-')[0]
    SCILIT_FOR_ENG = {'UIC1541','UIC1918','UIC1502','UIC1920','UIC1751','MAT1001',
        'PHY1001','CHE1001','BIO1001','MAT1002','PHY1002','CHE1002','BIO1002'}
    LHPCODES_FOR_ENG = {'UIC1251','UIC1351','UIC1401','UIC1501','UIC1551','ASP2022','ASP2033'}
    # R123: full 유의사항 audit. The old list caught 33 of 712; it missed 84 more,
    # including 59 sections that say outright 언더우드국제대학 소속 학생 수강 불가 — i.e.
    # they exclude Iden. 'senior[s]? only' also missed "Senior **students** only".
    BLOCK = [re.compile(x, re.I) for x in (
             r'LSBT|ISED', r'이학|생명시스템', r'UIC-ICU|LearnUs program',
             r'senior[s]? only', r'seniors only', r'senior\s+students\s+only',
             r'CDM first major', r'pre-?app?proved', r'해당학과 ?only', r'2학년 이상만',
             # --- R123 additions ---
             r'언더우드국제대학\s*소속\s*학생\s*수강\s*불가',   # 59 — explicitly bars UIC
             r'언더우드국제대학[^.]{0,80}제외한\s*1학년',        # 7  — "…를 제외한 1학년"
             r'의예과|치의예과|의치예과',                        # 9  — medical-only
             r'재외국민',                                      # 4  — 재외국민/외국인 전형 전용
             r'RA\(Residential Assistant\)만',                # 2  — RA only
             )]
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
    # R112 / R122: "(2)" courses are SEQUELS — unfulfillable without part (1), which Iden
    # has never taken. Most carry NO 유의사항, so the eligibility filter passes them.
    # R112 fixed only the SciRD pool; R122 extends it to OPEN, where MAT1002-05-00 had
    # reached the #1 timetable as a free elective.
    # ⚠ CODE MAP ONLY, never name matching (R80): "UIC1551 WORLD HISTORY: GROUP **II**"
    # is NOT a sequel, and a name rule would delete it from the LHP pool.
    SEQUEL_OF = {
        'MAT1002':'MAT1001','MAT1017':'MAT1001','MAT1012':'MAT1011',   # 미적분·공학수학
        'PHY1002':'PHY1001','PHY1012':'PHY1011',                       # 일반물리
        'CHE1002':'CHE1001','CHE1012':'CHE1011',                       # 일반화학
        'BIO1002':'BIO1001','BIO1012':'BIO1011','BIO1009':'BIO1001',   # 일반생물
        'SED2102':'SED2101','SED2010':'SED2009',                       # ISE
        'UIC1809':'UIC1805','UIC1808':'UIC1807',                       # UIC 언어(2)
        'YCF1302':'YCF1301','YCF1352':'YCF1351','YCF1452':'YCF1451',   # 제2외국어(2)
        'YCF1502':'YCF1501','YCF1552':'YCF1551','YCF1604':'YCF1603',
        'YCF1202':'YCF1201',
    }
    WCIV = {'UIC1561'}          # R80: UCB1103/YCE1253 are 대학교양 lookalikes, NOT the CC course
    # code-based per Iden (2026-08-05): match 학정번호, never similar English names.
    # CC L-H-P (World History / World Literature); UIC1653 excluded by R39.
    # R85: ASP2022 / ASP2033 carry 유의사항 "This course is also considered as
    # World History: Group Ⅱ" — they satisfy CC L-H-P despite non-UIC15xx codes.
    LHPCODES = {'UIC1251','UIC1351','UIC1401','UIC1501','UIC1551','ASP2022','ASP2033'}
    DONE = {'UIC2101','UIC1581','UIC1101','UIC1901','UCR1007','STA1001',
            'YCA1101','YCA1102','YCA1103','YCA1006'}
    SKIP = re.compile(r'사회참여|RC자기주도활동|RC심화|체육과건강')
    ZERO = {'SED4001','NSE4001','ASP4009','SIT3010','SIT4308'}
    for s in d:
        s['time'] = [b for b in s['time'] if b[1] >= 1]
        s['pres'] = [b for b in s['pres'] if b[1] >= 1]
    P = collections.defaultdict(list)
    for s in d:
        if not ok(s) or code(s) in ZERO: continue
        c = code(s)
        if   c == 'QRM1001': P['MR'].append(s)
        elif c in WCIV and cc_ok(s): P['WCiv'].append(s)
        elif c in LHPCODES and cc_ok(s): P['LHP'].append(s)
        elif (c == 'UIC2151' or c in SC) and cc_ok(s):
            if SEQUEL_OF.get(c) in DONE or c not in SEQUEL_OF:   # R112: part (1) required
                P['SciRD'].append(s)
        elif s['c'] in ('YCA1006-01-00','YCA1006-02-00'): P['Chapel'].append(s)
        elif c in DONE or SKIP.search(s['dept']) or s['cr'] < 1: pass
        elif c in SEQUEL_OF and SEQUEL_OF[c] not in DONE: pass   # R122
        else: P['OPEN'].append(s)
    for s in d:                                   # languages join the OPEN pool
        if ok(s) and code(s) in LANG: P['OPEN'].append(s)
    # R95/R96: QRM-relevant Major Electives = sections the catalogue itself tags ME and
    # that QRM's OWN department offers. This is how STA2102 선형대수 enters — it was
    # invisible while the pool was defined as "course code starts with QRM".
    for s in P['OPEN']:
        s['_qrm_me'] = (s.get('cat') == 'ME' and '계량위험관리' in s.get('dept', ''))
        c0 = code(s)
        # R102: prefer QRM's OWN label (qcat) over `cat`. `cat` is whichever 개설전공
        # query happened to run first, so ECO1103/1104 read MB (경제학's view) when QRM
        # itself calls them ME. qcat is authoritative for QRM credit; fall back only
        # when QRM does not list the section at all.
        q = s.get('qcat')
        if   q == 'MR':          s['_role'] = ROLE_MR
        elif q == 'ME':          s['_role'] = ROLE_ME
        elif c0 in MR_CODES:     s['_role'] = ROLE_MR
        elif s['_qrm_me']:       s['_role'] = ROLE_ME
        elif re.match(r'UIC3[56]\d\d', c0):
            # R148: UIC Seminars are 6 REQUIRED CC credits (R109/R131), not free electives.
            # They were scoring 0.0 — identical to a course that fills no requirement at all —
            # while paying the full readiness penalty, so they could never be chosen.
            # Treated like ME because they are the same KIND of thing: a required quota you
            # fill from a pool rather than one named course.
            # R149: MEASURED, not guessed. value = 8 * (credits still needed / reachable
            # supply). Seminars need 6 cr against 45 distinct courses = 135 cr -> ratio 0.04
            # -> 0.36. My first pass used ROLE_ME (6.0), which overvalued them ~17x: they are
            # required, but they are also the EASIEST requirement to satisfy later.
            s['_role'] = ROLE_SEMINAR
        elif s.get('cat') in ('MB', '전기'):
            s['_role'] = ROLE_MB          # R103: now 0.0 — kept as a named hook
        else:                    s['_role'] = 0.0
        if c0 == 'ECO1101': s['_role'] += BONUS_ECON2ND    # MR *and* Econ 이중전공 필수
    qme = [s for s in P['OPEN'] if s['_qrm_me']]
    print(f"QRM-department ME sections in OPEN: {len(qme)} -> "
          + ", ".join(sorted({x['code'] for x in qme})))
    def mk(bl):
        m = 0
        for day, per in bl: m |= 1 << (day*16 + per)
        return m
    for v in P.values():
        for s in v:
            s['tm'] = mk(s['time']); s['pm'] = mk(s['pres'])
            # ⭐ R210 — Iden: a 동영상콘텐츠 hour "is a real commitment, but it exists at the
            # best possible hour (maybe even saturday)". So a RECORDED hour does not pin the
            # week's shape; a LIVE one does. Three masks now, each with one job:
            #   tm = nominal hours  -> CONFLICT detection only (registration blocks overlaps)
            #   fm = FIXED hours    -> all comfort scoring (9am, lunch, runs, REST, events)
            #   pm = presence       -> the trip home
            _mode = str(s.get('mode') or '')
            s['fm'] = s['pm'] | (s['tm'] & ~s['pm'] if '실시간' in _mode else 0)
    print({k: len(v) for k, v in sorted(P.items())})

    # collapse OPEN by (time, presence, bonus, is-language)
    sig = collections.defaultdict(list)
    for s in P['OPEN']:
        sig[(s['tm'], s['pm'], BONUS.get(code(s), 0.0) + s.get('_role', 0.0) + YEAR_PEN(year_of(s['yr'])), code(s) in LANG, s['cr'])].append(s)
    sigs = list(sig)
    # course codes reachable from each signature — needed to forbid taking the same
    # course twice (two sections of one course) or duplicating a base course.
    SIGCODES = {g: {code(s) for s in sig[g]} for g in sigs}
    print(f"OPEN {len(P['OPEN'])} sections -> {len(sigs)} distinct signatures")

    heap = []; cnt=[0]
    bases = 0
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
         bases += 1
         basecodes = {code(m), code(w), code(lh), code(sr), code(ch)}
         basepen = sum(YEAR_PEN(year_of(x['yr'])) for x in (m, w, lh, sr, ch))
         # a signature is usable only if it still offers a course not already in the base
         cand = [g for g in sigs if not (t4 & g[0]) and (SIGCODES[g] - basecodes)]
         for i in range(len(cand)):
          a = cand[i]
          t5, p5 = t4|a[0], p4|a[1]
          ca = SIGCODES[a] - basecodes
          for j in range(i+1, len(cand)):
           b = cand[j]
           if t5 & b[0]: continue
           if a[3] and b[3]: continue            # never two language courses
           tot = a[4] + b[4]
           if tot < 6.0 or tot > 9.0: continue   # academic total 18..21 (D-17, R59)
           cb = SIGCODES[b] - basecodes
           # invalid only if every choice from a and b would be the SAME course
           if len(ca) == 1 and ca == cb: continue
           bonus = a[2] + b[2] + basepen
           sc, det = fast_score(t5|b[0], p5|b[1])
           sc += bonus
           if len(heap) < TOPN or sc > heap[0][0]:
               key = (m['c'], w['c'], lh['c'], sr['c'], ch['c'], a, b)
               item = (sc, cnt[0], key, det); cnt[0] += 1
               if len(heap) < TOPN: heapq.heappush(heap, item)
               else: heapq.heapreplace(heap, item)
    print(f"base combos: {bases:,}")
    out = sorted(heap, key=lambda x: -x[0])
    idx = {s['c']: s for v in P.values() for s in v}
    with open('FINAL_ranked2.csv', 'w', newline='', encoding='utf-8-sig') as f:
        wr = csv.writer(f)
        wr.writerow(['rank','score','QRM1001','WestCiv','LHP','SciRD','Chapel',
                     'open1','open2','has_language','credits','max_year','free_days',
                     'early1','early2','lunch_fail','late','runs_hours','holes'])
        DN='월화수목금'
        for i,(sc,_n,key,det) in enumerate(out,1):
            mc,wc,lc,sc_,cc,a,b = key
            based = {x.split('-')[0] for x in (mc,wc,lc,sc_,cc)}
            A = B = None
            for xa in sig[a]:
                if code(xa) in based: continue
                for xb in sig[b]:
                    if code(xb) in based or code(xb) == code(xa): continue
                    A, B = xa, xb; break
                if A: break
            if A is None: continue          # no valid distinct-course expansion exists
            fmt=lambda x: f"{x['c']} {x['n'][:24]} [{x['t']}]"
            lang = next((x['c'] for x in (A,B) if x['c'].split('-')[0] in LANG), '')
            wr.writerow([i, round(sc,2)] + [fmt(idx[c]) for c in (mc,wc,lc,sc_,cc)] +
                        [fmt(A), fmt(B), lang,
                         sum(idx[c].get('cr',0) for c in (mc,wc,lc,sc_)) + A['cr'] + B['cr'],
                         max(year_of(x['yr']) for x in [idx[c] for c in (mc,wc,lc,sc_,cc)]+[A,B]),
                         ''.join(DN[x] for x in sorted(det['free'])),
                         det['e1'],det['e2'],det['lf'],det['late'],
                         '+'.join(map(str,det['runs'])), '+'.join(map(str,det['holes']))])
    print("wrote FINAL_ranked2.csv")
    return out, sig, idx

if __name__ == '__main__':
    out, sig, idx = main()
    import collections as C
    print("\ntop score:", round(out[0][0],2))
    langtop = sum(1 for sc,_n,k,d in out[:50] if k[5][3] or k[6][3])
    print(f"top-50 containing a language course: {langtop}/50")
    print(f"top-500 containing a language course: {sum(1 for sc,_n,k,d in out[:500] if k[5][3] or k[6][3])}/500")
    print("top-50 free days:", dict(C.Counter(''.join('월화수목금'[x] for x in sorted(d['free'])) or 'none' for sc,_n,k,d in out[:50])))
    for sc,_n,key,det in out[:3]:
        mc,wc,lc,sc_,cc,a,b = key
        print(f"\n--- {sc:.2f} free={''.join('월화수목금'[x] for x in sorted(det['free']))} e1={det['e1']} runs={det['runs']}")
        for c in (mc,wc,lc,sc_,cc): print(f"    {idx[c]['c']:16s} {idx[c]['n'][:32]:32s} {idx[c]['t']}")
        for g in (a,b):
            s=sig[g][0]; print(f"    {s['c']:16s} {s['n'][:32]:32s} {s['t']}   <-- open slot")
