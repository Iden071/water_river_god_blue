# -*- coding: utf-8 -*-
"""k_inventory.py — the CHEAP audit. No search. Structural facts about every future item.

For each ledger item and each course code that can satisfy it, record what the K measurement
would actually be standing on: which term/campus receives it, where the section geometry comes
from, how many times it has been observed, how much that geometry VARIES across observed
terms, and whether the surrounding filler pool matches the receiving term."""
import json, collections, itertools, os
import semester_sim as SS
import difficulty as DIFF
from plan_model import ITEMS

HERE = os.path.dirname(os.path.abspath(__file__))
mh = json.load(open(os.path.join(HERE, 'mileage_history.json'), encoding='utf-8'))
raw = json.load(open(os.path.join(HERE, 'raw_2026F.json'), encoding='utf-8'))
raw = raw if isinstance(raw, list) else list(raw.values())[0]
D = '월화수목금토일'


def show(m):
    out = []
    for d in range(7):
        ps = [p for p in range(1, 16) if (m >> (d * 16 + p)) & 1]
        if ps:
            out.append(D[d] + ','.join(map(str, ps)))
    return '/'.join(out)


def observations(code):
    """Every observed offering of `code`: (year, term, campus, mask)."""
    out = []
    for r in mh:
        if str(r.get('subjtnb')) != code:
            continue
        tm, _ = SS.parse_time(r.get('lctreTimeNm'))
        if tm:
            out.append((r.get('_syy'), 'S' if str(r.get('smtDivCd')) == '10' else 'F',
                        r.get('campsDivNm'), tm))
    return out


def current(code):
    out = []
    for r in raw:
        if str(r.get('subjtnb')) != code:
            continue
        tm, _ = SS.parse_time(r.get('lctreTimeNm'))
        if tm:
            out.append((r.get('campsDivNm'), tm))
    return out


def daysets(masks):
    return {frozenset(d for d in range(7) if (m >> (d * 16)) & 0xffff) for m in masks}


def profile(code, term, campus):
    obs = observations(code)
    cur = current(code)
    same = [o for o in obs if o[1] == term and o[2] == campus]
    anyterm = [o for o in obs if o[2] == campus]
    cur_c = [c for c in cur if c[0] == campus]
    masks_same = [o[3] for o in same]
    masks_any = [o[3] for o in anyterm]
    cnt = collections.Counter(masks_same or masks_any)
    n = sum(cnt.values())
    singletons = sum(1 for m, k in cnt.items() if k == 1)
    if masks_same:
        src = 'term-matched history'
    elif cur_c:
        src = 'CURRENT catalogue (cross-season stand-in)' if term == 'S' else 'CURRENT catalogue'
    elif masks_any:
        src = 'CROSS-SEASON history stand-in'
    else:
        src = 'NO DATA'
    return dict(code=code, term=term, campus=campus, src=src,
                n_obs_matched=len(same), n_obs_any=len(anyterm), n_current=len(cur_c),
                n_masks=len(cnt), n_daysets=len(daysets(cnt)) if cnt else 0,
                # Good–Turing: the mass this evidence assigns to a geometry never yet seen
                p_novel=(singletons / n) if n else 1.0,
                masks=[show(m) for m in cnt], freq=[cnt[m] for m in cnt])


# which items can be deferred out of Fall 2026, and where each would land
RECEIVING = {'MR': ('QRM1001', 'S', '국제'), 'WCiv': ('WCiv', 'S', '국제'),
             'LHP': ('LHP', 'F', '신촌'), 'SciRD': ('SciRD', 'F', '신촌'),
             'Lang·easy': ('Lang', 'S', '국제'), 'Lang·hard': ('Lang', 'F', '신촌')}
by_key = {i['key']: i for i in ITEMS}
CODES = {'MR': ['QRM1001'], 'WCiv': ['UIC1561'], 'LHP': ['UIC1551', 'UIC1251', 'UIC1501'],
         'SciRD': ['UIC2151'], 'Lang·easy': sorted(DIFF.LANG_EASY),
         'Lang·hard': sorted(DIFF.LANG_HARD)}

print("=" * 108)
print("A · THE DEFERRABLE REQUIREMENTS — what the K measurement stands on")
print("=" * 108)
print(f"{'requirement':11s} {'code':8s} {'recv':7s} {'evidence source':42s} "
      f"{'obs':>4} {'geo':>4} {'days':>5} {'p_novel':>8}")
inv = {}
for name, codes in CODES.items():
    _k, term, camp = RECEIVING[name]
    for c in codes:
        p = profile(c, term, camp)
        inv[f"{name}/{c}"] = p
        print(f"{name:11s} {c:8s} {camp}{'봄' if term=='S' else '가을':2s} {p['src']:42s} "
              f"{p['n_obs_matched'] or p['n_obs_any']:4d} {p['n_masks']:4d} {p['n_daysets']:5d} "
              f"{p['p_novel']:8.2f}")
        if p['n_masks'] > 1:
            for m, f in zip(p['masks'], p['freq']):
                print(f"{'':21s}   └ {m:22s} seen {f}x")

print()
print("=" * 108)
print("B · THE LEDGER ITEMS THAT MAKE UP THE FILLER — can their geometry be known at all?")
print("=" * 108)
print(f"{'item':9s} {'n':>3} {'campus':7s} {'terms':6s} {'codes':34s} {'observable geometry?'}")
for it in ITEMS:
    cs = it.get('codes') or []
    obs = sum(len(observations(c)) for c in cs)
    curn = sum(len(current(c)) for c in cs)
    verdict = ('ABSTRACT — no codes at all' if not cs else
               f'{obs} obs / {curn} current sections' if (obs or curn) else 'codes but NO sections anywhere')
    print(f"{it['key']:9s} {it['count']:3d} {it['campus']:7s} {it['terms']:6s} "
          f"{','.join(cs)[:34]:34s} {verdict}")

print()
print("=" * 108)
print("C · THE FILLER POOLS — is the surrounding semester term-matched?")
print("=" * 108)
for camp in ('국제', '신촌'):
    for cd, lab in (('10', 'Spring'), ('20', 'Fall')):
        rows = [r for r in mh if r.get('campsDivNm') == camp and str(r.get('smtDivCd')) == cd]
        ms = set()
        for r in rows:
            tm, _ = SS.parse_time(r.get('lctreTimeNm'))
            if tm and bin(tm).count('1') >= 3:
                ms.add(tm)
        print(f"  observed {camp} {lab:6s}: {len(ms):4d} distinct ≥3h masks")
    cur = {tm for c, tm in ((r.get('campsDivNm'), SS.parse_time(r.get('lctreTimeNm'))[0])
                            for r in raw) if c == camp and tm and bin(tm).count('1') >= 3}
    print(f"  Fall 2026 catalogue {camp}: {len(cur):4d} distinct ≥3h masks   <-- what K actually used, "
          f"for BOTH seasons")
json.dump(inv, open(os.path.join(HERE, 'k_inventory.json'), 'w', encoding='utf-8'),
          indent=1, ensure_ascii=False)
print("\nwrote k_inventory.json")
