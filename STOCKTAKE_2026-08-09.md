# STOCKTAKE — 2026-08-09

**Registration 2026-08-25, 09:00 KST. 16 days.**
Written at Iden's request: stop, look at what was done, and what is left.
Read `INDEX.md` for navigation; this file is the state of play.

---

## THE ANSWER RIGHT NOW

**Score 43.140 · 월+금 free · 18 credits · 6 academic courses + chapel**

| slot | section | |
|---|---|---|
| chapel | `YCA1006-02` | |
| **MR** | `QRM1001-01` | Introduction to QRM |
| CC | `UIC1561-01` | Western Civilization *(fully online)* |
| CC | `UIC1551-01` | World History II |
| CC | `UIC2151-12` | Research Design & Quantitative Methods |
| **MR** | `ECO1101-06` | Mathematics for Economics 1 |
| **ME** | `STA2102-05` | a real Major Elective |
| **deferred** | **Language** | |

It takes **both** Major Required courses reachable this term, a real Major Elective,
**zero** pure free electives, keeps 월+금 clear, and maxes both tie-break rungs Iden controls.

Runner-up (39.715) defers Intro to QRM and takes Beginning Chinese instead. Margin **3.4**,
measured under the arm of the bracket that argues *against* the leader.

**Health:** `test_weights` 23/23 · `verify_rank4` 15/15 reconstruct · `test_retired`
**10 hold · 0 uncheckable · 1 broken** (correctly — see below). 7,200 candidates ranked.

---

## WHAT CHANGED TODAY

The session opened with a ranking whose top two differed by **0.73**, and that 0.73 turned
out to be two stale constants. It ends with a different #1, reached through five corrections.

### 1 · The model had no idea what a slot was worth
Iden noticed the old #1 spent **two of his four-to-five degree-long free electives** in his
first registered semester. The model priced electives at zero — correctly — but priced the
*alternatives* with static proxies (`ROLE = 8.0/2.29/0.36`, a 7-value fitted `DEFER` table).

His diagnosis was better than mine: *"the real cost comes from choosing the elective over
some other thing, the opportunity cost."* So nothing was charged to electives. Instead
`continuation.py` computes **V** — the best legal placement of everything Fall 2026 leaves
undone into semesters 3–8 — and `ROLE` and `DEFER` were **deleted**.

The ranking inverted. The old #1 fell to ~rank 4000.

### 2 · The crowding curve was measured, not assumed
| low-supply courses in a semester | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| best achievable week | 96.66 | 96.66 | 77.02 | 59.73 | 35.52 | **4.34** |
| marginal cost of the n-th | — | 0.00 | 19.64 | 17.29 | 24.22 | **31.18** |

Exhaustive over all 32 subsets, using two accelerations that were *proved* rather than
assumed (schedule monotonicity, verified on 4,000 random pairs with the run aborting on
violation; and superset seeding).

### 3 · "Doesn't change the answer" was decaying silently
Four claims had been retired with that phrase, measured against a model that was then
replaced. **`test_retired.py` now re-measures every retirement on every run.** First run
killed two. One of them — *"the widened language pool cannot matter"* — was false within the
hour: widening it changed #1 immediately.

### 4 · Mileage statistics are over APPLICANTS, not winners
Falsifiable with no external document: a **2-seat** section whose stats described the two
winners must have `avg = (min+max)/2`. Over 28 two-seat sections — **9 match, 19 don't**.
This broke three of my own estimates in both directions and dissolved a 0.002 "tie" that had
been an artefact of my bad estimator, not a property of the problem.

### 5 · Two load-bearing mechanisms were sitting in the PDFs
- **계절학기 cap = 7 credits**, sourced from 수강편람.
- **The 동점자 우선순위 ladder**, in two documents that agree verbatim — and it decides
  7 of 8 observed UIC1806 sections and every cap-12 course including a Major Required one.
  **Rung ⓗ uses 직전학기**, so this semester's credit load sets his tie-break rank in every
  future mileage round. Nothing knew that.

---

## WHAT IS NOW IN THE MODEL

weekly schedule · both arms of the 학년 gap (the late arm finally reachable) · continuation
value over 7 semesters · free-elective budget as opportunity cost · 휴학 parity · 계절학기 ·
difficulty axis + GPA gate · the full 10-course language pool · acquisition risk in both
regimes · the 72-point mileage budget · the Korean ME cap · the second-major channel ·
the tie-break ladder · and a harness that re-checks its own retirements.

---

## WHAT IS LEFT

### Has a date
| when | what |
|---|---|
| **after 8/14** | `fetch_fall2026.py` with a fresh `JSESSIONID` → `fall2026_seats.json`. `risk.p_get_freshman()` already reads that exact path. **A `sy1PercpCnt` of 0 makes a section impossible, not merely hard.** The only check that can invalidate the plan. |
| **8/15 – 8/24** | Plan B — click order and fallback chains. *Iden has said twice this is for later.* |
| **December** | The double major. It is not only a quota decision: rung ⓒ means an Economics double major lifts him above non-majors on ECO2101 and ECO2102, both Major Required. |

### Needs Iden
- **The 신촌 free-day rule.** At 국제 he dorms, so a free day pays only as part of a block
  worth travelling for. At 신촌 he commutes daily, so *every* free day saves a round trip.
  Opposite structures — and V now assigns him **four 신촌 semesters**, scored with the dorm
  rule. This is the largest single unpriced thing left, and it needs one answer from him.

### Data, no date
- **Mileage evidence for 12 of 15 ledger items.** Only Chapel (11), LHP (17) and SciRD (34)
  are priceable, so the 72-point budget is enforced but **cannot yet bind**. This is why
  `test_retired` stays red, and it is correct that it does.
- What 계절학기 actually offers — the cap is sourced, the catalogue is not.

### Logic still absent
difficulty beyond the language tier (~700 courses sit at 0) · professor quality ·
exam clashes (49 of 50 carry a 동영상 overlap) · prerequisite chains (VERIFY 23) ·
uncertainty propagation · **whether he wants the subject at all**, which the model has never
contained in any form.

---

## THE LESSON THAT REPEATED THREE TIMES

Three separate things passed green while being wrong, and all three were mine:

| | |
|---|---|
| a **verifier** that omitted the difficulty term | could not detect an error in that term |
| a **test** that searched for the string `'risk.json'` | tested the wrong thing entirely |
| a **renderer** still reading `FINAL_ranked3.csv` | showed a #1 that had fallen to ~rank 4000 |

**A green suite means only that the assertions which exist hold.** Each is now an assertion —
including a staleness check that fails if `TOP50.html` is older than the ranking it renders.

And the counterpart, from Iden: **every constraint in this project that binds across
semesters was found by him reading the output, not by the model** — the dorm (R129), the
freshman regime (R130), the Korean cap (R152), and the elective budget (R181).
