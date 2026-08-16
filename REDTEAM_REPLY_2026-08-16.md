# RED-TEAM REPLY — 2026-08-16

Baseline reproduced exactly before anything was attacked: per-branch
`max(score + Σunit_cost)` over all 3000 rows, MAX_FREE=2, D_LANG=10.0, minus `kdefer`
as shipped, gives **defer Lang 78.622 · defer MR 64.379 · margin 14.243** — the numbers in
the brief, to three decimals. Everything below is measured against that reproduction.

Harness: `_fixparse.py`, `_recompute_k.py`, `_branchmax.py`, `_boundtest.py`, `_disp.py`,
`_k_broken.json`, `_k_fixed.json`, `_branchmax.json`.

---

## F1 ⭐ `pools_past.parse` silently drops parenthesised time blocks. `kdefer('Lang')` is wrong by 21.340 and the verdict inverts.

**CLAIM**
`k_real.json` → `Lang·hard | 2026 | 월3,4 | 4` = **−4.725**. This single number *is*
`kdefer('Lang')` (it is the `min()` over the 11 receiving geometries), and it is the whole
reason `total(Lang)` exceeds `total(MR)`.

**TEST**

1. Traced `pools_past.parse('월3,4,수3(수4)')` by hand and by execution.
   `.replace('/',',').split(',')` yields the token `'수3(수4)'`. `tok.strip('()')` strips
   nothing (neither end is a paren). `''.join(c for c in tok if c.isdigit())` yields `'34'`,
   which fails `1 <= int(n) <= 15` — so **the entire 수 block is discarded**.
2. Compared `pools_past.parse` against `build_canonical.seg_blocks` (the char-scan parser the
   live path uses) over every section in `past_terms.json` + `raw_2026F.json`.
3. Confirmed against the live canonical record for the same source string.
4. Re-ran the exact `k_real` computation twice — once as shipped, once with `parse` replaced by
   `build_canonical` semantics — with `b1_curve.best_week(node_cap=30_000_000)` in both arms.
   Every value returned `exact=True`; no truncation in either arm.
5. Re-ran the full per-branch search and applied both K tables.

**RESULT**

Reproduction of the as-shipped arm is bit-exact against `k_real.json` (all 13 × 2026 values).

```
parse mismatch, all six terms: 1,047 / 10,159 sections (10.3%), 2,122 nominal hours lost
  월3,4,수3(수4)   n=70   pools_past: 월3,4        build_canonical: 월3,4/수3,4
  화1,2,목1(목2)   n=45   pools_past: 화1,2/목12   build_canonical: 화1,2/목1,2   ← fabricates 목12
  수6,7(수8,9)     n=18   pools_past: 수6,9        build_canonical: 수6,7,8,9     ← fabricates 수9
  금7(금8,9,10,11) n=19   pools_past: 금9,10,11    build_canonical: 금7,8,9,10,11 ← drops 금7
```

Live cross-check, same string, `canonical_2026F.json`:

```
YCF1452-02-00  t=월3,4,수3(수4)  canonical time=[[0,3],[0,4],[2,3],[2,4]]   (4 blocks)
                                 pools_past    =월3,4                       (2 blocks)
```

This is not a modelling disagreement. `build_canonical`'s docstring: *"Parenthesised periods
count as occupied (R54)"*, verified from a 강의계획서. `pools_past.parse`'s own docstring:
*"Parenthesised blocks are kept (they hold a nominal slot)."* Both modules **intend** the same
thing; one fails to do it. R54 settles the convention; R49 (2026-08-04) records this identical
defect being found and fixed once already in `fetch_2026_fall.py` — 101 of 661 sections — and
fixed *with a char-scan parser*, which `pools_past` then did not reuse.

**5 of Lang·hard's 11 geometries are parser artefacts, and they are the four cheapest plus one:**

| as shipped | K | corrected | K |
|---|---:|---|---:|
| 월3,4 ⛔ | **−4.725** | 월3,4/수3,4 | 16.615 |
| 화3,4 ⛔ | −2.487 | 월5,6/수6 | 16.615 |
| 월5,6 ⛔ | 0.209 | 월7,8/수8 | 16.615 |
| 화7,8 ⛔ | 5.688 | 화4/목5,6 | 18.685 |
| 월5,6/수6 | 16.615 | 화5,6/목4 | 18.685 |
| 월7,8/수8 | 16.615 | 화3,4/목3,4 | 21.186 |
| 화4/목5,6 | 18.685 | 화8,9/목7 | 24.919 |
| 화5,6/목4 | 18.685 | 화7/목8,9 | 25.919 |
| 화8,9/목7 | 24.919 | 월5,6/수5,6 | 27.240 |
| 화1,2/목12 ⛔ | 27.507 | 화7,8/목7,8 | 30.728 |
| 화7/목8,9 | 27.525 | 화1,2/목1,2 | 32.935 |
| **min** | **−4.725** | **min** | **16.615** |

Every one of the 35 신촌-Fall hard-language section-observations behind those five rows is a
3-credit course written `월3,4,수3(수4)` or similar — i.e. 4 nominal hours read as 2.
The **majority** (35 of 53) of 신촌-Fall hard-language sections are mis-parsed.

Only Language moves. MR (`목4,5,6` = 0.000), WCiv (24.643), LHP (16.615), SciRD (28.294) are
unchanged, and the 2026 baselines are identical in both arms (국제S n=5 = 69.017, 신촌F n=5 =
64.684), which isolates the effect cleanly to the pinned geometries.

```
branch    pre_K   K shipped  total    K corrected  total
-        33.333      0.000   33.333        0.000   33.333
MR       64.379      0.000   64.379        0.000   64.379
WCiv     68.647     24.643   44.004       24.643   44.004
LHP      56.647     16.615   40.032       16.615   40.032
SciRD    64.822     28.294   36.528       28.294   36.528
Lang     73.897     -4.725   78.622       16.615   57.282

SHIPPED : defer Lang 78.622, margin 14.243
CORRECTED: defer MR  64.379, margin  7.097
```

**IMPACT**
**−21.340 points on the Language branch. 78.622 → 57.282. The verdict inverts to defer MR,
which wins by 7.097.** The recommended timetable changes with it — the MR-branch optimum is
`UIC1561-01-00 · UIC1551-01-00 · UIC2151-06-00 · UIC1805-02-00 · YCK1998-03-00 ·
ECO1101-06-00 · YCA1006-01-00`, i.e. QRM1001 comes out and a Beginning-tier language goes in.
This is larger than R260's 13.989 and larger than every margin this model argues about.

`unit_cost` is **not** affected: 0 sections of ECO1101, STA2102, QRM1001, UIC1561, UIC1551,
UIC2151, UIC1805, UIC1806 hit the parse bug in any of the six terms, so `k_real.json['disp']`
and the `pre_K` column above stand.

---

## F2 `semester_sim.parse_time` has the same defect, and it is applied to 신촌 only

**CLAIM**
`semester_sim.parse_time`'s docstring: *"Mirrors build_canonical."*

**TEST** Same differential against `build_canonical.seg_blocks`, over `raw_2026F.json`; then
rebuilt `_SIN` with the corrected parser and re-measured `b1_curve.pool_for('신촌')`.

**RESULT**

```
월3,4,수3(수4)     semester_sim: 월3,4        correct: 월3,4/수3,4
화1,2,목1(목2)     semester_sim: 화1,2/목12   correct: 화1,2/목1,2
수6,7(수8,9)       semester_sim: 수6,9        correct: 수6,7,8,9
금7(금8,9,10,11)   semester_sim: 금9,10,11    correct: 금7,8,9,10,11

raw_2026F 신촌: 194 / 775 sections mis-parsed (25.0%)
b1_curve.pool_for('신촌'):  147 signatures as shipped  →  173 corrected  (+17.7%)
```

The asymmetry is the point. `semester_sim._INTL` is built from `rank3.build()`, i.e. from
`canonical_2026F.json` — **0 of 341 sections mismatch canonical**. `_SIN` is built from
`raw_2026F.json` through the broken `parse_time`. So the 국제 pool goes through the correct
parser and the 신촌 pool does not — and 신촌 is precisely where `Lang·hard` and `LHP`/`SciRD`
are received. This is error class 7 in a new form: not the wrong campus, but the *right*
campus reached through a different and worse code path.

**IMPACT** Not on 78.622 directly — `fallback.kdefer` reads `k_real.json` (pools from
`pools_past`), not `b1_K.json`. But `b1_curve.run()` is step 3 of the live pipeline in
`INDEX.md`, `b1_K.json` is its output, and every K curve and every `CASES` geometry in that
file inherits a 신촌 pool that is 15% short. Third independent instance of R49.

---

## F3 `prof_ratings.csv` contains 29 professors and **zero** ratings; `prof_compare.py` is a rigid translation

**CLAIM** §2.3 asks whether the `k * PBMAX` ceiling stays sound *"especially with a non-empty
`prof_ratings.csv`"*. `prof_compare.py` reports the 0-vs-max bracket.

**TEST** `len(prof.ratings())`; range of `prof.bonus` over every section in the pools; then
differenced `prof_compare.json`'s two arms row by row.

**RESULT**

```
prof.ratings() -> 0 entries   (the file has 29 data rows; every `rating` cell is empty)
prof.bonus over all pooled sections: min 0.0, max 0.0
prof_compare.json:  B_unrated1[i].total - A_unrated0[i].total = +70.000 for every row
                    (7 sections × PROF_W 10.0 × UNRATED 1.0)
```

Every candidate timetable holds exactly 7 sections, so `UNRATED=1.0` adds exactly +70 to
every row. The two arms are related by a constant. The comparison **cannot** reorder anything,
by construction, and its agreement is therefore not evidence that professors cannot change the
decision. Error class 4: a neutral default whose output is certainty. The professor term is
also identically zero everywhere, so `PROF.bonus` in the `esig` key, `PBMAX`, and the
`PROF_W`/`PROF_UNRATED` cache stamp are all currently inert.

**IMPACT** 0.000 points today. The claim it is read as supporting — that the professor axis is
closed — is unsupported by any measurement.

---

## F4 The stated "single load-bearing modelling assumption" is a consequence of F1, not a live sensitivity

**CLAIM** `INDEX.md` / R262 §3: *"`kdefer()` aggregates Language's 11 receiving geometries with
`min()`; under `median()` the answer inverts to defer MR … it is now the single load-bearing
modelling assumption behind the answer."*

**TEST** Recomputed every branch total under `min`, `median` and `mean` aggregation, with both
the shipped and the corrected K tables. Also tested the `MR` special case (`KD['MR'][y].get('목4,5,6')`,
a pinned geometry rather than an aggregate) against replacing it with the same aggregate.

**RESULT**

```
SHIPPED    min    -> defer Lang 78.622  margin 14.243
           median -> defer Lang 57.282  margin  0.344      (MR 56.939)
           mean   -> defer Lang 60.330  margin  3.392
CORRECTED  min    -> defer MR   64.379  margin  7.097      (Lang 57.282)
           median -> defer MR   56.711  margin  3.999      (Lang 52.711)
           mean   -> defer MR   56.711  margin  5.554      (Lang 51.157)
```

The MR special case is inert: `KD['MR']['2026']['목4,5,6']` = 0.000 and
`min(KD['MR']['2026'].values())` = `min(0.000, 15.337)` = 0.000, so pinning and minimising
agree in 2026. (It is fragile rather than wrong — `목4,5,6` was observed in exactly one term,
`2026-1`; if it is not re-offered, `kdefer('MR')` returns `None` and the entire MR branch is
dropped from `search()` without a message. That did not happen here.)

**IMPACT** Once F1 is fixed, defer-MR wins under all three aggregators, so the min-vs-median
question stops deciding the answer and the R262 §3 warning can be closed — but in the opposite
direction from the one the brief expects. The reason `min()` looked load-bearing is that four
fabricated 2-hour geometries manufactured a 21-point left tail that only `min()` could reach.

---

## TESTED AND CLEAN — I could not falsify these

* **§2.3, the branch-and-bound ceiling.** Extracted `run_branch`'s source, replaced
  `if week_value(p,f)[0] + b + k*PBMAX + pen + dif + pb + ch_c <= best[0]: return` with
  `if False: return`, and compared `best` on 3 randomly sub-sampled pools (5 sections per
  requirement, 3 chapels, 60 electives) × 4 branches × 2 rating regimes. **24/24 identical to
  1e-6.** Run once as shipped (0 ratings) and once with synthetic ratings injected for all 220
  professors drawn from {−1,−0.5,0,0.5,1}, i.e. `PROF.bonus` spanning ±10.0 — the regime the
  brief says the bound must survive. It survives. Argument order is also consistent:
  `week_value(pm, tm=0)` takes (presence, fixed) and `run_branch` calls `week_value(p, f)`.
* **§1.8, the `_v3_parts_f0/f1/f2` union.** Already guarded — `render_v3_top50.py` lines 75–110
  collect `consts` per part file, pop `MAX_FREE` (the constant they are supposed to differ in),
  and `sys.exit(1)` on any disagreement. Verified all 24 part files carry identical stamps
  `{D_LANG 10.0, GPA_GATE_MULT 1.0, PROF_W 10.0, PROF_UNRATED 0.0, PROF_RATED 0}`.
* **§2.5, the eligibility year gate.** `eligibility.py:94` is `if any(sy) and sy[0] == 0`, i.e.
  two-sided and in the documented direction. The consumers are `research_v3.build`,
  `fallback.search` and `test_v3`; all three call `eligibility.apply` on the same pool object
  before any scoring.
* **`test_v3.py`.** 21 hold / 3 broken, and the 3 are exactly the documented ones — R225
  (17 DM/FREE units with no course identity), R237 (4 duplicate OPEN rows), R248
  (`difficulty.py` reads `atnlcPercpCnt`). No failure has silently become a different failure.
* **`unit_cost` / `k_real.json['disp']`.** Checked directly for parse-bug exposure across all
  six terms: 0 affected sections among the 8 course codes that feed it or appear in either
  branch optimum.

## NOT REACHED

`rank2.py`'s exec trap (§2.4) — inspected, not stress-tested; `k_real`'s `n = 4` / 2027–2029
campus-season assignments (§2.2) beyond the parser; `risk.py`'s 신촌 acquisition measurement.

---

## REPRODUCE

```bash
python3 _recompute_k.py broken 2026            # reproduces k_real.json's 2026 values exactly
python3 _recompute_k.py fixed 2024,2025,2026   # the corrected K table
python3 _branchmax.py                          # per-branch max(score + Σunit_cost)
python3 _boundtest.py none ; python3 _boundtest.py synth
```
