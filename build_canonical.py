"""
build_canonical.py (v2) — canonical Fall 2026 국제 dataset.

SOURCE CHANGED: raw_2026F.json (61 fields, straight from the portal API) replaces
강의목록_2026F.xlsx. The xlsx was a hand-picked 18-column export that lost the real
과목종별 and duplicated rows (R51, R94).

Every record is keyed by SECTION id (학정번호-분반), never by course code — the same
course can be offered by two departments with different category/language (R97).

Block semantics (R52, 수강편람 p.4 라-2):
  대면 (room code)     -> occupies TIME + PRESENCE
  실시간온라인          -> TIME only
  동영상(중복수강불가)   -> TIME only
  동영상콘텐츠          -> occupies NOTHING (explicitly overlappable)
Parenthesised periods count as occupied (R54). Free days use PRESENCE (D-10).

Output: canonical_2026F.json
"""
import json, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
DAYS = {'월':0,'화':1,'수':2,'목':3,'금':4,'토':5,'일':6}

def seg_blocks(seg):
    out=set(); day=None; num=''
    for ch in seg+'#':
        if ch.isdigit(): num+=ch; continue
        if num:
            if day is not None and int(num) >= 1: out.add((day,int(num)))
            num=''
        if ch in DAYS: day=DAYS[ch]
    return out

def classify(room_seg):
    if '중복수강불가' in room_seg: return 'video_block'   # time only
    if '동영상' in room_seg:       return 'video_free'    # nothing
    if '실시간' in room_seg:       return 'live_online'   # time only
    return 'inperson'                                     # time + presence

OCC_TIME = {'inperson','video_block','live_online'}
OCC_PRES = {'inperson'}

def main():
    raw = json.load(open(P('raw_2026F.json'), encoding='utf-8'))
    print(f"raw: {len(raw)} sections (both campuses)")
    recs, warn = [], collections.Counter()
    for r in raw:
        if str(r.get('campsDivNm')) != '국제': continue
        t  = str(r.get('lctreTimeNm') or '').strip()
        rm = str(r.get('lecrmNm') or '')
        if not t: warn['no_time']+=1; continue
        tsegs = [s for s in t.split('/') if seg_blocks(s)]
        rsegs = rm.split('/')
        if len(rsegs) != len(tsegs): warn['seg_mismatch']+=1
        time_b, pres_b, kinds = set(), set(), []
        for i, sg in enumerate(tsegs):
            b = seg_blocks(sg)
            rs = rsegs[i] if i < len(rsegs) else (rsegs[-1] if rsegs else '')
            k = classify(rs); kinds.append(k)
            if k in OCC_TIME: time_b |= b
            if k in OCC_PRES: pres_b |= b
        recs.append(dict(
            c   = str(r.get('subjtnbCorsePrcts')),        # SECTION id — the key
            code= str(r.get('subjtnb')),                  # course code (for display only)
            n   = str(r.get('subjtEngNm') or r.get('subjtNm') or ''),
            kn  = str(r.get('subjtNm') or ''),
            t   = t, room = rm,
            mode= str(r.get('subjtClNm') or ''),          # 대면/블랜디드/비대면
            cat = str(r.get('subsrtDivNm') or ''),        # ★ CC / MR / ME / MB / UICE / 대교 …
            cr  = float(r.get('cdt') or 0),
            p   = str(r.get('cgprfNm') or ''),
            dept= str(r.get('estblDeprtNm') or ''),
            yr  = str(r.get('hy') or ''),
            lang= str(r.get('srclnLctreLangDivCd') or ''),   # '10' = 영어
            note= str(r.get('atntnMattrDesc') or ''),
            grade=str(r.get('gradeEvlMthdDivNm') or ''),     # 절대/상대평가
            time=sorted(time_b), pres=sorted(pres_b), kinds=kinds))
    print(f"국제 with a time: {len(recs)}   warnings: {dict(warn) or 'none'}")
    ids = [x['c'] for x in recs]
    assert len(ids) == len(set(ids)), "duplicate section ids!"
    print("section ids unique ✓")
    print("\ncategory (subsrtDivNm) distribution:")
    for k, v in collections.Counter(x['cat'] for x in recs).most_common():
        print(f"   {v:5d}  {k}")
    json.dump(recs, open(P('canonical_2026F.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"\n-> canonical_2026F.json ({len(recs)} sections, keyed by section id)")

if __name__ == '__main__':
    main()


# ---- v3 (2026-08-06): QRM's OWN 과목종별 -------------------------------------
# 과목종별 is a property of (section x 개설전공), not of the section. The old fetch
# deduped sections first-seen-wins, so ECO1101/1103/1104 carried 경제학's label (MB)
# instead of 계량위험관리's (MR / ME). qrm_listings.json comes from refetch_listings.py
# and holds QRM's own label. `cat` = whatever query won; `qcat` = QRM's view (or None).
import json as _j, os as _o
_q = _o.path.join(HERE, 'qrm_listings.json') if 'HERE' in dir() else 'qrm_listings.json'
if _o.path.exists(_q):
    _Q = _j.load(open(_q, encoding='utf-8'))
    _out = _o.path.join(HERE, 'canonical_2026F.json') if 'HERE' in dir() else 'canonical_2026F.json'
    _c = _j.load(open(_out, encoding='utf-8'))
    for _s in _c:
        _s['qcat'] = (_Q.get(_s['c']) or {}).get('cat')
    _j.dump(_c, open(_out, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"qcat merged from qrm_listings.json ({sum(1 for x in _c if x['qcat'])} QRM sections)")
