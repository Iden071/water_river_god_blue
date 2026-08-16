# -*- coding: utf-8 -*-
"""
eligibility.py — drop sections Iden cannot actually register for.

Three catalogue fields exist that **nothing in the ranker has ever read** (R238):

  · `rmvlcYnNm` = 폐강        — the section is CANCELLED. 7 in the Fall 2026 catalogue,
                                 **2 of them sitting in the candidate pool** (CTM2012-01-00,
                                 CTM2018-01-00). Neither reached the top 50, which was luck.
  · `atntnMattrDesc` 유의사항  — carries eligibility limits ("UIC students only", 학번 windows,
                                 department restrictions) and stated prerequisites.
  · `hy` 학년                  — advisory only (R1); the real gate is 학년별정원, which is the
                                 8/14 pull. NOT filtered here.

R61 audited eligibility exactly once, against a SciLit pool belonging to a model since
replaced. This re-runs it against whatever the pool actually contains, every build.

WHAT IS FILTERED, AND WHAT IS ONLY FLAGGED
Filtering on free text is how you silently lose a legal option, so only the unambiguous
machine-readable field is a filter:

  FILTER   폐강 — the section will not exist.
  FLAG     everything textual — reported, never dropped.

Iden's situation, for reading the flags: **UIC student, 2026 entrant, HASS division, 1학년.**
"UIC students only" is SATISFIED. A 2025-or-earlier 학번 window is NOT.

    import rank3, eligibility
    P = rank3.build()[0]
    eligibility.apply(P)
"""
import json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
_RAW = None

ENTRY_YEAR = 2026
COLLEGE = 'UIC'


def _raw():
    global _RAW
    if _RAW is None:
        r = json.load(open(os.path.join(HERE, 'raw_2026F.json'), encoding='utf-8'))
        r = r if isinstance(r, list) else list(r.values())[0]
        _RAW = {f"{x.get('subjtnb')}-{x.get('corseDvclsNo')}-{x.get('prctsCorseDvclsNo')}": x
                for x in r}
    return _RAW


def cancelled(sid):
    r = _raw().get(sid)
    return bool(r) and str(r.get('rmvlcYnNm') or '').strip() == '폐강'


def notice(sid):
    r = _raw().get(sid)
    return str((r or {}).get('atntnMattrDesc') or '').strip()


# ---------------------------------------------------------------------------
# 학년별정원 — the REAL year gate, and the only one that is machine-readable
# ---------------------------------------------------------------------------
# From the 8/16 seat pull (R247). 수강신청 제도안내 §4: registration is IMPOSSIBLE, not
# merely competitive, if the per-year quota is 0. Per-year quotas are OPTIONAL (FAQ 라), so
# the test is two-sided and R134 is precisely about the difference:
#
#     all sy1..sy6 == 0            -> no scheme in force        -> NOT a gate (R2)
#     some sy_i != 0 AND sy1 == 0  -> scheme in force, 1학년 = 0 -> BARRED
#     no row returned at all       -> NOT a gate (R249)  ← absence of evidence
#
# ⚠️ Nothing else in fall2026_seats.json may be used. `atnlcPercpCnt` is NOT section
# capacity (R248) — it is constant across 분반 regardless of 강의실 — so 정원/신청 must
# never reach a score. This function reads sy1..sy6 and nothing else, on purpose.
_SEATS = None


def _seats():
    global _SEATS
    if _SEATS is None:
        try:
            _SEATS = json.load(open(os.path.join(HERE, 'fall2026_seats.json'), encoding='utf-8'))
        except Exception:
            _SEATS = {}
    return _SEATS


def year_barred(sid):
    """(True, reason) if a 학년별정원 scheme is in force and the 1학년 share is zero."""
    r = _seats().get(sid)
    if not r:
        return False, ''                      # blank row is not a bar (R249)
    sy = [r.get(f'sy{i}PercpCnt') or 0 for i in range(1, 7)]
    if any(sy) and sy[0] == 0:
        return True, f'학년별정원 in force, 1학년 share 0 — sy1..sy6 {sy} (R134/R247)'
    return False, ''


# ---------------------------------------------------------------------------
# HARD EXCLUSIONS — unambiguous, machine-checkable, and true of Iden specifically
# ---------------------------------------------------------------------------
# Read out of the 유의사항 text on 2026-08-10. Each was checked by hand before being made a
# filter; anything requiring judgement stays a flag.
#
#   "N학년 이상만 수강 가능"        N > 1  -> he is 1학년. EXCLUDED.
#   "2026학번부터는 N학년 이상…"    N > 1  -> he IS 2026학번. EXCLUDED.
#   "…전공자와 … 학생만 수강가능"    a department allow-list that does not contain UIC. EXCLUDED.
#
# NOT excluded, and deliberately so:
#   "UIC students only"            -> he is UIC. satisfied.
#   "1학년만 수강 가능"             -> he IS 1학년. satisfied (BIZ2129).
#   "(Recommended) Prerequisite"   -> recommended, not enforced. flagged, kept.
#
# ⚠️ THE PATTERNS WERE KOREAN-ONLY UNTIL R243. A census of all 212 notices in the pool found
# 52 that no rule examined, and two of them were real exclusions written in English or in a
# bracketed 수강대상 tag. Restriction text is bilingual; the rules must be too.
_YEAR_MIN = re.compile(r'(\d)\s*학년\s*이상만?\s*수강\s*가능')
_DEPT_ONLY = re.compile(r'([^,.]*?)\s*학생만\s*수강\s*가능')
# English forms: "CDM students only" · "only IID first major and double major students can enrol"
_EN_ONLY = re.compile(r'\b([A-Z]{2,6})\s+students\s+only', re.I)
_EN_ONLY2 = re.compile(r'\bonly\s+([A-Z]{2,6})\s+(?:first\s+major|majors?|students)', re.I)
_TARGET = re.compile(r'\[수강대상\]\s*([^,.\n]{2,40})')
_MILEAGE_SCOPED = re.compile(r'mileage[^,.]*period|마일리지[^,.]*기간', re.I)
IDEN_YEAR = 1
IDEN_DEPT_WORDS = ('언더우드', 'UIC', '국제대학')
# programme codes Iden belongs to. Anything else naming itself "only" excludes him.
IDEN_PROGRAMMES = {'UIC', 'HASS', 'QRM'}


def excluded(sid):
    """(True, reason) if Iden cannot register for this section at all."""
    txt = notice(sid)
    if not txt:
        return False, ''
    m = _YEAR_MIN.search(txt)
    if m and int(m.group(1)) > IDEN_YEAR:
        return True, f'{m.group(1)}학년 이상만 수강 가능 (he is {IDEN_YEAR}학년)'
    m = _DEPT_ONLY.search(txt)
    if m and not any(w in m.group(1) for w in IDEN_DEPT_WORDS):
        return True, f'department allow-list excludes UIC: "{m.group(1).strip()[:44]}"'
    # ⚠️ SCOPE MATTERS. "During the mileage course registration period, only IID … can enrol.
    # The remaining spots will be available to all students during the additional course
    # enrollment period." — that restriction binds the MILEAGE round, which is 2학년+ only
    # (R130). Iden registers on 8/25 first-come, so it does NOT exclude him; it is a
    # seat-competition fact for the 8/14 pull, not an eligibility gate.
    # Caught by inspecting the full notice text after the first version wrongly dropped
    # IID1001 / IID2005 / IID3004 (R243).
    for rx in (_EN_ONLY, _EN_ONLY2):
        for m in rx.finditer(txt):
            prog = m.group(1)
            if prog.upper() in IDEN_PROGRAMMES:
                continue
            window = txt[max(0, m.start() - 90):m.start()]
            if _MILEAGE_SCOPED.search(window):
                continue                       # scoped to a round Iden is not in
            return True, f'"{prog} students only" — he is UIC/HASS/QRM'
    return False, ''


# textual patterns worth a human's attention. NOT used to drop anything.
PATTERNS = [
    ('prerequisite', re.compile(r'requisite|선수과목|선수 과목', re.I)),
    ('permission needed', re.compile(r'담당교수 *(승인|허가)|승인 *후|허가 *후')),
    # a bracketed target-audience tag. Too varied to filter on safely — SHOWN, not dropped.
    ('수강대상 tag', _TARGET),
    # a restriction that binds only the mileage round — 2학년+ only, so not Iden's round.
    # Kept, but it means the section is contested and its seats may be gone by 8/25.
    ('mileage-round priority', _MILEAGE_SCOPED),
]


def flags(sid):
    txt = notice(sid)
    if not txt:
        return []
    return [nm for nm, rx in PATTERNS if rx.search(txt)]


def apply(P, verbose=True):
    """Drop cancelled sections in place. Returns (dropped, flagged)."""
    dropped, flagged = [], collections.defaultdict(list)
    for nm, pool in P.items():
        keep = []
        for s in pool:
            if cancelled(s['c']):
                dropped.append((nm, s['c'], '폐강 (cancelled)'))
                continue
            ex, why = excluded(s['c'])
            if ex:
                dropped.append((nm, s['c'], why))
                continue
            yb, why = year_barred(s['c'])
            if yb:
                dropped.append((nm, s['c'], why))
                continue
            for f in flags(s['c']):
                flagged[f].append(s['c'])
            keep.append(s)
        pool[:] = keep
    if verbose:
        if dropped:
            print(f"  eligibility: dropped {len(dropped)} section(s) Iden cannot register for:")
            for _n, c, why in sorted(dropped, key=lambda x: x[1]):
                print(f"      {c:16s} {why}")
        for f, cs in sorted(flagged.items()):
            print(f"  eligibility: ⚠ {len(set(cs))} section(s) flagged '{f}' (kept, not dropped)")
            if f == '수강대상 tag':
                for c in sorted(set(cs)):
                    print(f"        {c}  {notice(c)[:88]}")
    return dropped, flagged


def audit(secs):
    """Full report for one timetable — every field, so nothing is silently satisfied."""
    out = []
    for c in secs:
        r = _raw().get(c) or {}
        out.append(dict(sid=c, name=str(r.get('subjtNm') or '')[:40],
                        cancelled=cancelled(c), hy=str(r.get('hy') or ''),
                        notice=notice(c), flags=flags(c)))
    return out


if __name__ == '__main__':
    import rank3
    P = rank3.build()[0]
    before = {nm: len(v) for nm, v in P.items()}
    apply(P)
    print('\n  pool sizes:', {nm: f"{before[nm]}->{len(v)}" for nm, v in P.items()})
