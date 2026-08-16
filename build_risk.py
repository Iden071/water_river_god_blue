"""
build_risk.py — DESIGN_v2 §2. Acquisition risk, regime 2 (anything DEFERRED).

⚠️ THE KEY DESIGN DECISION, and it is not obvious:
   mileage is NOT a cost — it is a BUDGET CONSTRAINT.

   Iden gets 76 마일리지 as a 1학년 and 72 from 2학년 (제도안내, 대학별 마일리지 table),
   max 36 on any one course and never 36 on two. Spending 30 on a contested course is not
   something he "feels"; it is 42% of the budget he cannot then spend elsewhere.

   So risk enters as FEASIBILITY, not as a score penalty:
       a future semester is affordable  <=>  sum of required bids <= 72
   That means it needs NO preference from Iden — nothing to elicit, nothing to weight.
   A plan whose backlog cannot be bought is simply excluded.

⚠️ REGIME. This applies ONLY to courses deferred to 2학년+, where Iden is a mileage bidder.
   Fall 2026 is 대기순번제 — no bidding at all — so none of this touches this semester's
   clicks (R130 vs R165). Getting that backwards has already cost this project twice.

⚠️ WHAT THE DATA CAN AND CANNOT SAY (R116):
   `avgMlg` is the average bid of everyone who APPLIED, not the winning cutoff. `minMlg` is
   the lowest bid among all applicants, also not the cutoff. So the true price is UNKNOWN
   and can only be bracketed. Every number below is a bracket, never a point.
"""
import json, os, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__)); P = lambda f: os.path.join(HERE, f)
BUDGET_1, BUDGET_2 = 76, 72          # 제도안내: UIC 1학년 / 2~4학년
MAX_PER_COURSE = 36

def brackets():
    m = json.load(open(P('mileage_history.json'), encoding='utf-8'))
    by = collections.defaultdict(list)
    for r in m: by[r['subjtnb']].append(r)
    out = {}
    for c, v in by.items():
        obs = []
        for r in v:
            cap, app = r.get('atnlcPercpCnt') or 0, r.get('cnt') or 0
            ratio = app / max(cap, 1)
            avg, mx = r.get('avgMlg'), r.get('maxMlg')
            if ratio <= 1.0:
                lo, hi = 1, (avg if avg is not None else 1)      # everyone fits: bid minimally
            else:
                lo = avg if avg is not None else 1               # must beat the field
                hi = min(MAX_PER_COURSE, mx if mx is not None else MAX_PER_COURSE)
            obs.append((ratio, lo, hi))
        ratios = [o[0] for o in obs]
        out[c] = dict(
            n_terms=len(obs),
            n_oversubscribed=sum(1 for r in ratios if r > 1),
            ratio_max=max(ratios),
            # R6: "prefer the MAX across recent semesters" — plan for the bad term, not the mean
            cost_lo=round(max(o[1] for o in obs), 1),
            cost_hi=round(max(o[2] for o in obs), 1),
            ever_safe=all(r <= 1 for r in ratios))
    return out

def main():
    B = brackets()
    json.dump(B, open(P('risk.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"wrote risk.json — {len(B)} courses with mileage evidence\n")
    print("MILEAGE COST TO SECURE, planning for the worst recorded term (R6)")
    print(f"budget from 2학년: {BUDGET_2}, across ~6 courses. Max {MAX_PER_COURSE} on any one.\n")
    print(f"{'course':9s} {'terms':>5s} {'over':>5s} {'worst 배율':>10s}   {'cost bracket':>14s}  {'% of budget':>12s}")
    for c, v in sorted(B.items(), key=lambda kv: -kv[1]['cost_lo']):
        pct = f"{100*v['cost_lo']/BUDGET_2:.0f}–{100*v['cost_hi']/BUDGET_2:.0f}%"
        flag = '' if not v['ever_safe'] else '   (never oversubscribed)'
        print(f"{c:9s} {v['n_terms']:5d} {v['n_oversubscribed']:5d} {v['ratio_max']:9.2f}x   "
              f"{v['cost_lo']:5.1f} – {v['cost_hi']:5.1f}  {pct:>12s}{flag}")

    print("\n" + "=" * 78)
    print("THE DEFERRAL QUESTION, in the units that actually bind")
    for c, label in (('QRM1001', 'Intro to QRM'), ('UIC1805', 'Chinese'), ('UIC1806', 'Japanese')):
        v = B.get(c)
        if not v: continue
        print(f"  defer {label:14s} -> costs {v['cost_lo']:5.1f}–{v['cost_hi']:5.1f} mileage "
              f"= {100*v['cost_lo']/BUDGET_2:2.0f}–{100*v['cost_hi']/BUDGET_2:2.0f}% of a future semester's budget")
    print("=" * 78)

    print("\n⚠️ COVERAGE — this is the honest limit")
    need = ['QRM3003','QRM3004','QRM3005','ECO2101','ECO2102','STA2102','QRM2004','QRM2102',
            'YCF1301','YCF1351','YCF1451','YCF1501','YCF1551','YCF1601','YCF1603','YCF1607']
    missing = [c for c in need if c not in B]
    print(f"   {len(B)} courses have evidence; {len(missing)} required/candidate courses have NONE:")
    print("   " + ', '.join(missing))
    print("   Every one is either 신촌, Spring-only, or a widened-language-pool course.")
    print("   ⇒ the budget check CANNOT yet be run on a full future semester. It can only")
    print("     compare the two deferral options, which is what the live decision needs.")

if __name__ == '__main__':
    main()
