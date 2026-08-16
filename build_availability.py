"""
build_availability.py — DESIGN_v2 §1. The state space, not a score.

"When / where / in what language / from which department / at what times does this course
exist" is DATA. Every other v2 factor consumes it. It has no weights and nothing to elicit.

Every finding it reproduces was hand-queried in the 2026-08-07 session:
  R159  ECO1101 is 월수 in every recorded Fall but offered 화목 in both recorded Springs
  R164  ECO1101's only ENGLISH 신촌 section is 월1,2/수2 — Monday AND a 9am start
  R152  the Korean cap attaches to the SECTION's offering department, not the course code
  R143  4 items are 국제-only; canonical_2026F.json cannot see the 신촌 side at all

SOURCES
  raw_2026F.json        Fall 2026, BOTH campuses (717 국제 + 783 신촌)   <- the only 신촌 source
  canonical_2026F.json  Fall 2026, 국제 only, but richer per-section fields
  mileage_history.json  4 completed semesters, but only 21 course codes  <- the thin part

⚠️ EVIDENCE IS ASYMMETRIC. Fall 2026 is fully observed; earlier terms exist for 21 courses
only. Every record carries n_terms so nothing downstream mistakes one observation for a rule.
"""
import json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
DAYS = '월화수목금'
SEMNAME = {('2024','20'):'F24', ('2025','10'):'S25', ('2025','20'):'F25',
           ('2026','10'):'S26', ('2026','20'):'F26'}

def days_of(t):
    return ''.join(sorted({c for c in (t or '') if c in DAYS}, key=DAYS.index))

def starts_at_9(t):
    return bool(re.search(r'[월화수목금]1(?![0-9])', t or ''))

def term_of(sem):     # 'F26' -> 'Fall'
    return 'Fall' if sem.startswith('F') else 'Spring'

def collect():
    rec = collections.defaultdict(lambda: collections.defaultdict(list))

    # --- Fall 2026, both campuses -------------------------------------------
    canon = {s['c']: s for s in json.load(open(P('canonical_2026F.json'), encoding='utf-8'))}
    for x in json.load(open(P('raw_2026F.json'), encoding='utf-8')):
        code = x.get('subjtnb'); sid = f"{code}-{x.get('corseDvclsNo')}-00"
        c = canon.get(sid, {})
        rec[code]['F26'].append(dict(
            sid=sid, campus=x.get('campsDivNm'),
            lang='EN' if x.get('srclnLctreLangDivCd') == '10' else 'KR',
            dept=c.get('dept') or x.get('estblDeprtCd'),
            time=x.get('lctreTimeNm') or '', prof=x.get('cgprfNm'),
            grade=c.get('grade'), cr=x.get('cdt')))

    # --- earlier terms: only where mileage history reaches ------------------
    for r in json.load(open(P('mileage_history.json'), encoding='utf-8')):
        sem = SEMNAME.get((r['syy'], r['smtDivCd']))
        if not sem: continue
        rec[r['subjtnb']][sem].append(dict(
            sid=r['subjtnbNo'], campus=r.get('campsDivNm'),
            lang='EN' if r.get('srclnLctreLangDivCd') == '10' else 'KR',
            dept=r.get('estblDeprtCd'), time=r.get('lctreTimeNm') or '',
            prof=r.get('cgprfNm'), grade=None, cr=r.get('cdt'),
            cap=r.get('atnlcPercpCnt'), applied=r.get('cnt'),
            yr_quota=[r.get(f'sy{i}PercpCnt') or 0 for i in range(1, 7)]))
    return rec

def summarise(rec):
    out = {}
    for code, terms in rec.items():
        secs = [s for v in terms.values() for s in v]
        falls   = {t for t in terms if term_of(t) == 'Fall'}
        springs = {t for t in terms if term_of(t) == 'Spring'}
        fall_days   = {days_of(s['time']) for t in falls   for s in terms[t] if s['time']}
        spring_days = {days_of(s['time']) for t in springs for s in terms[t] if s['time']}
        campuses = {s['campus'] for s in secs if s['campus']}
        langs    = {s['lang'] for s in secs}
        out[code] = dict(
            n_terms=len(terms), terms=sorted(terms), n_sections=len(secs),
            campuses=sorted(campuses), languages=sorted(langs),
            fall_day_patterns=sorted(fall_days), spring_day_patterns=sorted(spring_days),
            # --- derived flags, the things downstream actually asks ---
            campus_locked=(list(campuses)[0] if len(campuses) == 1 else None),
            fall_only=bool(falls and not springs and len(terms) > 1),
            spring_only=bool(springs and not falls and len(terms) > 1),
            day_pattern_varies_by_term=bool(fall_days and spring_days and fall_days != spring_days),
            english_available=('EN' in langs), korean_available=('KR' in langs),
            # ⚠️ a section's dept decides Korean-cap consumption (R152), not the code
            depts=sorted({str(s['dept']) for s in secs if s['dept']}),
            sections=secs)
    return out

def main():
    rec = collect(); tab = summarise(rec)
    json.dump(tab, open(P('availability.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    multi = {c: v for c, v in tab.items() if v['n_terms'] > 1}
    print(f"wrote availability.json — {len(tab)} courses")
    print(f"  observed in >1 term: {len(multi)}  (the rest are Fall-2026-only; do not "
          f"mistake one observation for a rule)\n")

    print("=== courses whose DAY PATTERN changes between Fall and Spring ===")
    hits = {c: v for c, v in multi.items() if v['day_pattern_varies_by_term']}
    if not hits: print("   none")
    for c, v in sorted(hits.items()):
        print(f"   {c:9s} Fall {sorted(v['fall_day_patterns'])}  vs  Spring {sorted(v['spring_day_patterns'])}"
              f"   [{v['n_terms']} terms]")
    print("\n=== campus-locked courses (seen at ONE campus only) ===")
    for c, v in sorted(multi.items()):
        if v['campus_locked']: print(f"   {c:9s} {v['campus_locked']:4s}  [{v['n_terms']} terms]")
    print("\n=== courses offered in BOTH languages — language selects the section (R164) ===")
    for c, v in sorted(tab.items()):
        if v['english_available'] and v['korean_available']:
            print(f"   {c:9s} depts={len(v['depts'])}  campuses={v['campuses']}")

if __name__ == '__main__':
    main()
