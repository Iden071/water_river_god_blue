# -*- coding: utf-8 -*-
"""
pools_past.py — real per-(campus, season) section pools, built from six observed terms.

Replaces the Fall-2026-for-everything substitution (G-9). `b1_curve` scored 국제 **Spring**
receiving semesters against the **Fall 2026** 국제 catalogue because that was the only one on
disk; R231 bounded that at about +2.07 on median K from 19 scraped masks. With
`past_terms.json` (R232) there are three real Springs and three real Falls, so the pool for a
receiving semester can simply be the right campus in the right season.

WHAT A POOL IS
  the union of distinct ≥3h (time mask, presence mask) signatures observed at that campus in
  that season, across every year held. Union rather than most-recent-year, because the pool
  answers "what could plausibly be on offer", not "what was on offer once".

⚠️ presence: the catalogue's 강의실 marks 동영상콘텐츠 hours, which occupy a nominal slot but
no campus presence. Parsed the same way `build_canonical` does, so pm ⊆ tm.
"""
import json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
DAY = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
DN = '월화수목금토일'
MIN_HOURS = 3

_TERMS = None


def terms():
    """{'2024-1': [rows], ...} — the five fetched terms plus Fall 2026 from raw_2026F."""
    global _TERMS
    if _TERMS is None:
        d = json.load(open(os.path.join(HERE, 'past_terms.json'), encoding='utf-8'))
        raw = json.load(open(os.path.join(HERE, 'raw_2026F.json'), encoding='utf-8'))
        d['2026-2'] = raw if isinstance(raw, list) else list(raw.values())[0]
        _TERMS = d
    return _TERMS


def parse(t):
    """'화5,6/목4' -> time mask. Parenthesised blocks are kept (they hold a nominal slot, R54).

    ⛔ REWRITTEN 2026-08-16 (R264). The previous split-on-comma version did NOT do what its
    own docstring said. `'월3,4,수3(수4)'.split(',')` yields the token `'수3(수4)'`;
    `.strip('()')` strips nothing (neither end is a paren) and
    `''.join(c for c in tok if c.isdigit())` yields `'34'`, which fails the 1..15 range test —
    so the entire 수 block was DISCARDED. Worse, it also FABRICATED hours:

        월3,4,수3(수4)      -> 월3,4            (수3,수4 lost)
        화1,2,목1(목2)      -> 화1,2/목12       (목12 does not exist)
        수6,7(수8,9)        -> 수6,9            (수7,수8 lost, 수9 invented)
        금7(금8,9,10,11)    -> 금9,10,11        (금7,금8 lost)

    66% of 신촌-Fall hard-tier language section-observations were mis-parsed, which
    manufactured four cheap 2-hour geometries that exist in no catalogue. `min()` over the
    receiving geometries then selected one of them, so `kdefer('Lang')` read −4.725 instead
    of 16.615 and the deferral verdict inverted. See R264.

    This now delegates to the char-scan parser the live path already uses
    (`build_canonical.seg_blocks`), which R49 introduced on 2026-08-04 to fix this identical
    defect in `fetch_2026_fall.py` — a fix `pools_past` never adopted.
    """
    try:
        from build_canonical import seg_blocks
    except Exception:
        seg_blocks = None
    s = str(t or '')
    if seg_blocks is not None:
        tm = 0
        for d, p in seg_blocks(s):
            if 0 <= d < 7 and 1 <= p <= 15:
                tm |= 1 << (d * 16 + p)
        return tm
    # inline fallback with identical semantics — a digit run closes on any non-digit, and the
    # most recent day character governs it, so parentheses are transparent rather than fatal.
    tm, day, num = 0, None, ''
    for ch in s + '#':
        if ch.isdigit():
            num += ch
            continue
        if num:
            if day is not None and 1 <= int(num) <= 15 and day < 7:
                tm |= 1 << (day * 16 + int(num))
            num = ''
        if ch in DAY:
            day = DAY[ch]
    return tm


def presence(row):
    """Hours that put him on campus: nominal minus any 동영상콘텐츠 (recorded) block."""
    tm = parse(row.get('lctreTimeNm'))
    room = str(row.get('lecrmNm') or '')
    if '동영상' not in room:
        return tm
    # a recorded block is written as a parenthesised segment of the time string
    keep = 0
    cur = None
    for seg in str(row.get('lctreTimeNm') or '').split('/'):
        seg = seg.strip()
        rec = seg.startswith('(') and seg.endswith(')')
        m = parse(seg)
        if not rec:
            keep |= m
    return keep if keep else 0


def show(m):
    out = []
    for d in range(7):
        ps = [p for p in range(1, 16) if (m >> (d * 16 + p)) & 1]
        if ps:
            out.append(DN[d] + ','.join(map(str, ps)))
    return '/'.join(out)


SEASON = {'1': 'S', '2': 'F'}


def pool(campus, season, years=None, min_hours=MIN_HOURS):
    """Distinct (tm, pm) signatures for a campus in a season, unioned over years."""
    sigs, src = {}, collections.Counter()
    for lab, rows in terms().items():
        y, s = lab.split('-')
        if SEASON[s] != season:
            continue
        if years and y not in years:
            continue
        for r in rows:
            if r.get('campsDivNm') != campus:
                continue
            tm = parse(r.get('lctreTimeNm'))
            if not tm or bin(tm).count('1') < min_hours:
                continue
            pm = presence(r)
            if (tm, pm) not in sigs:
                sigs[(tm, pm)] = lab
                src[lab] += 1
    out = sorted(sigs, key=lambda g: bin(g[0]).count('1'))
    return out, dict(src)


def course_geometries(code, campus=None, season=None):
    """Per-term observed (tm, pm) for one course — the empirical predictive distribution."""
    out = collections.OrderedDict()
    for lab in sorted(terms()):
        y, s = lab.split('-')
        if season and SEASON[s] != season:
            continue
        got = set()
        for r in terms()[lab]:
            if str(r.get('subjtnb')) != code:
                continue
            if campus and r.get('campsDivNm') != campus:
                continue
            tm = parse(r.get('lctreTimeNm'))
            if tm:
                got.add((tm, presence(r)))
        if got:
            out[lab] = sorted(got)
    return out


if __name__ == '__main__':
    print("POOL SIZES — distinct ≥3h (tm,pm) signatures")
    print(f"  {'campus/season':16s} {'union':>6}   contributed by")
    for camp in ('국제', '신촌'):
        for sea, nm in (('S', 'Spring'), ('F', 'Fall')):
            p, src = pool(camp, sea)
            print(f"  {camp} {nm:9s} {len(p):6d}   {src}")
    print()
    print("WHAT b1_curve USED INSTEAD (Fall 2026 only, for BOTH seasons):")
    import b1_curve as B
    for camp in ('국제', '신촌'):
        print(f"  {camp}: {len(B.pool_for(camp))}")
