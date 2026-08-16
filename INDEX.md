# INDEX — read this first

**Fall 2026 수강신청 · 국제캠퍼스 · registration 2026-08-25, 09:00–17:00 KST**
Finalised **2026-08-16**. 283 rules. The pipeline below is the one that produced the answer;
every file it does not name is superseded.

---

## THE ANSWER

# ✅ FINAL — 2026-08-16

```
defer  Intro to QRM (QRM1001)                     total 66.382

UIC1561-01  WESTERN CIVILIZATION            월7,8/수7
UIC1551-01  WORLD HISTORY: GROUP II         화7,목8,9
UIC2151-09  RESEARCH DESIGN (RDQM)          화5,6,목4
UIC1806-02  BEGINNING JAPANESE (1)
ECO1101-06  MATHEMATICS FOR ECONOMICS I     월9,10/수10
STA2102-05  선형대수                           월5,6/수6
YCA1006-01  채플(B)
```

**CLICK ORDER on 8/25 — most costly to lose, first**

| # | section | cost to lose |
|---|---|---:|
| 1 | `UIC1561-01-00` | 32.48 |
| 2 | `STA2102-05-00` | 6.64 |
| 3 | `ECO1101-06-00` | 2.51 |
| 4 | `YCA1006-01-00` | 1.18 |
| 5–7 | `UIC1551-01` · `UIC2151-09` · `UIC1806-02` | 0.00 |

`DECISION_v3.html` — **MR wins 3/3 catalogue-year cells.**
`TOP50_v3.html` — 88 cards from 107,209 structurally distinct candidates.

> ✅ **Registrable.** The 8/16 seat pull confirms `UIC1561-01-00` has no per-year quota scheme,
> so a 1학년 is not barred (R2/R134/R247). Two sections elsewhere DO bar 1학년
> (`YCG1804-01-00`, `YCG1853-01-00`); `eligibility.py` filters them.
> ⚠️ The pull answered **eligibility**, not seat competition — `atnlcPercpCnt` is not capacity
> and 여석 must never be computed from it (R248).

---

## WHY THE EARLIER ANSWER ("defer Language") WAS WRONG

| rule | what was broken |
|---|---|
| **R264** | `pools_past.parse` dropped and fabricated hours on parenthesised time blocks — 25.4% of all sections, 66% of 신촌-Fall language sections. It manufactured four cheap geometries existing in no catalogue; `min()` selected one. `kdefer('Lang')` wrong by **+21.340**; the verdict inverted. Found by external red-team, reproduced independently. |
| **R260 · R269 · R276** | Three independent *truncate-then-maximise* bugs — `rows[:60]`, `TOPN = 3000`, `rows[:400]`. Rows are ranked by `score`; the objective is `score + Σunit_cost − K`. No score-ranked prefix is safe. |
| **R267** | `k_real.json['disp']` had **no producer** — read by three modules, written by none, unregenerable after the parser fix. Producer written; table rebuilt. |
| **R272** | `kdefer` had two code paths (MR pinned to a geometry, everything else bare `min()`). Replaced by one estimator for every branch. `min` vs `median` dissolved into a measured acquisition probability. |
| **R247 · R259** | `risk.p_get_freshman` tested `sy1 == 0` one-sidedly and declared the recommendation impossible the day the seat file landed. `p_win_bracket` returned `(1.0, 1.0)` — certainty — for unmeasured courses. |

## ⛔⛔⛔ THE LARGEST OPEN DEFECT — R285, THE RELOCATION GAP

**The model prices AVOIDANCE where only RELOCATION is possible.** Every ledger item must be
taken eventually, so a schedule penalty on a required course cannot be avoided — only moved.
The objective scores this semester's discomfort and treats a penalty pushed into the future as
*removed*. `K` exists to catch this and does not, because it measures damage against a
**free-choice filler semester** rather than the actual remaining obligation set.

Measured on 금, the largest term in the ranking (32–43 points per hour):

```
minimum 금-broken semesters over the remaining degree : 1
QRM3003 runs 금 in 3 of 3 observed sections — it can NEVER avoid 금

clean semester      K(a 금 course)  +8.137
금 already broken   marginal        −2.321   ← a second 금 course is better than free
```

So 금-freedom is priced as permanently achievable and it is not. The correct plan is **one
금-broken semester absorbing every 금-ish obligation**, which the model cannot express because
`K` is per-course and per-semester-in-isolation. Same root cause as R275 (deferrals assumed
independent), opposite sign.

### ⭐ MEASURED (R286) — the verdict survives, the margin does not

`relocation.py` rebuilds K's filler pool from the **actual remaining ledger** (14 units over 6
semesters = 2.33 obligations per semester) instead of free-choice sections:

| | K shipped | K realistic |
|---|---:|---:|
| MR | 1.917 | 2.000 |
| Lang | 16.620 | **0.000** |
| WCiv | 24.643 | **2.400** |
| SciRD | 21.372 | **4.375** |
| LHP | 15.698 | **0.000** |

**K spread across branches: 24.643 → 4.375.**

```
SHIPPED    : defer MR 66.382   (2nd Lang 47.18, margin 19.203)
RELOCATION : defer MR 66.299   (2nd Lang 63.80, margin  2.500)
```

⇒ **Same answer, margin 19.203 → 2.500.** Almost everything that made the choice look decisive
was K, and K was measured against a semester that will never exist. What survives is a thin
2.5-point preference coming from `pre_K` — this semester's week quality and elective credit —
which is the part of the model with real elicitation behind it.

Still outstanding: the **partition** (optimise all 14 remaining units across 6 semesters), and
deferral independence (R275). The 2-obligation pin is an average, not a plan.

## THE OTHER OPEN STRUCTURAL QUESTION

`MAX_DEFER = 1` is an **operating choice, not a proven optimum**. R121's proof is stale (R273):
a two-deferral branch beats the current answer by **9.520**. But `ΣK` assumes deferred courses
do not interact, and co-locating two in one semester costs **+14.675** (R275) — enough to erase
the gain, if they co-locate. The model cannot yet tell.

⇒ **Unresolved, not eliminated (R277).** Closing it needs joint K plus a placement check
against `plan_model.ITEMS`.

---

## READ IN THIS ORDER

| # | file | what it is |
|---|---|---|
| 1 | **`RULES.md`** | ⭐ the evidence archive, **283 rules**, append-only. **R264–R277 are the current model.** Search it; never read front-to-back. |
| 2 | **`PURPOSE_CHECK_2026-08-10.md`** | what the code actually rewards, term by term, reconstructed from source rather than from documentation. Start here to understand the objective. |
| 3 | **`DESIGN_V3.md`** | why V was deleted as a score and what replaced it. |
| 4 | **`MISSING_2026-08-16.md`** | ⭐ what is still missing, ordered by whether we could *detect* it being wrong. Supersedes `MISSING_2026-08-10.md` and `GAPS.md`. |
| 5 | **`SHAPED_HOLES_2026-08-16.md`** | ⭐ every neutral-default path, classified and **forced to run**. Contains R250: the branch cache was keyed on `MAX_FREE` alone, so every constant sweep was silently a no-op. |
| 6 | **`RED_TEAM_2026-08-16.md`** | hand this to an outside reviewer. The eight error *classes* already found, the load-bearing claims ranked by damage, and what not to re-litigate. Written to be falsified. |
| 7 | `GAPS.md` · `VERIFY.md` | the pre-v3 gap list. ⚠️ both predate 08-10; R225–R244 supersede them where they disagree. |

### ⛔ SUPERSEDED — do not act on these
`HANDOFF*.md` · `STOCKTAKE_2026-08-09.md` · `MODEL.md` · `CONTINUATION_BUILD.md` ·
`DECISIONS_NEEDED.md` · `FINAL_ranked4.csv` · `TOP50.html` · `ALTERNATIVES.html`

All of them describe the **pre-v3** objective, in which the deferral verdict was decided by a
crowding proxy since shown to have the wrong curvature (R228). `STOCKTAKE` and
`HANDOFF_2026-08-10` also disagree with each other numerically. Kept only for the quotes.

---

## THE LIVE PIPELINE — run in this order

```bash
export D_LANG=10.0 K_T=0.5

# 1. data (needs jsessionid.txt; run on Iden's machine — sandbox gets proxy 403)
python fetch_past_terms.py     # past catalogues            -> past_terms.json
python fetch_fall2026.py       # 학년별정원 seat pull         -> fall2026_seats.json
python fetch_mileage.py        # mileage history            -> mileage_history.json

# 2. the K table   ⚠️ NODE_CAP=1200000 — 30M and 4M both OOM on 신촌 (R268)
NODE_CAP=1200000 python k_real.py       # K + disp          -> k_real.json

# 3. the search    ⚠️ ALL of 0/1/2 must share constants or the renderer refuses (R263)
for mf in 0 1 2 99; do MAX_FREE=$mf python research_v3.py; done   -> _v3_parts_f*/

# 4. the answer
python fallback.py             # recommendation + click order -> fallback.json
python render_v3_top50.py      # browsable top 50             -> TOP50_v3.html
python render_v3.py            # one-page decision view       -> DECISION_v3.html

# 5. verification — 21 hold / 3 broken is the expected state
python test_v3.py
python sweep_holes.py          # D_LANG x GPA_GATE_MULT, re-searched
```

⚠️ **After editing `prof_ratings.csv`, re-run step 3 for ALL of `MAX_FREE` 0/1/2**, not one.
`TOPN`, `D_LANG`, `GPA_GATE_MULT`, `PROF_W`, `PROF_UNRATED` are stamped into every part file
and a mismatch aborts the render (R250/R263/R269).

### Runtime overrides applied after `rank3.build()` — never edit rank2 above its exec marker
| module | what it fixes |
|---|---|
| `fm_fix.py` | the fixed-hour mask per SEGMENT, not per course mode (R239) |
| `eligibility.py` | drops 폐강 + sections Iden is barred from; flags the rest (R240/R243) |
| `ledger_nodm.py` | the single-major ledger, for testing the double-major assumption (R241) |

`pools_past.py` builds the per-(campus, season, year) section pools everything else measures
against. `verify_purpose_check.py` reproduces the old #1 from transcribed constants alone.

### What is NO LONGER used
`continuation.py` · `crowding.json` · `rank4.py` · `rank4_branch.py` · `semester_sim.py`'s
search. The v3 path imports none of them. **`crowding.json` is convex where all six measured
curves are concave (R228) — `test_v3.py` asserts the discrepancy so it cannot be used silently.**

---

## TRAPS THAT ARE STILL LIVE

1. **`rank2.py` cannot be reordered or reformatted above `    heap = []; cnt=[0]`** —
   `rank3.build()` execs its source text up to that literal. Most fragile thing here.
2. **Its docstring says "Iden lives at 국제 (dorm)". That is wrong** — he lives at home; 국제 is
   an auto-assigned dorm. The line sits above the exec marker and cannot be edited. See R129.
3. **`rank.py` looks legacy but holds every weight constant.** Deleting it deletes the model.
4. **`scipy` is required** (`continuation.py`), and is not in any requirements file.
5. The mount permits truncation but not deletion: `rm` fails, `: > file` works.

---

## OPEN, IN ORDER OF WHETHER IT CAN CHANGE 8/25

| | |
|---|---|
| ✅ ~~seat pull~~ | **DONE 2026-08-16** (R247). `UIC1561-01-00` is open to a 1학년; 2 sections barred, now filtered; re-search unchanged at 64.633. `fall2026_seats.json`, 179 sections. |
| ⚠️ seat *competition* | **still unmeasured** (R248). `fallback.py` gives the cost half of `cost × probability`; nothing gives the probability half. `atnlcPercpCnt` looked like capacity and is not. |
| ⚠️ `fall2026_seats.json` is now load-bearing | `eligibility.py` filters on it. If the file goes missing the filter silently stops and **nothing asserts it**. |
| ⚠️ 17 of 38 ledger units | `DM` ×12 and `FREE` ×5 have no course identity, so their hours are assumed (R225). `test_v3.py` holds this open. |
| ⚠️ workload | unpriced (R218). The two `fm = 0` sections are excluded as a guard, not fixed. |
| ⚠️ n = 4 | 신촌 at a full 6-course load is computationally out of reach; 국제 reaches n=5. |
| ⚠️ Lang's K | assumes a 신촌 **Fall** receiving semester. In Spring the easy tier exists there (R232). |
| December | the second major sets `DM`'s 12 units and can then be modelled properly. |
