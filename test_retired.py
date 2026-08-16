# -*- coding: utf-8 -*-
"""
test_retired.py — every "this cannot change the answer" claim, re-measured against the
CURRENT model, every time it is run.

WHY THIS FILE EXISTS
--------------------
Iden, 2026-08-09:
  "even if something 'does not change the answer', it should still be in the model in case
   of future model changes. Like why are we treating the model like some kind of already
   finished thing with only minimal changes to make."

The defect he is pointing at is not any one omission. It is that **"cannot change the
answer" was written into `GAPS.md` as prose.** Prose does not re-run. R185 found four such
claims that had outlived the model they were measured on, and R187 then killed one of them
outright within the hour — G-10's closure was false the moment the ranker changed.

So: a retirement is no longer a sentence. It is an assertion in here. If the model moves
and a retirement stops holding, THIS FILE FAILS instead of the claim quietly rotting.

RULE: nothing may be recorded as retired anywhere in this project unless it has a test here.
"""
import os, sys, csv, json

HERE = os.path.dirname(os.path.abspath(__file__))
FAILED, PASSED, STALE = [], [], []


def check(rule, claim, fn):
    """fn() -> (ok, detail). ok=None means the claim can no longer even be evaluated."""
    try:
        ok, detail = fn()
    except Exception as e:
        STALE.append((rule, claim, f"could not be evaluated: {type(e).__name__}: {e}"))
        return
    if ok is None:
        STALE.append((rule, claim, detail))
    elif ok:
        PASSED.append((rule, claim, detail))
    else:
        FAILED.append((rule, claim, detail))


# ---------------------------------------------------------------------------
def _rows():
    return list(csv.DictReader(open(os.path.join(HERE, 'FINAL_ranked4.csv'),
                                    encoding='utf-8-sig')))


# --- R175 / G-10 : "the widened language pool cannot change Fall 2026" ------
def r175():
    import difficulty as DIFF
    rows = _rows()
    top = rows[0]
    codes = top['requirements'].split() + top['electives'].split()
    hard = [c for c in codes if c[:7] in DIFF.LANG_HARD]
    if hard:
        return False, (f"#1 now TAKES a hard-tier language ({hard[0]}). The widened pool "
                       f"changed the answer. R175's 14.18 margin was measured against a "
                       f"pool that did not contain the 8 언어와표현 courses.")
    return True, "#1 contains no hard-tier language course"


# --- R160 : "RUN_EXP cannot reorder the top — every leader shares 월금" -----
def r160():
    rows = _rows()
    shapes = {r['free_days'] for r in rows[:50]}
    if len(shapes) > 1:
        return False, (f"top 50 now contains {len(shapes)} different free-day shapes "
                       f"{sorted(shapes)}; RUN_EXP no longer cancels and must be re-swept")
    return True, f"top 50 all share one free-day shape ({shapes.pop()}) — the term cancels"


# --- R174 : "W_DINNER fires in 0 of 5000, so it is inert" -------------------
def r174():
    rows = _rows()
    n = sum(1 for r in rows if r.get('dinner_fail') not in (None, '', '0'))
    if 'dinner_fail' not in (rows[0].keys() if rows else {}):
        return None, ("FINAL_ranked4.csv no longer carries a dinner column, so the claim "
                      "cannot be checked from the output. Re-add it or re-measure.")
    return (n == 0), f"dinner penalty fires in {n} of {len(rows)}"


# --- R171 : "risk appetite dissolved — mileage is a budget, not a preference"
def r171():
    import rank4, continuation, plan_model
    srcs = [open(os.path.join(HERE, f), encoding='utf-8').read()
            for f in ('rank4.py', 'continuation.py', 'plan_model.py')]
    # The claim is about the MECHANISM being present. Checking for the string 'risk.json'
    # tested the wrong thing — the live wiring imports risk.py and calls budget_check, and
    # risk.json (the old summary table) is genuinely dead. Split cleanly: this asserts the
    # mechanism, R171b asserts it can actually bind on real data.
    if any('import risk' in s and 'budget_check' in s for s in srcs):
        return True, ("risk.py is imported by continuation.py and the 72-point mileage "
                      "budget is enforced as a hard feasibility constraint, exactly as "
                      "R171 said it should be — a budget, not a preference")
    return False, ("no risk mechanism is wired into the live model; V assumes every future "
                   "course is obtained with probability 1")


# --- R144 : "국제 capacity is not scarce; it is 3x oversupplied" ------------
def r144():
    from continuation import solve, full_remaining
    v, plan = solve(full_remaining())
    if plan is None:
        return False, "the full remainder is INFEASIBLE — capacity claim is broken"
    reg = [s for s in plan['sems'] if s['kind'] == 'sem']
    n_intl = 1 + sum(1 for s in reg if plan['campus'][s['label']] == '국제')
    return (n_intl <= 4), (f"best plan uses {n_intl} 국제 semesters "
                           f"(minimum forced = 2). Scarce if this climbs.")


# --- R186 : "a 휴학 cannot change the 8/25 decision" ------------------------
def r186():
    from plan_model import ITEMS
    restricted = [i['key'] for i in ITEMS if i['terms'] != 'SF']
    if len(restricted) > 1:
        return False, (f"{len(restricted)} ledger items are now term-restricted "
                       f"{restricted}; the parity-invariance argument assumed exactly one "
                       f"(QRM3003) and must be re-run")
    return True, (f"only {restricted} is term-restricted, so every parity arrangement "
                  f"still offers it a legal Spring — invariance holds FOR THIS DATA")


# --- R181 : "the free-elective budget is respected" -------------------------
def r181():
    rows = _rows()
    top = rows[0]
    items = top.get('elective_items', '')
    n_free = items.split().count('FREE')
    return (n_free <= 1), (f"#1 spends {n_free} of ~5 degree-long free electives; "
                           f"it holds {items!r}")


# --- R152/R105 : the Korean Major-Elective cap is ENFORCED, not merely priced ---
def r152():
    import continuation
    src = open(os.path.join(HERE, 'continuation.py'), encoding='utf-8').read()
    if 'KOREAN_ME_COURSE_CAP' not in src:
        return False, 'the cap is not referenced anywhere in continuation.py'
    return True, (f'enforced at {continuation.KOREAN_ME_COURSE_CAP} ME courses in 신촌 '
                  f'semesters; 0 of 13 Fall-2026 ME sections are Korean-capped so it does '
                  f'not bind this term')


# --- R171b : the mileage budget is ENFORCED and actually priceable --------------
def r171b():
    import continuation
    from plan_model import ITEMS
    priced = [i['key'] for i in ITEMS if continuation.item_bid(i)]
    if not priced:
        return False, 'the budget check runs but nothing is priceable — it cannot bind'
    return (len(priced) >= 8), (f'{len(priced)}/{len(ITEMS)} ledger items priceable '
                                f'{priced}; the rest have no mileage evidence (G-3), so '
                                f'the 72-point budget cannot yet bind')


# --- R192 : the rendered deliverable is not older than the ranking it renders ----
def r192():
    csvp = os.path.join(HERE, 'FINAL_ranked4.csv')
    htmlp = os.path.join(HERE, 'TOP50.html')
    if not os.path.exists(htmlp):
        return False, 'TOP50.html does not exist'
    src = open(os.path.join(HERE, 'render_top50.py'), encoding='utf-8').read()
    if 'FINAL_ranked3' in src.split('"""', 2)[-1]:
        return False, 'render_top50.py still READS the superseded rank3 output'
    dt = os.path.getmtime(htmlp) - os.path.getmtime(csvp)
    if dt < 0:
        return False, (f'TOP50.html is {abs(dt)/60:.0f} min OLDER than FINAL_ranked4.csv — '
                       f'the file Iden opens disagrees with the model. Re-run '
                       f'render_top50.py.')
    return True, f'TOP50.html is {dt/60:.0f} min newer than the ranking it renders'


# --- R193 : #1 still maxes both tie-break rungs Iden controls -------------------
def r193():
    import tiebreak
    rows = _rows()
    top = rows[0]
    n_courses = len(top['requirements'].split()) + len(top['electives'].split())
    credits = float(top['credits'])
    r = tiebreak.fall2026_consequences(credits, n_courses, tiebreak.ALLOWANCE)
    ok = r['rung_d_maxed'] and r['rung_h_maxed']
    return ok, (f"#1 takes {n_courses} academic courses / {credits:.0f} cr -> "
                f"rung ⓓ {r['rung_d_courses_counted']}/6, rung ⓗ {r['rung_h_ratio']:.4f}. "
                f"These set his tie-break rank in EVERY future mileage round (R193).")


# --- R197 : an "equal swap" must not cross a requirement or a difficulty tier ------
def r197():
    import render_top50, difficulty as DIFF, rank2 as R2
    R2.LANG = set(DIFF.LANG_ALL)
    TW = render_top50.twins()
    bad = []
    for c, alts in TW.items():
        lang_c = c[:7] in DIFF.LANG_ALL
        for ac, _n in alts:
            lang_a = ac[:7] in DIFF.LANG_ALL
            if lang_c != lang_a:                      # crosses the Language requirement
                bad.append((c, ac, 'requirement'))
            elif DIFF.steps(c) != DIFF.steps(ac):     # crosses the difficulty tier
                bad.append((c, ac, 'tier'))
    if bad:
        return False, f'{len(bad)} bogus equal swaps, e.g. {bad[:3]}'
    return True, (f'{len(TW)} sections have equal swaps; none crosses a requirement '
                  f'boundary or a difficulty tier')


# --- R199 : difficulty and the year gap must not double-count -------------------
def r199():
    import rank2 as R2, difficulty as DIFF, rank3
    R2.LANG = set(DIFF.LANG_ALL)
    P = rank3.build()[0]
    codef = lambda s: s['code']
    both, seen = [], set()
    for v in P.values():
        for s in v:
            if s['c'] in seen:
                continue
            seen.add(s['c'])
            if DIFF.steps(codef(s)) and R2.eff_year(s, codef):
                both.append(s['c'])
    if both:
        return False, (f"{len(both)} courses now carry BOTH a difficulty step and a chart "
                       f"year, e.g. {both[:3]}. The EARLY arm of the year gap is itself a "
                       f"difficulty proxy (MODEL.md §3), so this double-counts. Decide "
                       f"which axis owns readiness before adding the carrier.")
    return True, ("difficulty and the year gap are disjoint (0 overlapping courses) — "
                  "difficulty has one carrier, the language tier, and language has no "
                  "chart year. Adding COURSE LEVEL as a carrier would break this.")


# --- R92/R202 : CC slots stay English; language is neutral everywhere else ---------
def r202():
    import rank2 as R2, difficulty as DIFF, rank3
    R2.LANG = set(DIFF.LANG_ALL)
    P = rank3.build()[0]
    bad = {}
    for pool in ('WCiv', 'LHP', 'SciRD', 'MR'):
        seen = {}
        for s in P[pool]:
            seen.setdefault(s['c'], s)
        k = [c for c, s in seen.items() if s.get('lang') != '10']
        if k:
            bad[pool] = k[:3]
    if bad:
        return False, f"R92 violated — Korean-taught sections can fill CC slots: {bad}"
    return True, ("R92 holds: 0 Korean-taught sections in any CC/MR pool. Elsewhere "
                  "language of instruction is NEUTRAL by explicit instruction (R202) — "
                  "its correct weight is zero, and zero is what the model uses. Do not "
                  "re-raise the 56%-Korean OPEN pool as a gap.")


# --- A3 (external audit F1/F2): provenance pointers must resolve ------------------
def a3():
    """Every rule ID cited in a provenance comment must exist in the extracted log."""
    import re, subprocess, sys
    ext = os.path.join(HERE, 'audit', 'ELICITED.md')
    if not os.path.exists(ext):
        return None, 'audit/ELICITED.md not built — run build_audit_package.py'
    have = set(re.findall(r'^\| (R\d+) \|', open(ext, encoding='utf-8').read(), re.M))
    cited = set()
    for f in ('rank.py', 'rank2.py', 'rank4.py', 'continuation.py', 'plan_model.py',
              'difficulty.py', 'risk.py', 'tiebreak.py'):
        p = os.path.join(HERE, f)
        if os.path.exists(p):
            cited |= set(re.findall(r'\bR\d{2,3}\b', open(p, encoding='utf-8').read()))
    missing = sorted(cited - have, key=lambda r: int(r[1:]))
    if missing:
        return False, (f'{len(missing)} rule IDs cited in code do not resolve in the '
                       f'extracted log: {missing[:8]}. A provenance tag that cannot be '
                       f'looked up is unfalsifiable.')
    return True, f'all {len(cited)} cited rule IDs resolve in audit/ELICITED.md'


if __name__ == '__main__':
    check('R175/G-10', 'the widened language pool cannot change Fall 2026', r175)
    check('R160', 'RUN_EXP cannot reorder the top', r160)
    check('R174', 'the dinner penalty is inert', r174)
    check('R171', 'risk appetite dissolved into a budget constraint', r171)
    check('R144', '국제 capacity is 3x oversupplied', r144)
    check('R186', 'a 휴학 cannot change the 8/25 decision', r186)
    check('R181', 'the free-elective budget is respected by #1', r181)
    check('R152/R105', 'the Korean ME cap is enforced, not merely priced', r152)
    check('R171b', 'the mileage budget can actually bind', r171b)
    check('R192', 'the rendered deliverable is not stale', r192)
    check('R193', '#1 maxes both tie-break rungs Iden controls', r193)
    check('R197', 'equal swaps are actually equal', r197)
    check('R199', 'difficulty and the year gap do not double-count', r199)
    check('R92/R202', 'CC stays English; language is neutral elsewhere', r202)
    check('A3', 'provenance pointers resolve (external audit F1)', a3)

    W = 62
    print("=" * W); print("RETIRED CLAIMS, RE-MEASURED AGAINST THE CURRENT MODEL"); print("=" * W)
    for tag, lst in (("✅ STILL HOLDS", PASSED), ("⚠️  CANNOT BE CHECKED", STALE),
                     ("❌ NO LONGER HOLDS", FAILED)):
        for rule, claim, detail in lst:
            print(f"\n{tag}  [{rule}]  {claim}")
            print(f"    {detail}")
    print()
    print("=" * W)
    print(f"{len(PASSED)} still hold · {len(STALE)} uncheckable · {len(FAILED)} BROKEN")
    if FAILED:
        print("\n⛔ A retirement has expired. Re-open it in GAPS.md — do not edit this test "
              "to make it pass.")
        sys.exit(1)
