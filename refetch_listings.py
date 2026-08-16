"""
refetch_listings.py (v4) — KEEP EVERY FIELD *AND* EVERY LISTING.

v3 BUG: a section was deduped on subjtnbCorsePrcts, first-seen-wins. But 과목종별
(subsrtDivNm) is a property of (section x 개설전공), NOT of the section. ECO1103-04-00
is MB under 경제학 and ME under 계량위험관리 — the same row. Because the 경제학 query runs
before 계량위험관리, every ECO1101/1103/1104 kept the WRONG label. 129 sections affected.
v4 keeps one record per (section, query) listing and never collapses them.

Self-contained: the 37 queries are embedded, and all outputs are written next to
this script — so it does not matter which folder you run it from.
  * JSONDecodeError -> the server did not return JSON. Now the response is
                    inspected and the first 400 chars are printed/saved so we can
                    see what actually came back (usually an SSO/login HTML page).

RUN
  1. Log into the portal in Chrome and keep that tab open:
     https://underwood1.yonsei.ac.kr/com/lgin/SsoCtr/initExtPageWork.do?link=handbStdntBusns
  2. F12 > Application > Cookies > https://underwood1.yonsei.ac.kr > copy JSESSIONID
  3. Paste below, run:  python refetch_full.py
If it still fails, send me debug_response.html — that tells us exactly why.
"""
import json, sys, collections, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
from urllib.parse import urlencode
import requests

JSESSIONID = "UC7A2FIPDq15OtkMsdLXh4LDufhwfAxodvz7aUfo7DMQKZxITxHgejglPaU9JsPS.aGFrc2FfZG9tYWluL2hha3NhMV8x"      # <<<<<< only thing to change

URL = "https://underwood1.yonsei.ac.kr/sch/sles/SlessyCtr/findAtnlcHandbList.do"
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Referer": "https://underwood1.yonsei.ac.kr/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
SYY, SMT, CAP = "2026", "20", 200

# ---------- 1. queries (embedded — no dependency on any other file) ----------
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
print(f'{len(QUERIES)} queries embedded')

# ---------- 2. fetch, with real diagnostics ----------
def fetch(nm, univ, facly, hy):
    payload = {
        "_menuId": "MTA5MzM2MTI3MjkzMTI2NzYwMDA=",
        "_menuNm": "",
        "_pgmId": "NDE0MDA4NTU1NjY=",
        "@d1#syy": SYY,
        "@d1#smtDivCd": SMT,
        "@d1#campsBusnsCd": "s1",
        "@d1#univCd": univ,
        "@d1#faclyCd": facly,
        "@d1#hy": hy,
        "@d1#cdt": "%",
        "@d1#kwdDivCd": "1",
        "@d1#searchGbn": "1",
        "@d1#kwd": "",
        "@d1#allKwd": "",
        "@d1#engChg": "",
        "@d1#prnGbn": "false",
        "@d1#lang": "",
        "@d1#campsDivCd": "",
        "@d1#stuno": "",
        "@d#": "@d1#",
        "@d1#": "dmCond",
        "@d1#tp": "dm",
    }
    r = requests.post(URL, headers=HEADERS, cookies={"JSESSIONID": JSESSIONID},
                      data=urlencode(payload).encode("utf-8"), timeout=30)
    body = r.text
    try:
        data = r.json()
    except Exception:
        open(P("debug_response.html"), "w", encoding="utf-8").write(body)
        print(f"\n  [NOT JSON]  HTTP {r.status_code}  len={len(body)}")
        print("  content-type:", r.headers.get("Content-Type"))
        print("  first 400 chars ------------------------------------")
        print("  " + body[:400].replace("\n", "\n  "))
        print("  ---------------------------------------------------")
        print("  full body saved to debug_response.html")
        if "login" in body.lower() or "sso" in body.lower() or "<html" in body[:200].lower():
            print("  >> looks like a login/SSO page: the JSESSIONID is not authenticated.")
            print("     Re-copy it while the portal course-list page is open, then retry.")
        sys.exit(1)
    for k, v in data.items():
        if isinstance(v, list) and v:
            if len(v) >= CAP:
                print(f"  [CAP] {nm}: {len(v)} rows — may be truncated")
            return v
    return []

listings = []
per_query = {}
for i, (nm, u, f, h) in enumerate(QUERIES, 1):
    got = fetch(nm, u, f, h)
    per_query[nm] = len(got)
    for r in got:
        if r.get("subjtnbCorsePrcts"):
            r["_분류"] = nm            # which query produced THIS listing
            listings.append(r)         # <-- no dedup: every listing is kept
    print(f"[{i:2}/{len(QUERIES)}] {nm:28s} {len(got):4} rows (running total {len(listings)})")

json.dump(listings, open(P("raw_2026F_listings.json"), "w", encoding="utf-8"),
          ensure_ascii=False)

sec = collections.defaultdict(list)
for r in listings:
    sec[r["subjtnbCorsePrcts"]].append(r)
multi = {k: v for k, v in sec.items() if len({x.get("subsrtDivNm") for x in v}) > 1}
print(f"\nwrote raw_2026F_listings.json")
print(f"  {len(listings)} listings over {len(sec)} distinct sections")
print(f"  {len(multi)} sections carry MORE THAN ONE 과목종별 <-- these were silently wrong in v3")

# QRM's own view: what does 계량위험관리 call each of its courses?
QV = "UIC - 계량위험관리"
qrm = {k: [x for x in v if x["_분류"] == QV] for k, v in sec.items()}
qrm = {k: v[0] for k, v in qrm.items() if v}
print(f"\n=== QRM (계량위험관리) lists {len(qrm)} sections. Its OWN 과목종별 for each: ===")
by = collections.defaultdict(list)
for k, r in qrm.items():
    by[r.get("subsrtDivNm")].append(k.split("-")[0])
for cat, cs in sorted(by.items()):
    print(f"  {cat:6s} {' '.join(sorted(set(cs)))}")
open(P("qrm_listings.json"), "w", encoding="utf-8").write(
    json.dumps({k: {"cat": r.get("subsrtDivNm"), "hy": r.get("hy"),
                    "camps": r.get("campsNm") or r.get("campsDivNm")}
                for k, r in qrm.items()}, ensure_ascii=False, indent=1))
print("wrote qrm_listings.json")

# report multi-label sections explicitly so nothing is hidden again
if multi:
    print("\n=== sections whose 과목종별 DEPENDS on which major lists them ===")
    for k in sorted(multi)[:60]:
        lab = " · ".join(f"{x['_분류'].replace('UIC - ','')}={x.get('subsrtDivNm')}"
                         for x in multi[k])
        print(f"  {k:15s} {lab}")
    if len(multi) > 60:
        print(f"  ... and {len(multi)-60} more")

# one representative per section, for the field scan only.
# NOTE: v3's second fetch loop used to live here and re-fetched all 37 queries, then
# overwrote raw_2026F.json with the DEDUPED rows — i.e. it re-introduced the exact bug
# this script exists to fix. Removed. raw_2026F.json is now never written by v4.
rows = [v[0] for v in sec.values()]

# ---------- 3. identify 과목종별 by its VALUES, not its name ----------
MARK = {"전필", "전선", "교양", "일선", "교필", "교선", "전공필수", "전공선택", "전공기초"}
fields = sorted({k for r in rows for k in r})
out, hits = [f"{len(rows)} sections, {len(fields)} fields\n"], []
for k in fields:
    vals = {str(r.get(k)) for r in rows if r.get(k) not in (None, "")}
    if vals & MARK:
        hits.append(k)
        out.append(f"*** {k}  <-- 과목종별 CANDIDATE  values={sorted(vals)[:15]}")
    else:
        out.append(f"    {k}  ({len(vals)} distinct)  {sorted(vals)[:6]}")
# also flag anything that looks like a capacity field
CAPWORDS = ("정원", "여석", "capa", "cnt", "num", "pesn")
for k in fields:
    if any(w in k.lower() for w in CAPWORDS):
        vals = [r.get(k) for r in rows[:5]]
        out.append(f"##  {k}  possible 정원/여석 field, samples={vals}")
open(P("field_report.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote field_report.txt")
print("\n과목종별 candidates:", hits or "NONE — send me field_report.txt")
for k in hits:
    print(f"  {k}:", dict(collections.Counter(str(r.get(k)) for r in rows).most_common(12)))
