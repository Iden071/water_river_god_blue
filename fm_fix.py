# -*- coding: utf-8 -*-
"""
fm_fix.py — build the FIXED-hour mask per SEGMENT instead of per course.

THE DEFECT
`rank2.py:340` sets
    s['fm'] = s['pm'] | (s['tm'] & ~s['pm'] if '실시간' in mode else 0)
which keys the fixed-hour mask off the COURSE-LEVEL mode string. When a section mixes a live
segment with a recorded one — mode `비대면(실시간+동영상)` — the whole non-presence time is
marked fixed, including the recorded half. `HANDOFF_2026-08-10` calls this "treated
conservatively, the live half cannot be separated". **It can.** `build_canonical` already
classifies every segment individually and stores the result in `kinds`.

Four modes, three distinct behaviours (R52, 수강편람 p.4 라-2):

| room segment      | blocks conflicts (tm) | on campus (pm) | fixed hour (fm) |
|-------------------|:---:|:---:|:---:|
| 강의실 (대면)        | ✔ | ✔ | ✔ |
| 실시간온라인          | ✔ | ✘ | **✔** — live, it pins the hour |
| 동영상(중복수강불가)   | ✔ | ✘ | **✘** — recorded; blocks registration, not your week |
| 동영상콘텐츠          | ✘ | ✘ | ✘ — explicitly overlappable |

`tm` and `pm` were already right. Only `fm` was wrong, and only where the two video kinds mix
with a live one.

MEASURED IMPACT (Fall 2026 국제, 341 sections): **exactly one section changes** —
`UIC1561-01-00 WESTERN CIVILIZATION`, 월7,8/수7 with rooms 실시간온라인/동영상(중복수강불가).
Its 수7 is recorded, so it is not a fixed hour. That section is in the recommended timetable,
where the correction is **−3.125** — the model had been crediting it with filling a Wednesday
hole that a shiftable recorded hour does not actually fill (R217's effect, in reverse).

⚠️ WHY THIS IS AN OVERRIDE AND NOT AN EDIT
`rank2.py:340` sits ABOVE the literal `    heap = []; cnt=[0]` at line 353, and
`rank3.build()` execs rank2's source text up to that marker — changing even its whitespace
breaks the ranker silently (INDEX trap #1). So this is applied at runtime to the built pools,
the same pattern R166/F3 used for the widened language pool.

    import rank3, fm_fix
    P, sig, sigs, SIGCODES, code = rank3.build()
    fm_fix.apply(P)          # <- one line, after build, before anything reads fm
"""
import json, os
import build_canonical as BC

HERE = os.path.dirname(os.path.abspath(__file__))
_CAN = None

# a segment whose hours are FIXED in the week: you must be somewhere at that hour
FIXED_KINDS = ('inperson', 'live_online')


def _canon():
    global _CAN
    if _CAN is None:
        _CAN = {s['c']: s for s in json.load(
            open(os.path.join(HERE, 'canonical_2026F.json'), encoding='utf-8'))}
    return _CAN


def fm_of(sec):
    """The fixed-hour mask for one section, classified per segment."""
    can = _canon().get(sec['c'])
    if not can:
        return sec.get('fm', sec.get('pm', 0))
    rsegs = str(can.get('room') or '').split('/')
    fm = 0
    for i, sg in enumerate(str(can.get('t') or '').split('/')):
        blocks = BC.seg_blocks(sg)
        rs = rsegs[i] if i < len(rsegs) else (rsegs[-1] if rsegs else '')
        if BC.classify(rs) in FIXED_KINDS:
            for (d, p) in blocks:
                fm |= 1 << (d * 16 + p)
    return fm


def apply(P, verbose=True):
    """Rewrite fm in place across every pool. Returns the list of changed section ids."""
    changed, seen = [], set()
    for pool in P.values():
        for s in pool:
            new = fm_of(s)
            if s['c'] not in seen and new != s.get('fm'):
                changed.append(s['c'])
            seen.add(s['c'])
            s['fm'] = new
    if verbose and changed:
        print(f"  fm_fix: {len(changed)} section(s) re-classified per segment: "
              f"{', '.join(sorted(set(changed)))}")
    return changed


if __name__ == '__main__':
    import rank3
    P = rank3.build()[0]
    ch = apply(P)
    DN = '월화수목금토일'

    def show(m):
        o = []
        for d in range(7):
            ps = [p for p in range(1, 16) if (m >> (d * 16 + p)) & 1]
            if ps:
                o.append(DN[d] + ','.join(map(str, ps)))
        return '/'.join(o) or '—'
    byc = {s['c']: s for v in P.values() for s in v}
    for c in sorted(set(ch)):
        can = _canon()[c]
        print(f"\n  {c}  {byc[c].get('n','')[:40]}")
        print(f"     {can['t']}   rooms {can['room']}")
        print(f"     tm {show(byc[c]['tm'])} · pm {show(byc[c]['pm'])} · fm now {show(byc[c]['fm'])}")
