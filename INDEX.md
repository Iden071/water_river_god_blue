# INDEX — read this first

**Fall 2026 수강신청 · 국제캠퍼스 · registration 2026-08-25, 09:00–17:00 KST**
Finalised **2026-08-17**. 300 rules. The pipeline below is the one that produced the answer;
every file it does not name is superseded.

---

## THE ANSWER

# ✅ FINAL — partition objective, 신촌 bonus 30

```
defer  Language                                    total 352.569

QRM1001-01  INTRODUCTION TO QUANTITATIVE RISK MGMT
UIC1561-01  WESTERN CIVILIZATION
UIC1551-04  WORLD HISTORY: GROUP II
UIC2151-12  RESEARCH DESIGN AND QUANTITATIVE METHODS
QRM2004-01  STATISTICAL ANALYTIC METHODS
STA2102-05  선형대수
YCA1006-01  채플(B)
```

**CLICK ORDER on 8/25 — most costly to lose, first** (`partition_clickorder.json`)

| # | section | cost |
|---|---|---:|
| 1 | `UIC1561-01-00` WESTERN CIVILIZATION | 21.10 |
| 2 | `STA2102-05-00` 선형대수 | 9.45 |
| 3 | `UIC2151-12-00` RDQM | 6.70 |
| 4 | `QRM1001-01-00` Intro to QRM | 5.33 |
| 5 | `QRM2004-01-00` Statistical Analytic Methods | 5.10 |
| 6 | `YCA1006-01-00` 채플(B) | 1.18 |
| 7 | `UIC1551-04-00` World History II | 0.00 — `UIC1551-01` substitutes free |

**THE REST OF THE DEGREE** (Σ 332.679, 5 신촌 / 1 국제 — the forced minimum)

| sem | | | value |
|---|---|---|---:|
| 3 | 신촌 S | Seminar | 49.671 |
| 4 | 신촌 F | Chapel + ECO1101 + ECO2101 | 35.569 |
| 5 | 국제 S | ME + ME + QRM3003 | **−7.050** |
| 6 | 신촌 F | Lang + ME + MR5 | 29.749 |
| 7 | 신촌 S | Seminar | 49.671 |
| 8 | 신촌 F | Chapel + ECO2102 + ME | 25.069 |

⚠️ sem 5 is negative because `QRM3003` forces one 국제 Spring and the plan pays for it once
rather than spreading it. A floor of 0 costs **7.9** and keeps all five 신촌 semesters — not
applied, recorded as available.

### LIVE FILES — everything else in this folder is superseded
```
TOP50_v3.html               the 50 browsable timetables, partition-scored
partition_clickorder.json   the 8/25 click order
partition_verdict.json      the six deferral branches
partition.json              the cost table (1,640 entries)
```
⛔ `DECISION_v3.html` and `fallback.json` are on the **old K objective** and disagree with the
above. Superseded by `partition_verdict.json` and `partition_clickorder.json` (R297).

## WHY THE EARLIER ANSWER ("defer Language") WAS WRONG

| rule | what was broken |
|---|---|
| **R264** | `pools_past.parse` dropped and fabricated hours on parenthesised time blocks — 25.4% of all sections, 66% of 신촌-Fall language sections. It manufactured four cheap geometries existing in no catalogue; `min()` selected one. `kdefer('Lang')` wrong by **+21.340**; the verdict inverted. Found by external red-team, reproduced independently. |
| **R260 · R269 · R276** | Three independent *truncate-then-maximise* bugs — `rows[:60]`, `TOPN = 3000`, `rows[:400]`. Rows are ranked by `score`; the objective is `score + Σunit_cost − K`. No score-ranked prefix is safe. |
| **R267** | `k_real.json['disp']` had **no producer** — read by three modules, written by none, unregenerable after the parser fix. Producer written; table rebuilt. |
| **R272** | `kdefer` had two code paths (MR pinned to a geometry, everything else bare `min()`). Replaced by one estimator for every branch. `min` vs `median` dissolved into a measured acquisition probability. |
| **R247 · R259** | `risk.p_get_freshman` tested `sy1 == 0` one-sidedly and declared the recommendation impossible the day the seat file landed. `p_win_bracket` returned `(1.0, 1.0)` — certainty — for unmeasured courses. |

## HOW THE OBJECTIVE GOT HERE — R285 and the partition

**The model used to price AVOIDANCE where only RELOCATION is possible.** Every ledger item must
be taken eventually, so a schedule penalty on a required course cannot be avoided, only moved.
`K` measured the damage of adding one course to a **free-choice filler semester** — a semester
that will never exist — and treated a penalty pushed into the future as removed.

Measured on 금, then the largest term in the ranking:
```
minimum 금-broken semesters over the remaining degree : 1   (QRM3003 runs 금 in 3 of 3)
clean semester      K(a 금 course)  +8.137
금 already broken   marginal        −2.321   <- a second 금 course is better than free
```

`K` is gone. The objective is now

    total = Fall week  +  best Σ best_week over semesters 3–8 of whatever units remain

with the 14 remaining units PARTITIONED across the six remaining semesters, campus chosen per
semester. Interaction is priced by construction — no independence assumption — which is what
R275 (superadditive, +14.675 when two deferrals collide) and R285 (subadditive, −2.321 when
they share a sacrificed day) both required.

⭐ It reproduces the 금 insight unprompted: `QRM3003` and `MR5` are placed in the SAME semester.
Nothing told it to cluster them.

| built | |
|---|---|
| `partition.py` | the cost table — 1,640 entries, 733 usable, 601 exact, **0 above-baseline violations** |
| `partition_solve.py` | the DP over partitions (1,728 states x 6 semesters x 2 campuses) |
| `partition_verdict.py` | the six deferral branches, every row scanned (R295) |
| `partition_clickorder.py` | leave-one-out click order on the same objective (R297) |

## STILL OPEN

| | |
|---|---|
| ⚠️ **prof ratings not applied** | `prof_ratings.csv` has ratings; `_v3_parts_*` were searched with `PROF_RATED=0`. Re-run all four `MAX_FREE`, then verdict + clickorder + render. |
| ⚠️ **re-pull `raw_2026F.json`** | it is from 08-06. Last diff was clean (0 time changes, 0 new 폐강 over 141 sections) but 폐강 cluster after registration closes. |
| ⚠️ **table asymmetry** | 국제 built at `PICKS=6`, 신촌 at `PICKS=2`; 132 BOUND entries, all 신촌 (R195's linear day value weakens the bound). Not a designed asymmetry — a speed compromise. |
| ⚠️ **2 UNMEASURED cells** | `Seminar` at 신촌F, `ECO2102` at 국제S — genuine season gaps, currently treated as unplaceable (R296). |
| ⛔ **`MAX_DEFER = 1`** | an operating choice, not a proven optimum. R121's proof is stale (R273: a pair beat it by 9.520 under the old objective). Never re-tested under the partition. |
| ⚠️ `test_v3.py` | 21 hold / 3 broken — R225 (December ledger), R237 (4 duplicate pool rows), R248 (label contamination). All documented. |

---

## READ IN THIS ORDER

| # | file | what it is |
|---|---|---|
| 1 | **`RULES.md`** | ⭐ the evidence archive, **300 rules**, append-only. **R285–R297 are the current model.** Search it; never read front-to-back. |
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
