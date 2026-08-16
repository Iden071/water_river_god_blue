# -*- coding: utf-8 -*-
"""
fetch_past_terms.py — pull PAST-TERM course catalogues (esp. 국제 SPRING).

WHY THIS EXISTS
---------------
K — what a deferred requirement costs the semester that receives it — is a function of a
section's TIME MASK, not of which course it is (R230). Three of the six deferral branches
(MR · WCiv · Lang·easy) land in a 국제 **Spring** semester, but every one of them is currently
scored against a filler pool built from the **Fall 2026** catalogue, because that is the only
catalogue on disk. Measured, that substitution shifts median K by about +2.07 (R231) — small,
but the narrowest branch margin under debate is 1.84, and the estimate itself rests on only
19 Spring masks scraped out of `mileage_history.json`.

One real Spring catalogue replaces the whole substitution and lifts that pool from 19 masks
to ~100. That is what this fetches.

  ⚠️  The sandbox gets proxy 403 on every Yonsei host. This must run on YOUR machine.

------------------------------------------------------------------------------------------
HOW TO RUN  — three steps, and only step 2 is fiddly
------------------------------------------------------------------------------------------
 1. Log into the portal in Chrome and LEAVE THE TAB OPEN:
      https://underwood1.yonsei.ac.kr/com/lgin/SsoCtr/initExtPageWork.do?link=handbStdntBusns

 2. Get the cookie:  F12  ->  Application  ->  Cookies  ->  underwood1.yonsei.ac.kr
    Click JSESSIONID, copy its **Value** (a long string ending in something like
    `.aGFrc2FfZG9tYWluL2hha3NhMV8x`).
    Paste it into a plain text file named  jsessionid.txt  next to this script.
    (A file, not the source — so you can refresh it without editing code.)

 3. Run:   python fetch_past_terms.py

WHAT IT DOES THAT THE OLD FETCHERS DID NOT
  · **Resumable.** Every (term, query) is saved the moment it returns. If the cookie expires
    mid-run — it will, they are short-lived — just refresh jsessionid.txt and run it again.
    It picks up exactly where it stopped. Nothing is re-fetched.
  · **Fails loudly and usefully.** A stale cookie returns an SSO HTML page, not JSON. It says
    so in one line instead of dying on a JSONDecodeError.
  · **Un-truncates itself.** The endpoint silently caps a query at 200 rows. On a cap hit it
    automatically re-queries split by 학년, which the old script only warned about.
  · **Ordered by value.** Spring 2026 국제 comes first, so a partial run is still useful.
  · **Verifies its own output** and tells you exactly which file to send back.

Safe to re-run any number of times.
"""
import json, os, sys, time, collections
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    sys.exit("⛔ needs `requests`.  Run:  pip install requests")

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
STATE = P('_fetch_state')
os.makedirs(STATE, exist_ok=True)

URL = "https://underwood1.yonsei.ac.kr/sch/sles/SlessyCtr/findAtnlcHandbList.do"
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Referer": "https://underwood1.yonsei.ac.kr/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
CAP = 200

# (year, smtDivCd) — 10 = Spring, 20 = Fall. Ordered MOST USEFUL FIRST.
TARGETS = [
    ("2026", "10"),   # ⭐ Spring 2026 — the gap that matters. You lived through this one.
    ("2025", "10"),   # Spring 2025 — a second Spring; lets Spring-to-Spring drift be measured
    ("2025", "20"),   # Fall 2025 — 신촌 year-drift check
    ("2024", "10"),   # older Springs: bonus, only if the portal still serves them
    ("2024", "20"),
]

QUERIES = [
    ('교양기초', 's11000', '', ''),
    ('대학교양 - 문학과예술', 's11001', '30109', ''),
    ('대학교양 - 인간과역사', 's11001', '30110', ''),
    ('대학교양 - 언어와표현', 's11001', '30111', ''),
    ('대학교양 - 가치와윤리', 's11001', '30112', ''),
    ('대학교양 - 국가와사회', 's11001', '30113', ''),
    ('대학교양 - 지역과세계', 's11001', '30114', ''),
    ('대학교양 - 논리와수리', 's11001', '30115', ''),
    ('대학교양 - 자연과우주', 's11001', '30116', ''),
    ('대학교양 - 생명과환경', 's11001', '30117', ''),
    ('대학교양 - 정보와기술', 's11001', '30118', ''),
    ('대학교양 - 체육과건강', 's11001', '30119', ''),
    ('자율선택', 's11002', '', ''),
    ('RC교육', 's1160', '', ''),
    ('UIC - 1011(미확인)', 's1125', '1011', ''),
    ('UIC - 1012(미확인)', 's1125', '1012', ''),
    ('UIC - 1015(미확인)', 's1125', '1015', ''),
    ('UIC - 경제학', 's1125', '1013', ''),
    ('UIC - 국제학', 's1125', '1014', ''),
    ('UIC - 정치외교학', 's1125', '1016', ''),
    ('UIC - 사회정의리더십', 's1125', '1020', ''),
    ('UIC - 계량위험관리', 's1125', '1021', ''),
    ('UIC - 과학기술정책', 's1125', '1022', ''),
    ('UIC - 지속개발협력', 's1125', '1023', ''),
    ('UIC - 나노과학공학', 's1125', '1024', ''),
    ('UIC - 에너지환경융합', 's1125', '1025', ''),
    ('UIC - 바이오융합', 's1125', '1026', ''),
    ('UIC - 공통교과과정', 's1125', '1805', ''),
    ('UIC - 정보/인터랙션디자인', 's1125', '1818', ''),
    ('UIC - 아시아학', 's1125', '1819', ''),
    ('UIC - 창의기술경영', 's1125', '1820', ''),
    ('UIC - 문화디자인경영', 's1125', '1821', ''),
    ('공통', 's1190', '', ''),
    ('상경대학', 's1102', '', ''),
    ('경영대학', 's11021', '', ''),
    ('이과대학', 's1103', '', ''),
    ('인공지능융합대학', 's1106', '', ''),
]


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


def fetch(syy, smt, univ, facly, hy, _try=0):
    payload = {
        "_menuId": "MTA5MzM2MTI3MjkzMTI2NzYwMDA=", "_menuNm": "", "_pgmId": "NDE0MDA4NTU1NjY=",
        "@d1#syy": syy, "@d1#smtDivCd": smt, "@d1#campsBusnsCd": "s1",
        "@d1#univCd": univ, "@d1#faclyCd": facly, "@d1#hy": hy, "@d1#cdt": "%",
        "@d1#kwdDivCd": "1", "@d1#searchGbn": "1", "@d1#kwd": "", "@d1#allKwd": "",
        "@d1#engChg": "", "@d1#prnGbn": "false", "@d1#lang": "", "@d1#campsDivCd": "",
        "@d1#stuno": "", "@d#": "@d1#", "@d1#": "dmCond", "@d1#tp": "dm",
    }
    try:
        r = requests.post(URL, headers=HEADERS, cookies={"JSESSIONID": JSESSIONID},
                          data=urlencode(payload).encode("utf-8"), timeout=40)
    except requests.exceptions.RequestException as e:
        # a dropped wifi / VPN / proxy should not dump a traceback — retry, then stop cleanly
        if _try < 2:
            time.sleep(3 * (_try + 1))
            return fetch(syy, smt, univ, facly, hy, _try + 1)
        raise Unreachable(str(e)[:160])
    try:
        data = r.json()
    except Exception:
        body = r.text
        open(P("debug_response.html"), "w", encoding="utf-8").write(body)
        if "<html" in body[:400].lower() or "login" in body.lower() or "sso" in body.lower():
            raise Stale()
        print(f"    [NOT JSON] HTTP {r.status_code} len={len(body)} — saved debug_response.html")
        raise Stale()
    for v in data.values():
        if isinstance(v, list):
            return v
    return []


def fetch_query(syy, smt, nm, univ, facly, hy):
    """One query, auto-split by 학년 if the server caps it at 200 rows."""
    rows = fetch(syy, smt, univ, facly, hy)
    if len(rows) < CAP:
        return rows, False
    seen, merged = set(), []
    for h in ('1', '2', '3', '4', '5', '6'):
        part = fetch(syy, smt, univ, facly, h)
        for r in part:
            k = (r.get('subjtnbCorsePrcts'), r.get('hy'))
            if k not in seen:
                seen.add(k); merged.append(r)
        time.sleep(0.2)
    return (merged, True) if len(merged) >= len(rows) else (rows, True)


def term_label(syy, smt):
    return f"{syy}-{'1' if smt == '10' else '2'}"


def main():
    global JSESSIONID
    JSESSIONID = cookie()
    print(f"cookie loaded ({len(JSESSIONID)} chars)\n")
    stale = offline = False
    for syy, smt in TARGETS:
        lab = term_label(syy, smt)
        done_n = 0
        print(f"=== {lab} ({'Spring' if smt == '10' else 'Fall'} {syy}) ===")
        for i, (nm, u, f, h) in enumerate(QUERIES, 1):
            sf = os.path.join(STATE, f"{lab}__{i:02d}.json")
            if os.path.exists(sf) and os.path.getsize(sf):
                done_n += 1
                continue
            try:
                rows, split = fetch_query(syy, smt, nm, u, f, h)
            except Stale:
                stale = True
                break
            except Unreachable as e:
                offline = True
                print(f"    network error: {e}")
                break
            for r in rows:
                r["_분류"] = nm
            json.dump(rows, open(sf, "w", encoding="utf-8"), ensure_ascii=False)
            done_n += 1
            print(f"  [{i:2}/{len(QUERIES)}] {nm:26s} {len(rows):4d} rows"
                  f"{'  (un-truncated by 학년)' if split else ''}")
            time.sleep(0.25)
        if stale or offline:
            break
        print(f"  {lab}: {done_n}/{len(QUERIES)} queries cached\n")

    if offline:
        print("\n" + "=" * 78)
        print("⛔ COULD NOT REACH THE PORTAL (network / VPN / proxy).")
        print("   Nothing is lost — everything already fetched is cached.")
        print("   Check you can open the portal in Chrome, then run this again.")
        print("=" * 78)
    if stale:
        print("\n" + "=" * 78)
        print("⛔ THE COOKIE EXPIRED (the server returned a login page, not data).")
        print("   Nothing is lost — every query already fetched is cached.")
        print("   1. Reload the portal tab so you are logged in again.")
        print("   2. Copy the NEW JSESSIONID into jsessionid.txt.")
        print("   3. Run this script again. It resumes from where it stopped.")
        print("=" * 78)

    # ---------------- assemble + verify ----------------
    bundles = collections.defaultdict(list)
    for fn in sorted(os.listdir(STATE)):
        if not fn.endswith('.json'):
            continue
        lab = fn.split('__')[0]
        try:
            bundles[lab] += json.load(open(os.path.join(STATE, fn), encoding='utf-8'))
        except Exception:
            pass
    if not bundles:
        return

    DAY = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}

    def masks(rows, camp):
        out = set()
        for r in rows:
            if r.get('campsDivNm') != camp:
                continue
            t = r.get('lctreTimeNm')
            if not t:
                continue
            tm, cur = 0, None
            for tok in str(t).replace('/', ',').split(','):
                tok = tok.strip()
                if not tok:
                    continue
                if tok[0] in DAY:
                    cur = DAY[tok[0]]; tok = tok[1:]
                if cur is None:
                    continue
                num = ''.join(c for c in tok if c.isdigit())
                if num and 1 <= int(num) <= 15 and cur < 7:
                    tm |= 1 << (cur * 16 + int(num))
            if tm and bin(tm).count('1') >= 3:
                out.add(tm)
        return out

    have = set()
    try:
        cur = json.load(open(P('raw_2026F.json'), encoding='utf-8'))
        cur = cur if isinstance(cur, list) else list(cur.values())[0]
        have = masks(cur, '국제') | masks(cur, '신촌')
    except Exception:
        pass

    out = {}
    print("\n" + "=" * 78)
    print("WHAT WAS FETCHED")
    print("=" * 78)
    print(f"  {'term':8s} {'sections':>9} {'국제':>6} {'신촌':>6} {'≥3h masks':>10} {'NEW vs Fall 2026':>17}")
    for lab, rows in sorted(bundles.items()):
        secs = {r.get('subjtnbCorsePrcts') for r in rows if r.get('subjtnbCorsePrcts')}
        mi, ms = masks(rows, '국제'), masks(rows, '신촌')
        new = (mi | ms) - have
        out[lab] = rows
        print(f"  {lab:8s} {len(secs):9d} {len(mi):6d} {len(ms):6d} {len(mi | ms):10d} {len(new):17d}")
    json.dump(out, open(P('past_terms.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print("\n  ✅ wrote past_terms.json")
    print(f"     {P('past_terms.json')}")
    print("     ^ send me THIS file. Nothing else is needed.")
    missing = [term_label(y, s) for y, s in TARGETS
               if len([f for f in os.listdir(STATE)
                       if f.startswith(term_label(y, s) + '__')]) < len(QUERIES)]
    if missing:
        print(f"\n  ⚠ incomplete terms: {', '.join(missing)} — re-run with a fresh cookie to finish.")
        print("     A partial file is still useful: 2026-1 alone closes the main gap.")


if __name__ == '__main__':
    main()
