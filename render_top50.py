"""render_top50.py — standalone browsable HTML of the top-50 timetables.

Reads FINAL_ranked4.csv + canonical_2026F.json, writes TOP50.html.

⚠️ REPOINTED 2026-08-09 (R191). This read `FINAL_ranked3.csv` for a full session AFTER the
ranker was replaced, so the HTML — the one artefact Iden actually opens — showed a #1 that
had since fallen to roughly rank 4000. A renderer silently reading a superseded input is the
same failure class as a verifier silently omitting a term.
⚠️ rank4 scores are NOT comparable to rank3's: they contain the value of the rest of the
degree (DESIGN_v2 §5). Never put the two in one column.
Self-contained: no CDN, no network, opens straight from disk.
Grid shows PRESENCE vs TIME distinctly (R129) — hatched = online, holds an hour
but costs no trip home, which is the whole point of the free-day model.
"""
import csv, json, collections, html, io, contextlib, os

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)   # R177: this file used P() without defining it

KIND = {'MR':0,'ME':1,'WCiv':2,'LHP':3,'SciRD':4,'Lang':5,'Chapel':6,'ELEC':7}
KN = ["Major required","Major elective","Western Civ","World Hist/Lit","Research Design","Language","Chapel","Free elective"]
KC = ["#b8562f","#c98a2e","#4a7c9e","#5b8c6a","#7a6ba8","#a35d7e","#8a8a80","#b0b0a6"]
ME = {'ECO1103','ECO1104','ECO1105','QRM2001','QRM2002','QRM2004','QRM2100','QRM2101','QRM2102',
      'STA2102','STA2104','STA2105','QRM3001','QRM3002','QRM3007','ECO3104','ECO3127','ECO3130',
      'ECO3134','QRM4001','QRM4807','QRM4808','QRM4809','STA4103','ECO4115','ECO4862','ECO4865','STP3007'}
MR = {'QRM1001','ECO1101','ECO2101','ECO2102','QRM3003','QRM3004','QRM3005'}
REQ = {'UIC1561':'WCiv','UIC1251':'LHP','UIC1351':'LHP','UIC1401':'LHP','UIC1501':'LHP',
       'UIC1551':'LHP','ASP2022':'LHP','ASP2033':'LHP','UIC2151':'SciRD','UIC1805':'Lang',
       'UIC1806':'Lang','YCA1006':'Chapel'}
PT = ["","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00"]
DAYS = ["월","화","수","목","금"]

def twins():
    """Sections the model genuinely scores IDENTICALLY, so swapping one for another is free.

    ⛔ REWRITTEN 2026-08-09 (R197). Iden:
        "i'm 100% sure these are not equal swaps. Language is a requirement. ... if you swap
         any of those and the timetable gets an equal score, that's wrong right?"
    He is right. The old version grouped on (time, presence, bonus, credits) ALONE and so
    offered `YCB1101 WRITING` as an "equal swap" for `UIC1805 BEGINNING CHINESE`. They do
    share a time slot — but UIC1805 **fills the Language requirement** and YCB1101 does not.
    Making that swap leaves Language unsatisfied, which on the live #1 (already deferring
    Intro to QRM) means TWO deferrals — outside `MAX_DEFER = 1`, i.e. not merely unequal but
    outside the space the ranking was computed over.

    Two further faults in the old key, both the R192 class — a renderer running a dead model:
      · it used `_role`, which rank4 DELETED (R182);
      · it ignored the ledger item, so a Major Elective and a free elective in the same slot
        were called equal though they differ by ~31 of continuation value.

    An equal swap now requires ALL of:
        same time mask · same presence mask · same credits · same year penalty
        · same REQUIREMENT MEMBERSHIP (both Language, or both plain electives, ...)
        · same LEDGER ITEM (FREE / ME / ECO1101)
        · same DIFFICULTY TIER (easy vs hard language)
    """
    import rank2 as R2, rank3 as R3, rank4 as R4, difficulty as DIFF
    R2.LANG = set(DIFF.LANG_ALL)                 # the widened pool (R166/R187)
    with contextlib.redirect_stdout(io.StringIO()):
        P, sig, sigs, SIGCODES, code = R3.build()
    # which requirement pool does each section belong to? '' = plain elective
    pool_of = {}
    for pname, v in P.items():
        for s in v:
            pool_of.setdefault(s['c'], pname)
    g = collections.defaultdict(list)
    seen = set()
    for s in P['OPEN']:
        if s['c'] in seen:        # P['OPEN'] carries duplicate rows for 4 sections
            continue
        seen.add(s['c'])
        req = 'LANG' if code(s) in R2.LANG else pool_of.get(s['c'], '')
        key = (s['tm'], s['pm'], s['cr'],
               round(R2.YEAR_PEN(R2.eff_year(s, code)), 4),
               req, R4.item_of_section(s, code),
               # ⭐ and the DIFFICULTY TIER. The first fix still offered YCF1601 LATIN as an
               # equal swap for BEGINNING JAPANESE: both satisfy Language, both fit the slot
               # — but Latin is 언어와표현, the HARD tier, worth -D_LANG (10). Same error one
               # level down, found by applying Iden's own test to the corrected output.
               DIFF.steps(code(s)))
        g[key].append(s)
    out = {}
    for k, v in g.items():
        if len(v) > 1:
            for s in v:
                out[s['c']] = [(x['c'], x['n']) for x in v if x['c'] != s['c']]
    return out

def same_course_sections():
    """R163: sections of the SAME course at the SAME time, differing only by professor.
    Distinct from twins() — those are *different courses* the model scores equally.
    These are the same course, so they are a professor choice AND a registration-day
    fallback: if one 분반 is full, another may not be. 56 such groups exist."""
    d = json.load(open(P('canonical_2026F.json'), encoding='utf-8'))
    def mask(bl):
        m = 0
        for a, b in bl: m |= 1 << (a*16 + b)
        return m
    g = collections.defaultdict(list)
    for s in d:
        g[(s['c'].split('-')[0], mask(s['time']), mask(s['pres']))].append(s)
    out = {}
    for v in g.values():
        if len(v) > 1:
            for s in v:
                out[s['c']] = [(x['c'], x.get('p') or '?') for x in v if x['c'] != s['c']]
    return out

def build(n=50):
    d = {s['c']: s for s in json.load(open(P('canonical_2026F.json'), encoding='utf-8'))}
    rows = list(csv.DictReader(open(P('FINAL_ranked4.csv'), encoding='utf-8-sig')))
    seen, out = set(), []
    for x in rows:
        codes = [c for c in (x['requirements']+' '+x['electives']+' '+x['chapel']).split() if c and c != '-']
        # ⭐ R222 (Iden 2026-08-10): "Just give me the best 50 schedules structurally, and
        # I'll personally choose based on which courses sound interesting."
        # The key was (deferral, SECTION codes). Two rows holding the SAME courses at the
        # SAME hours, differing only in 분반 number, were two separate entries — so the
        # shortlist showed 50 rows containing 9 distinct course sets, and 28 of the 50 were
        # relabellings of an earlier row. If he picks on course identity, the shortlist has
        # to vary course identity.
        # Structural key = (deferral, BASE course codes, occupied time cells). A row survives
        # if it differs in WHAT he takes or in WHEN the week sits — not merely in 분반.
        # Same-time 분반 alternatives are not lost: they are already listed on each card by
        # `same_course_sections()` as the professor choice / fill-up fallback.
        # ⚠️ VIEW ONLY. FINAL_ranked4.csv, the ranking and every score are untouched.
        cells = tuple(sorted({(a, b) for c in codes
                              for a, b in (d.get(c) or {}).get('time', [])}))
        key = (x['deferred'], tuple(sorted({c.split('-')[0] for c in codes})), cells)
        if key in seen: continue
        seen.add(key)
        cs = []
        for c in codes:
            s = d.get(c)
            if not s: continue
            b = c.split('-')[0]
            cs.append(dict(code=c, base=b, name=s['n'], t=s.get('t',''), cr=s.get('cr',0),
                           prof=s.get('p') or '',
                           kind=KIND['MR' if b in MR else ('ME' if b in ME else REQ.get(b,'ELEC'))],
                           time=s['time'], pres=s['pres']))
        # ⭐ TWO DIFFERENT GOODS, AND THE OLD LABEL CONFLATED THEM (R194).
        # `free_days` in the CSV is the PRESENCE mask — no trip to campus. A day can be
        # "free" there while holding three online courses. REST needs the TIME mask.
        busy_t = set()
        for c in cs:
            for a, b in c['time']:
                if a < 5: busy_t.add(a)
        empty = ''.join(DAYS[i] for i in range(5) if i not in busy_t)
        out.append(dict(rank=len(out)+1, score=round(float(x['score']),2), defer=x['deferred'],
                        items=x.get('elective_items',''),
                        empty=empty,
                        free=x['free_days'], cr=x['credits'], e1=int(x['early1']),
                        lf=int(x['lunch_fail']), late=int(x['late']), holes=x['holes'], courses=cs))
        if len(out) == n: break
    return out

def grid(tt):
    busy = {}
    for ci, c in enumerate(tt['courses']):
        pres = {(a,b) for a,b in c['pres']}
        for a,b in c['time']:
            if a < 5: busy[(a,b)] = (ci, (a,b) in pres)
    lo = min((p for _,p in busy), default=1); hi = max((p for _,p in busy), default=9)
    free = set(tt['free'])
    h = ['<table class="g"><tr><th></th>' + ''.join(
        f'<th class="{"fr" if DAYS[i] in free else ""}">{DAYS[i]}</th>' for i in range(5)) + '</tr>']
    for p in range(lo, hi+1):
        h.append(f'<tr><td class="hh">{PT[p]}</td>')
        for dd in range(5):
            cell = busy.get((dd,p))
            if not cell:
                h.append(f'<td class="{"fr" if DAYS[dd] in free else ""}"></td>'); continue
            ci, on = cell; c = tt['courses'][ci]; col = KC[c['kind']]
            cls = 'on' if on else 'onl'
            style = f'background:{col}' if on else f'background:{col}33'
            tip = c['code'] + ' \u00b7 ' + c['name'] + ((' \u00b7 ' + c['prof']) if c['prof'] else '')
            h.append(f'<td class="{cls}" style="{style}" title="{html.escape(tip)}">{c["base"]}</td>')
        h.append('</tr>')
    return ''.join(h) + '</table>'

def deferral_risk():
    """R171: what a deferral costs in MILEAGE — the currency that actually binds from 2학년.
    NOT a score term (mileage is a budget constraint, not a preference), so it is shown
    alongside the score rather than folded into it."""
    import json as _j
    # ⚠️ NO silent fallback. A bare `except: return {}` hid a real failure here once and the
    # output simply lost a column with no warning — the exact pattern that has cost this
    # project repeatedly. If risk.json is missing, say so loudly.
    if not os.path.exists(P('risk.json')):
        raise FileNotFoundError("risk.json missing — run `python build_risk.py` first")
    R = _j.load(open(P('risk.json'), encoding='utf-8'))
    POOL = {'MR': ['QRM1001'], 'Lang': ['UIC1805', 'UIC1806'], 'WCiv': ['UIC1561'],
            'SciRD': ['UIC2151'], 'LHP': ['UIC1551', 'UIC1501', 'UIC1401', 'UIC1351', 'UIC1251']}
    out = {}
    for k, codes in POOL.items():
        vs = [R[c] for c in codes if c in R]
        if vs:
            best = min(vs, key=lambda v: v['cost_lo'])      # he would pick the cheapest option
            out[k] = (best['cost_lo'], best['cost_hi'])
    return out

def main():
    tts = build()
    global TW, SC, DR
    TW = twins()
    SC = same_course_sections()
    DR = deferral_risk()
    cards = []
    for t in tts:
        kinds = sorted({c['kind'] for c in t['courses']})
        legend = ' '.join(f'<i><b style="background:{KC[k]}"></b>{KN[k]}</i>' for k in kinds)
        parts = []
        for c in t['courses']:
            altH = ''
            same = SC.get(c['code'], [])
            if same:
                items = ' · '.join(f'<u>{a.split("-")[1]}</u> {html.escape(pr)}' for a, pr in same)
                altH += (f'<span class="alt sm"><b>{len(same)} other 분반, same time</b>'
                         f' — professor choice, and a fallback if this one fills: {items}</span>')
            alt = TW.get(c['code'], [])
            if alt:
                items = ' · '.join(f'<u>{a.split("-")[0]}</u> {html.escape(n[:26])}' for a, n in alt)
                altH += (f'<span class="alt"><b>{len(alt)} equal swap'
                         f'{"s" if len(alt)>1 else ""}</b> — different course, same score: {items}</span>')
            prof = f'<span class="pf">{html.escape(c["prof"])}</span>' if c['prof'] else ''
            parts.append(f'<li><b style="background:{KC[c["kind"]]}"></b>'
                         f'<span><strong>{html.escape(c["code"])}</strong> {html.escape(c["name"][:40])}'
                         f'{prof}{altH}</span>'
                         f'<em>{c["t"]}</em></li>')
        clist = ''.join(parts)
        online = sum(1 for c in t['courses'] for a,b in c['time']
                     if a < 5 and (a,b) not in {(x,y) for x,y in c['pres']})
        flags = []
        if t['e1']: flags.append(f'{t["e1"]}× 9am start')
        if t['lf']: flags.append(f'{t["lf"]}× no lunch')
        if t['late']: flags.append(f'{t["late"]}× late finish')
        if t['holes']: flags.append(f'gaps {t["holes"]}')
        if online: flags.append(f'{online} online hour{"s" if online>1 else ""}')
        defer = {'MR':'QRM입문','Lang':'Chinese/Japanese'}.get(t['defer'], t['defer'])
        dr = DR.get(t['defer'])
        drH = ''
        if dr:
            pct = (100*dr[0]/72, 100*dr[1]/72)
            cls = 'bad' if pct[0] >= 20 else 'ok'
            drH = (f'<span class="dr {cls}">costs <b>{dr[0]:.0f}–{dr[1]:.0f}</b> mileage later '
                   f'= {pct[0]:.0f}–{pct[1]:.0f}% of a future budget</span>')
        cards.append(f'''<article class="c" data-rank="{t['rank']}" data-defer="{t['defer']}">
<header><span class="rk">#{t['rank']}</span><span class="sc">{t['score']:.2f}</span>
<span class="tg">postpones <b>{defer}</b></span>{drH}
<span class="tg">home <b>{t['free']}</b></span>
<span class="tg">no class at all <b>{t['empty'] or '—'}</b></span>
<span class="tg">{t['cr']} cr</span></header>
<div class="body"><div class="gw">{grid(t)}<div class="lg">{legend}<i><b class="hatch"></b>online — no campus</i></div>
<p class="fl">{' · '.join(flags) or 'no penalties'}</p></div>
<ul class="cl">{clist}</ul></div></article>''')

    shapes = collections.Counter(t['free'] for t in tts)
    defers = collections.Counter(t['defer'] for t in tts)
    doc = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Fall 2026 · top 50 timetables</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{--bg:#fff;--fg:#1a1a1a;--mut:#6b6b6b;--fai:#9a9a9a;--ln:#e4e4e0;--sub:#f0f0ec;--card:#fff}}
@media(prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#eeeeec;--mut:#a0a09a;--fai:#77776f;--ln:#33332f;--sub:#1f1f1d;--card:#1b1b1a}}}}
*{{box-sizing:border-box}}
body{{margin:0;padding:26px 22px 60px;background:var(--bg);color:var(--fg);
font:14px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
h1{{font-size:19px;margin:0 0 3px;font-weight:600}}
.sub{{color:var(--mut);font-size:12.5px;margin:0 0 16px}}
.bar{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;position:sticky;top:0;z-index:5;
background:var(--bg);padding:9px 0 11px;border-bottom:1px solid var(--ln);margin-bottom:16px}}
.bar button{{font:inherit;font-size:12.5px;padding:4px 11px;border:1px solid var(--ln);
background:var(--sub);color:inherit;border-radius:99px;cursor:pointer}}
.bar button[aria-pressed=true]{{background:var(--fg);color:var(--bg);border-color:var(--fg)}}
.bar .n{{color:var(--mut);font-size:12.5px;margin-left:auto}}
.c{{border:1px solid var(--ln);border-radius:10px;margin-bottom:12px;background:var(--card);overflow:hidden}}
.c header{{display:flex;gap:9px;align-items:center;flex-wrap:wrap;padding:9px 13px;border-bottom:1px solid var(--ln);background:var(--sub)}}
.rk{{font-weight:700;font-size:15px;font-variant-numeric:tabular-nums}}
.sc{{font-weight:600;font-variant-numeric:tabular-nums;font-size:15px}}
.tg{{font-size:11.5px;color:var(--mut);border:1px solid var(--ln);border-radius:99px;padding:1px 9px;background:var(--bg)}}
.tg b{{color:var(--fg)}}
.dr{{font-size:11px;border-radius:99px;padding:1px 9px;border:1px solid var(--ln)}}
.dr.ok{{color:var(--mut)}}
.dr.bad{{color:#b8562f;border-color:#b8562f66;font-weight:600}}

.body{{display:flex;gap:18px;padding:13px;flex-wrap:wrap;align-items:flex-start}}
.gw{{flex:1 1 330px;min-width:300px}}
.cl{{flex:1 1 300px;min-width:280px;list-style:none;margin:0;padding:0}}
.cl li{{display:flex;gap:7px;align-items:baseline;padding:3.5px 0;border-bottom:1px solid var(--ln);font-size:12px}}
.cl li:last-child{{border:0}}
.cl b{{width:9px;height:9px;border-radius:2px;flex:none;position:relative;top:1px}}
.cl span{{flex:1;min-width:0}}
.cl strong{{font-weight:650}}
.cl em{{font-style:normal;color:var(--fai);font-size:11px;white-space:nowrap;font-variant-numeric:tabular-nums}}
.alt{{display:block;margin-top:2px;font-size:10.5px;color:var(--mut);line-height:1.4}}
.alt b{{width:auto;height:auto;display:inline;background:none!important;font-weight:650;color:var(--fg)}}
.alt u{{text-decoration:none;font-weight:650;color:var(--fg)}}
.alt.sm{{border-left:2px solid var(--ln);padding-left:7px}}
.pf{{display:block;color:var(--fg);font-size:11px;opacity:.85}}
.cl strong{{font-weight:650;font-variant-numeric:tabular-nums}}
table.g{{border-collapse:collapse;width:100%;table-layout:fixed}}
table.g th{{font-size:11.5px;font-weight:500;color:var(--mut);padding:0 0 4px;text-align:center}}
table.g th.fr,table.g td.fr{{background:var(--sub)}}
table.g td{{height:24px;border:1px solid var(--ln);text-align:center;font-size:10px;padding:0;overflow:hidden}}
table.g td.hh{{border:0;color:var(--fai);font-size:10px;text-align:right;padding-right:7px;width:44px;font-variant-numeric:tabular-nums}}
td.on{{color:#fff;font-weight:600}}
td.onl{{font-weight:600;background-image:repeating-linear-gradient(45deg,transparent,transparent 3px,rgba(128,128,128,.3) 3px,rgba(128,128,128,.3) 6px)}}
.lg{{display:flex;gap:9px;flex-wrap:wrap;margin-top:8px;font-size:10.5px;color:var(--mut)}}
.lg i{{display:inline-flex;align-items:center;gap:4px;font-style:normal}}
.lg b{{width:9px;height:9px;border-radius:2px;display:inline-block}}
.lg b.hatch{{background:repeating-linear-gradient(45deg,transparent,transparent 2px,rgba(128,128,128,.55) 2px,rgba(128,128,128,.55) 4px);border:1px solid var(--ln)}}
.fl{{margin:7px 0 0;font-size:11.5px;color:var(--mut)}}
.note{{font-size:12.5px;color:var(--mut);border-left:2px solid var(--ln);padding-left:11px;margin:0 0 16px;line-height:1.55}}
</style>
<h1>Fall 2026 · top 50 timetables</h1>
<p class="sub">generated {len(tts)} distinct grids · scores {tts[0]['score']:.2f} → {tts[-1]['score']:.2f}
· free-day shapes {dict(shapes)} · postpones {dict(defers)}</p>
<p class="note"><b>Ranked purely by the score.</b> The mileage figure on each card is
<i>measured data shown in its own units</i> — what that timetable's deferral would cost in a
future semester's bidding budget. It is <b>not</b> folded into the score and does <b>not</b>
reorder anything; converting mileage to score points would need an exchange rate nobody has
set. Read it alongside the rank, not instead of it.<br><br>
<b>"home" = no trip to campus. "no class at all" = genuinely nothing scheduled.</b>
They are different, and #1 differs on them: Monday is home-but-working (three online
courses), Friday is genuinely empty. Only the second earns REST; the first earns the trip.
<br><b>Every one of these leaves Monday and Friday free of campus</b> — home Friday
through Monday, every week. Solid blocks are in person. Hatched blocks are online: they hold an
hour of your time but cost you no trip, which is why a day can still count as campus-free with
one on it. Hover a block for the full course name.</p>
<div class="bar">
<button data-f="all" aria-pressed="true">all 50</button>
<button data-f="MR">postpones QRM입문</button>
<button data-f="Lang">postpones language</button>
<span class="n" id="n"></span></div>
<div id="list">{''.join(cards)}</div>
<script>
var btns=[].slice.call(document.querySelectorAll('.bar button')),
    cards=[].slice.call(document.querySelectorAll('.c')),n=document.getElementById('n');
function apply(f){{var s=0;cards.forEach(function(c){{
  var ok=(f==='all'||c.dataset.defer===f);c.style.display=ok?'':'none';if(ok)s++;}});
  n.textContent=s+' shown';
  btns.forEach(function(b){{b.setAttribute('aria-pressed',b.dataset.f===f);}});}}
btns.forEach(function(b){{b.onclick=function(){{apply(b.dataset.f);}};}});
apply('all');
</script></html>'''
    open(P('TOP50.html'),'w',encoding='utf-8').write(doc)
    print(f"wrote TOP50.html — {len(tts)} timetables, {len(doc):,} bytes")

if __name__ == '__main__':
    main()
