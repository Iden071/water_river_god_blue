# -*- coding: utf-8 -*-
"""
fetch_fall2026.py — THE SEAT PULL.  Run on Iden's machine; the sandbox gets proxy 403.

WHAT IT ANSWERS
  The 2학년+ rounds closed 8/14. This pulls the Fall 2026 mileage result for every section
  Iden might click on 8/25 and answers ONE question per section:

      can a 1학년 register for this at all?

  수강신청 제도안내 §4: registration is IMPOSSIBLE — not merely competitive — if
  "학년별 정원이 0". Per-year quotas are OPTIONAL (FAQ 라: 학과 선택사항), so:

      all sy1..sy6 == 0            -> no per-year scheme in force        -> fine
      some sy_i != 0 AND sy1 == 0  -> scheme IS in force, 1학년 gets ZERO -> BARRED

  That distinction is R134 and it is the whole point of this script.

  ⭐ THE ONE THAT MATTERS: UIC1561-01-00. Losing it costs 35.72; losing anything else in the
  recommendation costs ≤ 0.25 (R242). The verdict block calls it out by name.

  ⚠️ Do NOT read 배율 as Iden's odds. The mileage round is 2학년+ only (R130), and freshmen
  are structurally invisible in this table (R7). An all-zero 학년별정원 means NO GATE (R2),
  not "no freshman seats". A blank result for a section is likewise not evidence of a bar.

------------------------------------------------------------------------------------------
HOW TO RUN — three steps, and only step 2 is fiddly
------------------------------------------------------------------------------------------
 1. Log into the portal in Chrome and LEAVE THE TAB OPEN:
      https://underwood1.yonsei.ac.kr/com/lgin/SsoCtr/initExtPageWork.do?link=handbStdntBusns

 2. Get the cookie:  F12 -> Application -> Cookies -> underwood1.yonsei.ac.kr
    Click JSESSIONID, copy its **Value** (long, ends in something like
    `.aGFrc2FfZG9tYWluL2hha3NhMV8x`).
    Paste it into a plain text file named  jsessionid.txt  next to this script.
    (A file, not the source — so it can be refreshed without editing code.)

 3. Run:   python fetch_fall2026.py

Safe to re-run any number of times. **Resumable**: every section is saved the moment it
returns, so if the cookie expires mid-run — it will, they are short-lived — just refresh
jsessionid.txt and run it again. Nothing already fetched is re-fetched.

CHANGES 2026-08-16
  · cookie read from jsessionid.txt, not pasted into source (matches fetch_past_terms.py)
  · resumable — the old version lost the whole run on an expired cookie
  · RequestException retry with backoff; a dropped VPN no longer dumps a traceback
  · targets() rebuilt from the **v3** search output. It previously read FINAL_ranked3.csv,
    which INDEX marks superseded. MEASURED, not assumed: old list 99 sections, new 179.
    The old list did cover the current recommendation — the first draft of this note claimed
    otherwise and was wrong — but it missed YCI1704-02-00, which is the zero-cost swap for
    YCE1253-01-00 in fallback.json, plus 79 other reachable sections (14 YCB1101 chapel
    분반, 4 YCF1201, the QRM2xxx/3xxx ME pool, UIC1751). Those are exactly the sections a
    re-search would move to if something is barred, so their 1학년 gate has to be known too.
  · dumps the raw field names of the first hit, so the sy*/정원 keys are VERIFIED against
    the response rather than trusted (the field-code-vs-field-name error, R-log 2026-08-10)
"""
import json, os, sys, time, glob, collections
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    sys.exit("⛔ needs `requests`.  Run:  pip install requests")

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
OUT = P('fall2026_seats.json')

SYY, SMT = "2026", "20"                        # Fall 2026
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

STAR = 'UIC1561-01-00'          # the 35.72 section (R242)


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
        "   JSESSIONID value (step 2 in the docstring at the top of this file).\n"
        f"   Expected at: {P('jsessionid.txt')}")


JSESSIONID = None


class Stale(Exception):
    pass


class Unreachable(Exception):
    pass


# --------------------------------------------------------------------------- fetch
def fetch(code, dv, pr, _try=0):
    pl = {"_menuId": "MTA5Njk5NjM3MTY5MTMxNTgwMDA=", "_menuNm": "", "_pgmId": "NDE0MDA4NTU1NjY=",
          "@d1#syy": SYY, "@d1#smtDivCd": SMT, "@d1#sysinstDivCd": "H1", "@d1#subjtnb": code,
          "@d1#corseDvclsNo": dv, "@d1#prctsCorseDvclsNo": pr, "@d1#syySmtDivCd": SYY + SMT,
          "@d#": "@d1#", "@d1#": "dmCond", "@d1#tp": "dm"}
    try:
        r = requests.post(URL, headers=HEADERS, cookies={"JSESSIONID": JSESSIONID},
                          data=urlencode(pl).encode("utf-8"), timeout=40)
    except requests.exceptions.RequestException as e:
        if _try < 2:
            time.sleep(3 * (_try + 1))
            return fetch(code, dv, pr, _try + 1)
        raise Unreachable(str(e)[:160])
    try:
        d = r.json()
    except Exception:
        body = r.text
        open(P("debug_response.html"), "w", encoding="utf-8").write(body)
        raise Stale()
    for v in d.values():
        if isinstance(v, list) and v:
            return v
    return []


# --------------------------------------------------------------------------- targets
POOLS = ['UIC1561', 'UIC1251', 'UIC1351', 'UIC1401', 'UIC1501', 'UIC1551', 'ASP2022', 'ASP2033',
         'UIC2151', 'UIC1751', 'QRM1001', 'ECO1101', 'ECO2101', 'ECO2102', 'STA2102',
         'UIC1805', 'UIC1806', 'YCA1006',
         'YCF1301', 'YCF1351', 'YCF1451', 'YCF1501', 'YCF1551', 'YCF1601', 'YCF1603', 'YCF1607']


def targets():
    """Every section that could plausibly be clicked on 8/25.

    Three sources, unioned — a section missing here is a section whose 1학년 gate we never
    check, so this errs wide on purpose:
      1. every row of the v3 search output (_v3_parts*/part_*.json)
      2. the recommendation and all its scored fallbacks (fallback.json)
      3. every section of every requirement/chapel/language pool (canonical_2026F.json)
    """
    want = set()

    n_rows = 0
    for fp in sorted(glob.glob(os.path.join(HERE, '_v3_parts*', 'part_*.json'))):
        try:
            blob = json.load(open(fp, encoding='utf-8'))
        except Exception:
            continue
        for row in (blob.get('rows') if isinstance(blob, dict) else blob) or []:
            n_rows += 1
            for key in ('requirements', 'electives'):
                for c in row.get(key) or []:
                    if str(c).count('-') == 2:
                        want.add(c)
            ch = row.get('chapel')
            if ch and str(ch).count('-') == 2:
                want.add(ch)
    print(f"  v3 search output : {n_rows} ranked rows -> {len(want)} distinct sections")

    try:
        fb = json.load(open(P('fallback.json'), encoding='utf-8'))
        before = len(want)
        want |= {c for c in fb['base']['sections'] if c.count('-') == 2}
        for d in fb.get('loss', {}).values():
            if d:
                want |= {c for c in d.get('sections', []) if c.count('-') == 2}
        print(f"  fallback chains  : +{len(want)-before}")
    except Exception as e:
        print(f"  (fallback.json unavailable: {e})")

    try:
        before = len(want)
        for s in json.load(open(P('canonical_2026F.json'), encoding='utf-8')):
            if s['c'].split('-')[0] in POOLS:
                want.add(s['c'])
        print(f"  requirement pools: +{len(want)-before}")
    except Exception as e:
        print(f"  (canonical_2026F.json unavailable: {e})")

    if STAR not in want:
        want.add(STAR)
        print(f"  ⚠ {STAR} was not in any source — added explicitly. Check why.")
    return sorted(want)


# --------------------------------------------------------------------------- verdict
def verdict(out):
    barred, scheme, plain, blank = [], [], 0, 0
    for sid, r in sorted(out.items()):
        if not r:
            blank += 1
            continue
        sy = [r.get(f'sy{i}PercpCnt') or 0 for i in range(1, 7)]
        cap, app = r.get('atnlcPercpCnt') or 0, r.get('cnt') or 0
        if any(sy):
            (barred if sy[0] == 0 else scheme).append((sid, cap, app, sy))
        else:
            plain += 1

    print("=" * 78)
    star = out.get(STAR)
    if star is None:
        print(f"⭐ {STAR}: NOT FETCHED — re-run. This is the 35.72 question (R242).")
    elif not star:
        print(f"⭐ {STAR}: no mileage row returned.")
        print("   That is NOT evidence of a bar — freshmen are invisible in this table (R7),")
        print("   and an absent row most often means no per-year scheme was registered.")
    else:
        sy = [star.get(f'sy{i}PercpCnt') or 0 for i in range(1, 7)]
        if not any(sy):
            print(f"⭐ {STAR}: ✅ NO per-year scheme in force -> a 1학년 is NOT barred (R2/R134).")
        elif sy[0] == 0:
            print(f"⭐ {STAR}: ⛔ BARRED — scheme in force and the 1학년 share is 0.")
            print("   The recommendation is dead. Re-run research_v3.py with it excluded;")
            print("   fallback.json already scores that branch at 28.911 (defer WCiv).")
        else:
            print(f"⭐ {STAR}: ✅ scheme in force but 1학년 share = {sy[0]}. Registrable.")
        print(f"   정원 {star.get('atnlcPercpCnt')}  신청 {star.get('cnt')}  sy1..sy6 {sy}")
    print("=" * 78)

    if barred:
        print(f"\n⛔ {len(barred)} SECTION(S) BAR 1학년 OUTRIGHT — scheme in force, 1학년 share = 0")
        for sid, cap, app, sy in barred:
            print(f"     {sid:16s} 정원 {cap:4d}  신청 {app:4d}  sy1..sy6 {sy}")
        print("\n   Any of these in a chosen timetable makes it UNREGISTRABLE.")
        print("   Re-run research_v3.py with them excluded before building the click order.")
    else:
        print("\n✅ NO section bars 1학년. Every candidate is registrable in principle.")
    if scheme:
        print(f"\n   {len(scheme)} section(s) run a per-year scheme WITH a non-zero 1학년 share:")
        for sid, cap, app, sy in scheme:
            print(f"     {sid:16s} 정원 {cap:4d}  1학년 몫 {sy[0]:4d}   sy1..sy6 {sy}")
    print(f"\n   {plain} section(s) have no per-year scheme at all (the normal case).")
    print(f"   {blank} section(s) returned no mileage row (not a bar — see R7).")
    print("\n⚠️ Do NOT read 배율 here as Iden's odds — the mileage round is 2학년+ only (R130).")
    print("   The ONLY thing in this file that binds him is the 1학년 share.")


# --------------------------------------------------------------------------- main
def main():
    global JSESSIONID
    JSESSIONID = cookie()
    print(f"cookie loaded ({len(JSESSIONID)} chars)\n")

    print("building the target list …")
    secs = targets()

    out = {}
    if os.path.exists(OUT) and os.path.getsize(OUT):
        try:
            out = json.load(open(OUT, encoding='utf-8'))
            print(f"\n  resuming: {len(out)} section(s) already fetched")
        except Exception:
            out = {}
    todo = [s for s in secs if s not in out]
    print(f"\nquerying {len(todo)} of {len(secs)} sections for Fall {SYY} …\n")

    def save():
        json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    shown_fields = bool(out)
    stale = offline = False
    for i, sid in enumerate(todo, 1):
        a, b, c = sid.split('-')
        try:
            rows = fetch(a, b, c)
        except Stale:
            stale = True
            break
        except Unreachable as e:
            offline = True
            print(f"  network error: {e}")
            break
        out[sid] = rows[0] if rows else {}
        if rows and not shown_fields:
            shown_fields = True
            print(f"  FIRST HIT {sid} — raw fields, so the keys below are VERIFIED not assumed:")
            print(f"    {sorted(rows[0])}")
            print(f"    {json.dumps(rows[0], ensure_ascii=False)[:400]}\n")
        if i % 20 == 0:
            save()
            print(f"  … {i}/{len(todo)}")
        time.sleep(0.25)

    save()

    if stale:
        print("\n" + "=" * 78)
        print("⛔ THE COOKIE EXPIRED (the server returned a login page, not data).")
        print(f"   Nothing is lost — {len(out)} section(s) are cached in fall2026_seats.json.")
        print("   1. Reload the portal tab so you are logged in again.")
        print("   2. Copy the NEW JSESSIONID into jsessionid.txt.")
        print("   3. Run this script again. It resumes from where it stopped.")
        print("=" * 78)
        return
    if offline:
        print("\n" + "=" * 78)
        print("⛔ COULD NOT REACH THE PORTAL (network / VPN / proxy).")
        print(f"   Nothing is lost — {len(out)} section(s) are cached.")
        print("   Check you can open the portal in Chrome, then run this again.")
        print("=" * 78)
        return

    print(f"\nwrote fall2026_seats.json — {len(out)} sections")
    print(f"   {OUT}")
    print("   ^ send me THIS file.\n")
    verdict(out)


if __name__ == '__main__':
    main()
