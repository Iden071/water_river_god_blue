# SHAPED-HOLE AUDIT — 2026-08-16

Prompted by `risk.py`, which was written as a deliberate placeholder returning
`1.0, 'NO DATA'` "so the model is numerically unchanged today," and which — the moment the
8/16 seat pull landed — began declaring `UIC1561`, `QRM1001` and `UIC1551` **IMPOSSIBLE**.

> **The pattern:** a neutral default is correct exactly as long as it is never exercised.
> Its first real execution happens when the data arrives, which is the one moment nobody is
> watching it. It cannot be tested by running the model, because while the data is absent
> the model is *defined* to be unchanged.

This audit enumerates every such path, classifies it, and — where possible — **forces the
active branch and looks at what comes out.**

---

## THE HEADLINE: two unelicited constants sit in the live scoring line, and NEITHER had ever been swept

```python
# research_v3.py
dif = -DIFF.D_LANG * DIFF.GPA_GATE_MULT * sum(DIFF.steps(code(s)) for s in combo)
```

| constant | value | own source comment |
|---|---|---|
| `D_LANG` | `10.0` | *"has never been elicited. Default 10.0 — sweep it."* |
| `GPA_GATE_MULT` | `1.0` | *"[P] NEVER ELICITED. Default 1.0 = inert."* |

**Both tools that were supposed to sweep them were broken, in ways that produce false
reassurance rather than errors.**

### ⛔ B-1. The branch cache was keyed only on `MAX_FREE`
`STATE = _v3_parts_f{MAX_FREE}`. Nothing about the scoring constants entered the key, so:

```
$ D_LANG=999.0 MAX_FREE=2 python research_v3.py Lang
branch Lang: cached
```

Any sweep driven through `research_v3.py` **silently returned the baseline at every grid
point.** A sweep that found "the answer is robust" would have been indistinguishable from a
sweep that did nothing, because it *was* a sweep that did nothing.

**FIXED.** The constants are now stamped into each part file and `cache_is_valid()` refuses a
stale one:

```
branch Lang: RECOMPUTING — stale: D_LANG 10.0->999.0
```

Locked by two R250 assertions, one of which perturbs `D_LANG` and demands the cache reject it.

### ⛔ B-2. `sweep_difficulty.py` has been dead since R190
```
TypeError: unsupported operand type(s) for +: 'int' and 'tuple'
```
R190 changed `p_hard_if_deferred()` to return a bracket; the sweep still adds it as a scalar.
It also reads `FINAL_ranked4.csv` (superseded) and **rescores a fixed candidate set instead of
re-searching**, so it structurally cannot find a timetable that only becomes optimal at a
different `D_LANG`.

### ✅ What the constants actually do — measured
`sweep_holes.py` (new) re-**searches** at every grid point with no cache reuse:

| `D_LANG` | gate=1.0 | gate=2.0 |
|---:|---|---|
| 0.00 | **MR** 66.329 | **MR** 66.329 |
| 5.00 | Lang 64.633 | Lang 64.633 |
| 10.00 | Lang 64.633 ⭐ | Lang 64.633 |
| 20.00 | Lang 64.633 | Lang 64.633 |
| 45.00 | Lang 64.633 | Lang 64.633 |

Refined: the flip sits **between `D_LANG` 1.0 and 2.0**, against a default of **10.0** — a
5–10× margin. The verdict is not sensitive to the constant nobody elicited.

**`GPA_GATE_MULT` is bit-for-bit inert, and the reason matters.** The winning branch *defers*
Language, so the timetable contains no language course, so `sum(DIFF.steps(...)) = 0` and the
entire `dif` term is zero — the multiplier is multiplying nothing.

> ⚠️ **It is inert only while Language is deferred.** If the verdict ever flips to *taking* a
> language — which it does at `D_LANG < 2` — `GPA_GATE_MULT` becomes live scoring, and it has
> never been elicited. It is not a dead constant; it is a dormant one.

---

## CLASS A · LIVE and exercised (safe, now measured)

| path | default | status |
|---|---|---|
| `difficulty.D_LANG` | 10.0 | verdict flips only below ~2 (R251) |
| `difficulty.GPA_GATE_MULT` | 1.0 | inert *because the winning branch charges zero steps* — dormant, not dead (R251) |
| `eligibility._seats()` | `{}` on any exception | a malformed `fall2026_seats.json` silently disables the year filter. Caught by the R247 assertion (`len(SEATS) > 100`) |

## CLASS B · DORMANT — would activate on data arrival, and have never executed for real

| path | returns while dormant | what happens when it activates |
|---|---|---|
| `risk.p_get_freshman` | `1.0, 'NO DATA'` | **ACTIVATED 8/16 AND WAS WRONG** — tested `sy1==0` without `any(sy)`, declaring the recommendation impossible. Fixed; now agrees with `eligibility.year_barred` on all 179 sections |
| `risk.p_win_bracket` | `1.0, 1.0, 'NO DATA'` | **6 of 12** required courses have no mileage history — `ECO2101, ECO2102, QRM3003, QRM3004, QRM3005, STA2102`. A probability of **1.0 is fabricated certainty**, not neutrality. Nothing consumes it today |
| `semester_sim.sections_for` | `'NO DATA'` | 21 of 48 (course, term, campus) combinations have no sections at all |
| `plan_model` `DM`×12, `FREE`×5 | assumed hours | **17 of 38 ledger units** have no course identity; they are the filler every K measurement sits on. December |
| `rank4.DM_MAJOR` | `None` | the second major; December (R147). `rank4` is not in the v3 path |
| `continuation.summer_eligible` | NO DATA | `continuation` is not in the v3 path |
| `crowding.json` | convex where all six measured curves are concave | not used by v3; the discrepancy is asserted so it cannot be used silently (R228) |

## CLASS C · Absent files referenced only by superseded modules — benign
`FINAL_ranked.csv`, `FINAL_ranked2.csv`, `FINAL_top5000.json` (`rank.py`/`rank2.py` outputs,
never read back), `incumbent.json` (`rank4_branch`), `강의목록_전체_v3.xlsx` (optional Spring
source in `fetch_mileage.py`, which degrades to the canonical catalogue and says so).

---

## WHAT THIS AUDIT CHANGES ABOUT HOW TO READ THE MODEL

1. **"Numerically unchanged today" is not a safety property.** It is a statement that the code
   has never run. `risk.py` was correct under that description and wrong on first contact.
2. **A neutral default is a *value choice*, not an abstention.** `p_win_bracket` returning
   `1.0` does not mean "unknown", it means "certain" — and it is the most optimistic value in
   the range. `k_inventory` and `semester_sim` at least label theirs `'NO DATA'` in the output.
3. **A cache whose key omits the scoring constants converts a sensitivity analysis into a
   tautology.** This one did, for both constants, for the life of the v3 model.
4. Every remaining Class-B entry should be assumed wrong until it has been forced to run.
   That is what §CLASS B's first row cost.

## OPEN

- `risk.p_win_bracket`'s `1.0` for the six no-history courses should return a **bracket with
  an explicit unknown arm**, not certainty, before anything consumes it.
- R190's "top TWO of a **2-seat** section" premise rests on `atnlcPercpCnt`, which R248 shows
  is not capacity. The `test_v3` R248 leak guard is left failing on `difficulty.py` for this
  reason — the fix is to re-derive the premise, not to rename the variable.
