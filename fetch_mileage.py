# -*- coding: utf-8 -*-
"""
fetch_mileage.py (v3) — mileage competition HISTORY for every required course.

WHY: deferral cost must reflect "how hard is this to grab next semester". Section counts do
NOT predict that — Iden found two LHP sections cutting off at mileage 15 and 1. R6 says the
same and prescribes "prefer the MAX across recent semesters". This replaces estimates with
measurement.

  ⚠️ RUN ON IDEN'S MACHINE — the sandbox gets proxy 403 on every Yonsei host.

RUN THIS *SECOND*.
  `fetch_fall2026.py` answers the question with a deadline (is a 1학년 barred from
  UIC1561-01-00?). This one only enriches the deferral model. It shares the endpoint, so it
  **skips any section already in fall2026_seats.json** rather than asking twice.

PAYLOAD: captured from Iden's DevTools 2026-08-06, NOT guessed. Three corrections to what
the old notes claimed:
  * endpoint is findMlgAppcsResltList.do, not findMlgRankResltList.do (R5 was wrong)
  * _menuId differs from the catalogue endpoint's
  * the query is PER SECTION — corseDvclsNo (분반) + prctsCorseDvclsNo are required, so we
    must walk actual section lists rather than asking by course code

CHANGES 2026-08-16
  · ("2026","20") added to SEMESTERS — Fall 2026 mileage ran 8/10–8/11 and was published
    8/12, so for the first time it returns data. It was absent entirely before.
  · cookie read from jsessionid.txt, not hardcoded (the pasted one expired 8/06)
  · the blocking `input("continue? [y/N]")` prompt is gone — it made the script unrunnable
    unattended. The probe still prints; set PROBE_ONLY=1 to stop after it.
  · resumable per (semester, section); an expired cookie no longer discards the run
  · RequestException retry with backoff

RUN:  python fetch_mileage.py
"""
import json, os, sys, time, collections
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    sys.exit("⛔ needs `requests`.  Run:  pip install requests")

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
STATE = P('_mlg_state')
os.makedirs(STATE, exist_ok=True)

URL = "https://underwood1.yonsei.ac.kr/sch/sles/SlessyCtr/findMlgAppcsResltList.do"
HEADERS = {
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://underwood1.yonsei.ac.kr",
    "Referer": "https://underwood1.yonsei.ac.kr/com/lgin/SsoCtr/initExtPageWork.do?link=handbStdntBusns",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"),
    "X-Requested-With": "XMLHttpRequest",
}

# ⭐ Fall 2026 FIRST — it is the only term here that did not exist when v2 was written.
SEMESTERS = [("2026", "20"), ("2026", "10"), ("2025", "20"), ("2025", "10"), ("2024", "20")]


# --------------------------------------------------------------------------- cookie
def cookie():
    for src in ('jsessionid.txt', 'JSESSIONID.txt'):
        if os.path.exists(P(src)):
            v = open(P(src), encoding='utf-8').read().strip().strip('"').strip("'")
            if v.lower().startswith('jsessionid='):
                v = v.split('=', 1)[1]
            if v and not v.startswith('PASTE'):
                return v
    v = os.environ.get('JSESSIONID', '').strip()
    if v:
        return v
    sys.exit(
        "⛔ No cookie found.\n"
        "   Create a file called  jsessionid.txt  next to this script containing ONLY the\n"
        "   JSESSIONID value.\n"
        f"   Expected at: {P('jsessionid.txt')}")


JSESSIONID = None


class Stale(Exception):
    pass


class Unreachable(Exception):
    pass


def _payload(subjtnb, dvcls, prcts, syy, smt):
    return {
        "_menuId": "MTA5Njk5NjM3MTY5MTMxNTgwMDA=", "_menuNm": "", "_pgmId": "NDE0MDA4NTU1NjY=",
        "@d1#syy": syy, "@d1#smtDivCd": smt, "@d1#sysinstDivCd": "H1",
        "@d1#subjtnb": subjtnb, "@d1#corseDvclsNo": dvcls, "@d1#prctsCorseDvclsNo": prcts,
        "@d1#syySmtDivCd": f"{syy}{smt}",
        "@d#": "@d1#", "@d1#": "dmCond", "@d1#tp": "dm",
    }


def fetch(subjtnb, dvcls, prcts, syy, smt, _try=0):
    try:
        r = requests.post(URL, headers=HEADERS, cookies={"JSESSIONID": JSESSIONID},
                          data=urlencode(_payload(subjtnb, dvcls, prcts, syy, smt)).encode("utf-8"),
                          timeout=40)
    except requests.exceptions.RequestException as e:
        if _try < 2:
            time.sleep(3 * (_try + 1))
            return fetch(subjtnb, dvcls, prcts, syy, smt, _try + 1)
        raise Unreachable(str(e)[:160])
    try:
        data = r.json()
    except Exception:
        open(P("debug_response.html"), "w", encoding="utf-8").write(r.text)
        raise Stale()
    for v in data.values():
        if isinstance(v, list) and v:
            return v
    return []


# ---- which sections to ask about -------------------------------------------
REQ = {
    'WCiv': ['UIC1561'],
    'LHP': ['UIC1251', 'UIC1351', 'UIC1401', 'UIC1501', 'UIC1551', 'ASP2022', 'ASP2033'],
    'SciRD': ['UIC2151', 'UIC1751'],
    'MR': ['QRM1001', 'ECO1101', 'ECO2101', 'ECO2102', 'QRM3003', 'QRM3004', 'QRM3005'],
    # ⭐ R254 — THE HARD TIER WAS NEVER FETCHED, AND THE VERDICT DEPENDS ON IT.
    # This list held only the EASY tier, so mileage_history.json has zero YCF rows, so
    # risk.p_win_bracket() returns 'NO DATA' for all eight hard-tier languages, which
    # defaults to p = 1.0 — certainty (R252). The deferral verdict needs p >= 0.901.
    # The single most decision-relevant thing this script can now measure.
    'Lang': ['UIC1805', 'UIC1806',
             'YCF1301', 'YCF1351', 'YCF1451', 'YCF1501',
             'YCF1551', 'YCF1601', 'YCF1603', 'YCF1607'],
    'Chapel': ['YCA1003', 'YCA1005', 'YCA1006', 'YCA1007', 'YCA1009'],
    'ME': ['QRM2001', 'QRM2002', 'QRM2004', 'QRM2102', 'QRM3001', 'QRM3007',
           'QRM4807', 'QRM4808', 'QRM4809', 'STA2102', 'ECO1103', 'ECO1104'],
}
CODE2GROUP = {c: g for g, cs in REQ.items() for c in cs}


def sections_from_files():
    """(subjtnb, 분반, 실습) triples we know exist, from the catalogues on disk."""
    out = set()
    try:                                   # Spring 2026 — a COMPLETED mileage semester
        import openpyxl
        p = os.path.join(os.path.dirname(HERE), 'uploads', '강의목록_전체_v3.xlsx')
        if not os.path.exists(p):
            p = P('강의목록_전체_v3.xlsx')
        for r in openpyxl.load_workbook(p, read_only=True).active.iter_rows(values_only=True):
            sid = str(r[7] if len(r) > 7 else '')
            if sid.count('-') == 2 and sid.split('-')[0] in CODE2GROUP:
                a, b, c = sid.split('-'); out.add((a, b, c))
    except Exception as e:
        print(f"  (spring xlsx unavailable: {e})")
    try:                                   # Fall 2026 section numbers, reused as probes
        for s in json.load(open(P('canonical_2026F.json'), encoding='utf-8')):
            sid = s['c']
            if sid.count('-') == 2 and sid.split('-')[0] in CODE2GROUP:
                a, b, c = sid.split('-'); out.add((a, b, c))
    except Exception as e:
        print(f"  (canonical unavailable: {e})")

    # ⭐ R256 — SEED FROM THE PAST CATALOGUES TOO, OR 신촌 IS INVISIBLE.
    # The two sources above are both 국제 Fall. 신촌 numbers its 분반 01–04 while the 국제
    # catalogue lists 03–08, so probing 국제 분반 numbers finds nothing at 신촌. Measured:
    # 7 of 8 hard-tier languages had ZERO overlap; only YCF1551-04 matched, by coincidence,
    # and it was consequently the single hard language with any 신촌 history at all.
    # That matters because k_real receives `Lang·hard` AT 신촌 IN FALL — so the acquisition
    # probability behind the whole deferral verdict was being measured at the wrong campus.
    try:
        import pools_past as PP
        n0 = len(out)
        for lab, rows in PP.terms().items():
            for r in rows:
                a = str(r.get('subjtnb') or '')
                if a in CODE2GROUP:
                    b = str(r.get('corseDvclsNo') or '')
                    c = str(r.get('prctsCorseDvclsNo') or '00')
                    if b:
                        out.add((a, b, c))
        print(f"  past_terms seed: +{len(out)-n0} (subjtnb, 분반) probes, incl. 신촌")
    except Exception as e:
        print(f"  (past_terms unavailable, 신촌 분반 will be missed: {e})")
    return sorted(out)


def already_pulled():
    """Sections fetch_fall2026.py already has for 2026-20 — do not ask twice."""
    try:
        return set(json.load(open(P('fall2026_seats.json'), encoding='utf-8')))
    except Exception:
        return set()


def probe():
    print("\n=== PROBE: full JSON, so an empty vs a real answer is distinguishable ===")
    PROBES = [("UIC1561", "01", "00", "2026", "20", "⭐ the 35.72 section, Fall 2026"),
              ("UIC1251", "01", "00", "2026", "10", "R3 says avg 19.1 — should have data"),
              ("UIC1251", "01", "00", "2025", "10", "same course, a year earlier"),
              ("YCA1006", "01", "00", "2025", "20", "Fall chapel code, Fall term"),
              ("UIC2151", "01", "00", "2026", "10", "RDQM, R3 says avg 7.4")]
    for a, b, c, y, s, why in PROBES:
        try:
            rows = fetch(a, b, c, y, s)
        except (Stale, Unreachable) as e:
            print(f"  {a}-{b} {y}-{s}: {type(e).__name__} {e}")
            return False
        print(f"\n  {a}-{b} {y}-{s}  ({why})  -> {len(rows)} row(s)")
        if rows:
            print(f"    FIELDS: {sorted(rows[0])}")
            print(f"    ROW   : {json.dumps(rows[0], ensure_ascii=False)[:420]}")
    print("\n=== end probe ===\n")
    return True


def main():
    global JSESSIONID
    JSESSIONID = cookie()
    print(f"cookie loaded ({len(JSESSIONID)} chars)")

    secs = sections_from_files()
    skip = already_pulled()
    print(f"{len(secs)} known sections across {len(CODE2GROUP)} required course codes")
    if skip:
        print(f"  ({len(skip)} already in fall2026_seats.json — those are skipped for 2026-20)")

    if not probe():
        print("⛔ the probe could not reach the portal with a valid cookie. Fix that first.")
        return
    if os.environ.get('PROBE_ONLY'):
        return

    out, stale, offline = [], False, False
    t0 = time.time()
    for syy, smt in SEMESTERS:
        lab = f"{syy}-{'1' if smt == '10' else '2'}"
        sf = os.path.join(STATE, f"{lab}.json")

        # ⛔ R257 — THE CACHE MUST RECORD *WHICH SECTIONS WERE PROBED*, NOT JUST THE ROWS.
        # The first version stored a bare list of rows. Adding the 88 신촌 probes (R256) then
        # did nothing at all: every term reported "cached" and replayed the previous
        # 76-section run. This is R250's failure exactly — a cache key that omits what
        # determines the contents — reintroduced in the resume logic written the same day.
        got, probed = [], set()
        if os.path.exists(sf) and os.path.getsize(sf):
            try:
                blob = json.load(open(sf, encoding='utf-8'))
            except Exception:
                blob = None
            if isinstance(blob, dict) and '_probed' in blob:
                got = blob.get('rows', [])
                probed = set(blob['_probed'])
            elif isinstance(blob, list):
                # legacy format: rows only. A section that returned nothing left no trace,
                # so we can only credit the ones that DID return data and must re-probe
                # the rest. Keeps the 187 rows already fetched; costs one pass over the
                # empties. Written back in the new format, so this happens once.
                got = blob
                probed = {f"{r.get('_code')}-{r.get('_dvcls')}-00" for r in blob}
                print(f"  {lab}학기: legacy cache — {len(probed)} sections credited, "
                      f"re-probing the rest")

        todo = [(a, b, c) for a, b, c in secs
                if f"{a}-{b}-{c}" not in probed
                and not (smt == "20" and syy == "2026" and f"{a}-{b}-{c}" in skip)]
        if not todo:
            out += got
            print(f"  {lab}학기: cached ({len(got)} rows, {len(probed)} sections probed)")
            continue

        hit = 0
        for a, b, c in todo:
            try:
                rows = fetch(a, b, c, syy, smt)
            except Stale:
                stale = True; break
            except Unreachable as e:
                offline = True; print(f"    network error: {e}"); break
            probed.add(f"{a}-{b}-{c}")
            if rows:
                hit += 1
                for r in rows:
                    r.update(_code=a, _dvcls=b, _syy=syy, _smt=smt,
                             _group=CODE2GROUP.get(a, '?'))
                    got.append(r)
            time.sleep(0.2)
        # partial progress is saved even on a stale cookie / dropped network
        json.dump({'_probed': sorted(probed), 'rows': got},
                  open(sf, 'w', encoding='utf-8'), ensure_ascii=False)
        if stale or offline:
            break
        out += got
        print(f"  {lab}학기: +{hit}/{len(todo)} newly probed had data "
              f"(rows {len(got)} total, {len(probed)} sections probed, {time.time()-t0:.0f}s)")

    if stale:
        print("\n⛔ THE COOKIE EXPIRED. Every completed semester is cached in _mlg_state/.")
        print("   Refresh jsessionid.txt and re-run — it resumes.")
        return
    if offline:
        print("\n⛔ COULD NOT REACH THE PORTAL. Completed semesters are cached; re-run later.")
        return

    json.dump(out, open(P('mileage_history.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f"\nwrote mileage_history.json — {len(out)} rows")
    print("by group:", dict(collections.Counter(r['_group'] for r in out)))
    print("by term :", dict(collections.Counter(f"{r['_syy']}-{r['_smt']}" for r in out)))


if __name__ == "__main__":
    main()
