# RED-TEAM REPLY #2 — 2026-08-17, on the changed files only

Scope: everything modified or created since 2026-08-16 07:22 (my previous snapshot). That is
the R264 parser fixes, the `k_real` regeneration and its new `disp` producer, and the entire
new partition path (`partition.py`, `partition_solve.py`, `partition_verdict.py`,
`partition_clickorder.py`, `build_sinchon.py`, `relocation.py`, `_sweep_sin.py`, `_floor.py`).
Snapshot taken 05:30 UTC; `partition.json` last written 05:29 and unchanged at 05:35, with no
python process running — so this is a settled state, not a race.

Harness: `_a_cache.py`, `_a_islice.py`, `_a_chapel.py`, `_a_sinS.py`, `_a_sem.py`.

---

## F1 ⭐⭐ `partition.json`'s 신촌 half has been destroyed. The shipped answer cannot be recomputed from any file in the repo.

**CLAIM**
`INDEX.md`'s answer (352.569), `partition_verdict.json`, `partition_clickorder.json` and
`TOP50_v3.html` are all derived from `partition.json` by `partition_solve.solve()`.

**TEST**

1. Counted `partition.json` entries and non-null values per (campus, season).
2. Rebuilt the shipped winning Fall row out of `_v3_parts_f2/part_Lang.json`
   (`QRM1001-01 · UIC1561-01 · UIC1551-04 · UIC2151-12 · QRM2004-01 · STA2102-05 · YCA1006-01`,
   Fall week 19.890, `items = ['ME','ME']`), took `partition_verdict.remainder('Lang', row)`,
   and called `partition_solve.solve()` on it at `SINCHON_BONUS` 0.0 and 30.0.
3. Retrieved the committed copy: `git show HEAD:partition.json`.

**RESULT**

```
current partition.json
  국제 S   410 entries   194 valued
  국제 F   410 entries   142 valued
  신촌 S     3 entries     3 valued
  신촌 F     0 entries     0 valued

solve({'Chapel':2,'Lang':1,'Seminar':2,'ECO1101':1,'ECO2102':1,'ECO2101':1,
       'MR5':1,'QRM3003':1,'ME':4})
  SINCHON_BONUS =  0.0  ->  -1e18   NO FEASIBLE PARTITION
  SINCHON_BONUS = 30.0  ->  -1e18   NO FEASIBLE PARTITION
```

`ECO2101` is 신촌-only (`availability` = IMPOSSIBLE at both 국제 seasons, R288) and has **no
cell at either 신촌 season**, so no partition places it. Every branch is infeasible.

`git show HEAD:partition.json` is an **831-byte, 20-entry 국제-S stub** — the table that
produced 352.569 is not in git either. It exists nowhere.

**Root cause, and it is not a one-off.** `partition.save()` is
`json.dump(d, open(OUT,'w'))` — a non-atomic full-file rewrite executed **once per entry**,
hundreds of times per run. `partition.load()` is

```python
try:    return json.load(open(OUT, encoding='utf-8'))
except Exception: pass
return {'base': {}, 'cost': {}}
```

One interrupted write leaves truncated JSON; the next `load()` swallows the decode error and
hands `build_table` an empty dict, which then rebuilds from scratch in its iteration order
`국제S → 국제F → 신촌S → 신촌F`. **That is exactly the shape observed** — the first two
complete, the third has 3 entries, the fourth has none. `build_sinchon.py`'s docstring says
*"Nothing is lost on interrupt; partition.json is only ever appended to."* It is not: the file
is rewritten whole, and the loader treats corruption as absence. `build_sinchon`'s own stall
guard cannot see it, because after a wipe the child does do work and the entry count moves.

**IMPACT**
Not expressible on the 352.569 scale, because 352.569 is no longer computable. Worse than a
crash: all 50 distinct remainders the verdict needs are present in `_future_cache.json`
(measured — 0 missing across all six branches, 113,278 rows), so **re-running
`partition_clickorder.py` or `render_v3_top50.py` right now will reprint 352.569 and the same
click order entirely from cache, against a table that is empty underneath.** Only
`partition_verdict.py` would notice, and only because it happens to re-solve nothing.

---

## F2 ⭐ `_future_cache.json`'s key omits `SINCHON_BONUS`. `partition_verdict.py` runs at 0.0 and reads values written at 30.0 — a 150-point difference.

**CLAIM**
`partition_verdict.json`'s six branch totals are computed under one objective.

**TEST** Grepped every setter of `SINCHON_BONUS`; then did the arithmetic on INDEX's own
per-semester table.

**RESULT**

```
partition_solve.SINCHON_BONUS   default 0.0
render_v3_top50.py:72           _PS.SINCHON_BONUS = 30.0
partition_clickorder.py:25      PS.SINCHON_BONUS  = 30.0
partition_verdict.py            never sets it            -> runs at 0.0
```

All three read and write the same `_future_cache.json`, keyed on
`tuple(sorted(rem.items()))` — the remainder alone. The bonus is not in the key. Neither is
which `partition.json` produced the value.

The arithmetic, from INDEX's own numbers:

```
INDEX's six semester values  49.671 + 35.569 − 7.050 + 29.749 + 49.671 + 25.069 = 182.679
INDEX's "THE REST OF THE DEGREE"                                                 332.679
difference                                                                       150.000
                                                            = 5 신촌 semesters × 30
Fall week of the winning row  19.890 ;  19.890 + 332.679 = 352.569  = the shipped total
                                        19.890 + 182.679 = 202.569  = the same plan at bonus 0
```

So `partition_verdict.py`, whose own bonus is 0.0, emitted a number carrying +150 of 신촌
bonus. It could only do that by reading the renderer's cache — which it did: the renderer ran
04:40, the verdict 04:48, and coverage is 50/50.

**Currently latent, and the next step in INDEX's own TODO detonates it.** INDEX lists
*"prof ratings not applied — re-run all four MAX_FREE"* as the open item.
`prof_ratings.csv` now holds **10 filled ratings** (김선영 0.85, 이명숙 1.0, 차성운 −0.75,
왕하영 −0.8, 김애자 0.95 …) while every `_v3_parts_f*` is stamped `PROF_RATED: 0`. Re-running
the search changes the Fall rows, hence each row's `items`, hence its remainder — producing
cache misses. Any branch with one miss is scored ≈150 low and loses outright; the current
Lang→MR margin is **5.325**.

`_sweep_sin.py` — same author, same session — keys its in-memory cache on
`(tuple(sorted(rem.items())), bonus)`. The bonus is in the key there and not here.
Third recurrence of R250.

---

## F3 `itertools.islice(product(*pins), PICKS)`: 72 cells are labelled `'OK'`, stamped `exact=True`, and hold no value. Legal placements worth up to 29.498 are silently unplaceable.

**CLAIM**
`partition.py:319` — *"Ordering by day-spread makes a truncated pick the best available one."*

**TEST**
Counted cells with `v[2] == 'OK' and v[0] is None`. For three of them, enumerated **every**
element of `product(*pins)`, filtered self-clashing ones, and ran `b1_curve.best_week` over
all survivors at the table's own `NODE_CAP=600000`.

**RESULT**

```
cells with verdict 'OK' and no value, 국제 half alone:  72

국제|F|Seminar+ME+ME        36 products,   6 legal,  0 within the first PICKS=6
   shipped cell [None, True, 'OK', None]      TRUE value 17.691 (exact)
   via 화5,6/목4 · 월5,6/수6 · 화4/목5,6

국제|S|Seminar+Seminar+Lang 272 products, 152 legal,  0 within the first PICKS=6
   shipped cell [None, True, 'OK', None]      TRUE value 29.498 (exact)
   via 화5,6/목4 · 화4/목5,6 · 화8,9/목7

국제|S|ME+ME+ME               8 products,   0 legal   — genuinely unplaceable,
   and indistinguishable in the file from the two above
```

Three separate mechanisms, all in one line:

* `islice` charges **clashing** products against the PICKS budget, so a cell with 152 legal
  placements can be recorded as having none.
* `product` varies the **last** list fastest, so with `PICKS ≤ len(pins[-1])` the first item's
  geometry is never varied at all — the day-spread ordering the docstring relies on is applied
  per item but the truncation only ever explores one of them.
* `best_exact` is initialised `True` and never touched when no product is evaluated, so a cell
  that was never measured is stamped **exact**.

`partition_solve.solve()` skips these cells (`if v is None: continue`) and cannot report that
it did — they are indistinguishable from `IMPOSSIBLE` and `UNMEASURED` in the solver's view,
which is precisely the conflation R288 was written to prevent.

**IMPACT**
The DP optimises over a strictly restricted set of partitions. The direction is one-sided —
restoring a cell can only raise Σ — but which branches gain depends on their remainders, so it
can reorder the verdict. Per-cell magnitude up to **29.498** against a **5.325** Lang→MR
margin. Sixth instance of truncate-then-maximise (after R260, R269, R276, R295, and F5 below).

---

## F4 The "weekend geometries are free" rule fires only when there is no weekday alternative. 신촌 chapel is over-charged 6.125 per semester, and the shipped plan carries two.

**CLAIM**
`partition.py:292–297` — *"WEEKEND GEOMETRIES ARE FREE … drop weekend-only geometries from the
pinned set and charge them zero."*

**TEST**
Enumerated Chapel geometries per (campus, season); pinned each weekday geometry at 신촌 F and
maximised `best_week` at `NODE_CAP=600000` against the **exact** base 52.404.

**RESULT**

```
Chapel 국제S   weekend-only: []       weekday: 화2 화3 수2 수3 수6 목2 목3 목6
Chapel 국제F   weekend-only: []       weekday: 화2 화3 수2 수3 수6 목2 목3 목6
Chapel 신촌S   weekend-only: [일1]    weekday: 수3 수10 목6 목7
Chapel 신촌F   weekend-only: [일1]    weekday: 수3 목6 수10

  일1 provenance: YCA1003 채플(3)(비대면) / YCA1007 채플(C)(비대면), room 동영상콘텐츠
                  15 신촌 sections across the six terms

신촌|F  base 52.404 (exact) ; best weekday chapel 46.279 via 수10  ->  charged 6.125
신촌|S  base 49.671          ; table 신촌|S|Chapel 41.737          ->  charged 7.934
```

The code drops the weekend geometry from the candidate list, then charges zero **only if
nothing is left**. When a weekday alternative exists it discards the free option and charges
for the weekday one — the opposite of the "you choose your section" semantics `geoms()`'s own
docstring invokes, and inconsistent with `build_canonical`'s R52 (`동영상콘텐츠` occupies
nothing). 국제 has no 일1 chapel, so the over-charge is **신촌-only**.

**IMPACT**
The shipped plan places Chapel in sem 4 and sem 8, both 신촌 F: **≈ +12.25 understated** inside
the 332.679, entirely on the 신촌 side of a campus comparison whose whole margin is a
hand-set 30-point bonus.

---

## F5 The evidence for `SINCHON_BONUS = 30` is itself a top-5 truncation.

**CLAIM**
R292's sweep (`bonus 2.0 → 4 국제 / 10.0 → 3 국제 / 30.0 → 1 국제`) establishes the bonus and
the campus plan.

**TEST** Read `_sweep_sin.py`, the file that produces that table.

**RESULT**

```python
for r in sorted(rows.get(br) or [], key=lambda x: -x['score'])[:5]:
```

Rank by Fall week, then maximise `Fall + future`. R295 already documents that the true argmax
has a Fall week of **19.890** and is *"far below the top 40"* — so it is not in the top 5
either, at any bonus. Fifth instance of the same class, sitting under the one constant the
campus plan is entirely determined by. R292's verdict table (347.467) is the pre-R295
truncated answer, so the bracket and the sweep were both derived from rows the model has since
declared wrong.

Separately, R292 derives the interval's lower bound (≈1.8) from
`국제|S 51.392 vs 신촌|S 49.671`, and 신촌|S is the only one of the four bases flagged
`exact=False`. **I could not falsify that number** — see below.

**IMPACT** Not a numeric error I can price; the bonus is the single unelicited constant that
selects between a 1-국제 and a 4-국제 plan, and the measurement chain behind it runs through a
five-row prefix. Every independent bias found in this audit (F3's missing cells, F4's chapel
over-charge, the 신촌 PICKS=2 handicap `build_sinchon.py` documents at R299) pushes 신촌 down,
i.e. inflates the bonus needed.

---

## TESTED AND CLEAN — I could not falsify these

* **The R264 parser fixes are correct.** `pools_past.parse` vs `build_canonical.seg_blocks`:
  **0 / 10,159** mismatches across all six terms. `semester_sim.parse_time`: **0 / 1,487** over
  `raw_2026F.json`. All three agree on the adversarial set — `월3,4,수3(수4)`, `화1,2,목1(목2)`,
  `수6,7(수8,9)`, `금7(금8,9,10,11)`, `(화3,4)/목3,4`, `화3(화4)/목3,4`, `월16`, `월0`,
  `토1,2`, `일3`. Both now delegate to `seg_blocks` with an identical inline fallback.
* **`k_real.json`'s regeneration is sound at the lower cap.** All **51** of my independently
  computed 2026 n=4 values (30M node cap, previous session) reproduce exactly against their
  4M-cap rebuild — **0 disagreements**. Every n=4 entry is `exact=True`; the 36 BOUND entries
  are all n=5, which `fallback.kdefer` filters out (`int(nn) == 4`). R268's claim that 4M
  suffices holds where it is used.
* **`base['신촌|S'] = 49.671` is flagged BOUND but appears to be tight.** `solve()` uses it as
  the empty-semester value and discards the exactness flag, so I re-ran
  `best_week([], 6, 신촌S pool)` at node caps 400k / 1.2M / 4M: **49.671 at every cap**
  (1.98M → 9.83M nodes), never proving exactness but never moving. R292's 1.721 campus gap
  stands.
* **Seminar at 신촌 S genuinely costs 0.** The shipped plan values sem 3 and sem 7 at exactly
  the 신촌|S base, which looked like a truncation artefact. Re-measured all four geometries at
  600k: `월6,7,8 → 49.671`, `수5,6,7 → 39.862`, `화4/목5,6 → 35.373`, `월7,8/수8 → 35.569`.
  The best one is free because it lands where the unconstrained optimum already sits.
* **R291's chapel-slot fix holds.** 0 above-baseline violations in the current table.
* **`test_v3.py`** — 21 hold / 3 broken, still R225 / R237 / R248.
* **Cache-constant stamping in the search** — `_v3_parts_f{0,1,2,99}` all carry
  `{D_LANG, GPA_GATE_MULT, MAX_FREE, PROF_W, PROF_UNRATED, PROF_RATED, TOPN=20000}` and agree
  on everything but `MAX_FREE`; `render_v3_top50`'s R263 refusal is intact. `_v3_parts_f3` is
  an empty directory and is read by nothing.

**One gap worth naming rather than measuring:** nothing in `test_v3.py` asserts the parser
agreement, the partition table's completeness, or the cache keys. R49 was reintroduced twice
in three modules precisely because no assertion held it, and F2 is R250's third recurrence.
Every finding above is invisible to the current test suite.

## NOT REACHED

`relocation.py` and `_floor.py` (read, not exercised); `plan_model.py`'s diff; the
`MAX_DEFER = 1` question INDEX itself flags as never re-tested under the partition;
`rank2.py`'s exec trap.

---

## REPRODUCE

```bash
python3 _a_cache.py     # F1: solve() on the shipped winner's remainder; cache coverage; the 150 arithmetic
python3 _a_islice.py    # F3: true values of three 'OK'-with-no-value cells
python3 _a_chapel.py    # F4: 신촌 chapel over-charge against the exact base
python3 _a_sinS.py      # clean: 신촌|S base stability over node caps
python3 _a_sem.py       # clean: Seminar@신촌S is genuinely free
```
