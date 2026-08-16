# -*- coding: utf-8 -*-
"""
render_alternatives.py — for every slot in #1, EVERY other course that could fill it, priced.

WHY (R198)
----------
Iden, on being told Beginning Japanese is not an "equal swap" for Beginning Chinese:
    "oh really? I thought beginning japanese would be an equal swap"

He was right about the COURSE and the display was right about the SECTION, and the gap
between those two facts is the whole problem:

    UIC1805-01 Beginning Chinese   화1,목2,3   ┐ share a slot -> genuinely equal
    UIC1806-01 Beginning Japanese  화1,목2,3   ┘
    UIC1805-02 Beginning Chinese   화5,6,목4   <- what #1 actually uses; nothing matches it

So Japanese IS interchangeable as a course, and is NOT a free swap for the section #1 holds —
it costs **-21.25**, because its only compatible section starts at 화1, a 9:00.

`TOP50.html` showed only EQUAL swaps (delta exactly 0) and same-course 분반 alternates. Every
other option was invisible, which reads as "there are no other options". There are nineteen
for the Language slot alone. **A display that shows only the free moves implies the priced
moves do not exist.**

This page shows, for each slot: every course that can legally fill it, its time, its tier,
its resulting total, and the delta — including the ones that time-conflict, marked as such.
"""
import csv, json, os, html, collections, io, contextlib

import rank2 as R2, difficulty as DIFF
R2.LANG = set(DIFF.LANG_ALL)
import rank3, rank4
from rank2 import fast_score, eff_year, YEAR_PEN

HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    P, sig, sigs, SIGCODES, code = rank3.build()

byc = {}
for v in P.values():
    for s in v:
        byc.setdefault(s['c'], s)

ITEM = json.load(open(os.path.join(HERE, 'elective_items.json'), encoding='utf-8'))
V_REF = rank4.v_ref()
ROW = list(csv.DictReader(open(os.path.join(HERE, 'FINAL_ranked4.csv'),
                               encoding='utf-8-sig')))[0]
CHAPEL = ROW['chapel']
DEFER = frozenset(ROW['deferred'].split('+')) if ROW['deferred'] != '-' else frozenset()

# which pool can fill each slot
LANGP = [s for s in P['OPEN'] if code(s) in R2.LANG]
POOLS = {'Lang': LANGP, 'WCiv': P['WCiv'], 'LHP': P['LHP'], 'SciRD': P['SciRD'],
         'MR': P['MR']}


def score(codes, elective_codes):
    # ⚠️ R218. `+ [CHAPEL]` assumed #1 always TAKES chapel. Under the powerset search the
    # winner defers it ('-'), and byc['-'] raised KeyError. Also: comfort is scored on the
    # FIXED mask (R210) — this renderer was still passing the nominal one, so its numbers
    # did not match the ranker's.
    tm = pm = fm = 0
    for c in codes + ([CHAPEL] if CHAPEL and CHAPEL != '-' else []):
        s = byc[c]; tm |= s['tm']; pm |= s['pm']; fm |= s['fm']
    w, _ = fast_score(tm, pm, fm)
    yr = sum(YEAR_PEN(eff_year(byc[c], code)) for c in codes)
    dif = -DIFF.D_LANG * DIFF.GPA_GATE_MULT * sum(DIFF.steps(c) for c in codes)
    if 'Lang' in DEFER:
        dif -= DIFF.p_hard_if_deferred()[1] * DIFF.D_LANG
    items = tuple(sorted(ITEM.get(c, 'FREE') for c in elective_codes))
    ch = rank4.CHAPEL_BONUS if (CHAPEL and CHAPEL != '-') else rank4.CHAPEL_DEFER
    return w + yr + ch + dif + (rank4.V((DEFER, items)) - V_REF)


def conflicts(codes):
    tm = 0
    for c in codes + ([CHAPEL] if CHAPEL and CHAPEL != '-' else []):
        if tm & byc[c]['tm']:
            return True
        tm |= byc[c]['tm']
    return False


def alternatives_for(slot_code, base_codes, elective_codes, pool):
    base = score(base_codes, elective_codes)
    out = []
    seen = set()
    for s in pool:
        c = s['c']
        if c == slot_code or c in seen:
            continue
        seen.add(c)
        trial = [x for x in base_codes if x != slot_code] + [c]
        trial_el = [x for x in elective_codes if x != slot_code] + \
                   ([c] if slot_code in elective_codes else [])
        if slot_code in elective_codes:
            trial = base_codes[:]
            trial[trial.index(slot_code)] = c
            trial_el = trial_el
        if conflicts(trial):
            out.append((None, c, s))
        else:
            out.append((score(trial, trial_el), c, s))
    out.sort(key=lambda r: (r[0] is None, -(r[0] if r[0] is not None else 0)))
    return base, out


CSS = """<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:24px;
color:#1a1a1a;background:#fafafa;max-width:1100px}
h1{font-size:20px;margin:0 0 4px} h2{font-size:15px;margin:26px 0 6px;
border-bottom:2px solid #333;padding-bottom:3px}
.sub{color:#666;font-size:13px;margin-bottom:18px}
table{border-collapse:collapse;width:100%;font-size:12.5px;background:#fff}
th{background:#333;color:#fff;text-align:left;padding:5px 8px;font-weight:600}
td{padding:4px 8px;border-bottom:1px solid #eee}
.cur{background:#fff8dc;font-weight:600}
.pos{color:#0a7d28;font-weight:600}.neg{color:#b00}.na{color:#999}
.hard{background:#ffe9e9;color:#a00;padding:1px 5px;border-radius:3px;font-size:11px}
.easy{background:#e9f5ff;color:#06c;padding:1px 5px;border-radius:3px;font-size:11px}
.note{background:#fffbe6;border-left:3px solid #e8b500;padding:9px 12px;margin:14px 0;
font-size:13px}
</style>"""


def build():
    reqs = ROW['requirements'].split()
    els = ROW['electives'].split()
    base_codes = reqs + els
    h = [CSS, "<h1>Every alternative for every slot in #1 — priced</h1>"]
    h.append(f"<div class='sub'>#1 = <b>{float(ROW['score']):.3f}</b> · "
             f"defers <b>{ROW['deferred']}</b> · home {ROW['free_days']} · "
             f"{ROW['credits']} credits</div>")
    h.append("<div class='note'><b>Why this page exists.</b> TOP50.html shows only "
             "<i>equal</i> swaps — score delta exactly 0. Everything else was invisible, "
             "which reads as “there are no other options”. There are nineteen for the "
             "Language slot alone. Beginning Japanese is a perfectly good substitute for "
             "Beginning Chinese <i>as a course</i>; it is not free here because its only "
             "compatible section starts at 화1, a 9:00.</div>")

    slots = []
    for c in reqs:
        for name, pool in POOLS.items():
            if any(x['c'] == c for x in pool):
                slots.append((name, c, pool)); break
    for c in els:
        slots.append(('elective', c, [s for s in P['OPEN'] if code(s) not in R2.LANG]))

    for name, c, pool in slots:
        cur = byc[c]
        base, alts = alternatives_for(c, base_codes, els, pool)
        h.append(f"<h2>{name} — currently {c} · {html.escape(str(cur.get('n') or ''))} "
                 f"· {cur['t']}</h2>")
        h.append("<table><tr><th>section</th><th>course</th><th>time</th><th>prof</th>"
                 "<th>tier</th><th>total</th><th>vs #1</th></tr>")
        h.append(f"<tr class='cur'><td>{c}</td>"
                 f"<td>{html.escape(str(cur.get('n') or ''))}</td><td>{cur['t']}</td>"
                 f"<td>{html.escape(str(cur.get('p') or ''))}</td>"
                 f"<td>{'<span class=hard>HARD</span>' if DIFF.steps(c) else ''}</td>"
                 f"<td>{base:.3f}</td><td>— current</td></tr>")
        shown = 0
        for sc, ac, s in alts:
            if shown >= 25:
                break
            shown += 1
            tier = ('<span class=hard>HARD</span>' if DIFF.steps(ac)
                    else ('<span class=easy>easy</span>' if code(s) in R2.LANG else ''))
            if sc is None:
                h.append(f"<tr><td>{ac}</td><td>{html.escape(str(s.get('n') or ''))}</td>"
                         f"<td>{s['t']}</td><td>{html.escape(str(s.get('p') or ''))}</td>"
                         f"<td>{tier}</td><td class='na'>—</td>"
                         f"<td class='na'>time conflict</td></tr>")
            else:
                d = sc - base
                cls = 'pos' if d > 1e-9 else ('neg' if d < -1e-9 else '')
                lab = f"{d:+.3f}" if abs(d) > 1e-9 else "equal"
                h.append(f"<tr><td>{ac}</td><td>{html.escape(str(s.get('n') or ''))}</td>"
                         f"<td>{s['t']}</td><td>{html.escape(str(s.get('p') or ''))}</td>"
                         f"<td>{tier}</td><td>{sc:.3f}</td>"
                         f"<td class='{cls}'>{lab}</td></tr>")
        h.append("</table>")
    open(os.path.join(HERE, 'ALTERNATIVES.html'), 'w', encoding='utf-8').write(''.join(h))
    print(f"wrote ALTERNATIVES.html — {len(slots)} slots")


if __name__ == '__main__':
    build()
