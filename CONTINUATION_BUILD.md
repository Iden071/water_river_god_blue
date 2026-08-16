# THE FOUR-YEAR LAYER — built 2026-08-09

**Read this instead of `HANDOFF_2026-08-07.md` for anything about deferral, quotas, or why
a course is worth taking.** Registration 2026-08-25 — 16 days.

---

## WHY THIS EXISTS

Iden, looking at the old #1:

> "BIZ1101 is a pure elective, also is YCE1253-01-00. But that timetable is considered #1,
> right? So I was curious, because considering the double major, I have like about 5 pure
> electives to fit within 7 semesters. But I already have 2 this semester."

His arithmetic was exact. And his diagnosis of the fix was better than mine:

> "Electives not costing anything is probably right. Because the real cost comes from
> choosing the elective over some other thing, the opportunity cost."

So nothing was charged to electives. What was built is the thing whose absence made them
look free: **a model of the six semesters after this one.**

---

## THE ONE-LINE CHANGE

**before**  `score = week + Σ role bonuses + Σ year penalties + DEFER[deferred]`
**after**   `score = week + Σ year penalties + [ V(remainder) − V(reference) ]`

`ROLE` (8.0 / 2.29 / 0.36) and `DEFER` (7 fitted numbers) are **removed, not retuned**.
Their two jobs — *quota progress is worth something*, *deferring costs something* — turned
out to be one quantity, and it is now derived.

`V(remainder)` = the best legal placement of everything Fall 2026 leaves undone into
semesters 3–8, respecting campus, term, academic year, credit caps and chapel limits;
`−∞` if no legal placement exists.

---

## WHAT THE NUMBERS SAY

### The credit ledger reconciles exactly
`106.5 = 126 − 19.5 done`, split CC 19.5 · MR 18 · ME 18 · 2nd major 36 · **free electives 15.0**.
Five free-elective courses for the whole degree — four if the second major is 39 credits.

### The crowding curve, measured over all 32 subsets
| low-supply courses in a semester | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| best achievable week | 96.66 | 96.66 | 77.02 | 59.73 | 35.52 | 4.34 |
| marginal cost of the n-th | — | 0.00 | 19.64 | 17.29 | 24.22 | **31.18** |

The first one is free. The fifth costs 31. Convex, exactly as R144 predicted from one point.

### Deferral cost — computed vs R117's fitted table
| defers | computed | fitted | |
|---|---|---|---|
| **MR (QRM1001)** | **−39.175** | −17.700 | 국제-only · 1 section · chart-year 1 |
| WCiv | −31.175 | −12.000 | 국제-only |
| LHP · SciRD · **Lang** | −28.508 | −13.000 / −14.990 / −16.970 | Lang has **no chart year** |

Every fitted number understated the cost by about half, and the ordering is now structural.
**The gap deciding #1 vs #2 was 0.73 under the old table (R180). It is 10.667 now.**

### The answer to the question Iden asked
| 6th slot | vs a free elective |
|---|---|
| free elective | 0.000 |
| **ECO1101 (Major Required)** | **+31.175** |
| **a QRM Major Elective** | **+31.175** |

---

## THE RESULT

**#1 — score 46.640, 월+금 free**

| slot | course | |
|---|---|---|
| chapel | YCA1006-02 | |
| MR | **QRM1001-01** | Introduction to QRM |
| CC | UIC1561-01 | Western Civilization |
| CC | UIC1551-01 | World History II |
| CC | UIC2151-12 | Research Design & Quantitative Methods |
| MR | **ECO1101-06** | Mathematics for Economics 1 |
| ME | **STA2102-05** | a real Major Elective |
| deferred | **Language** | |

**The ranking inverted.**

| | |
|---|---|
| the old #1 (two pure electives) is now | **rank 4037** |
| the new #1 was, under the old model | **rank 4114** |
| of the old top 50, still in the new top 5000 | **4**, at ranks 1136–1240 |

All 50 of the new top 50 still hold **월+금 free** — the week was not traded away to buy the
quota progress. The old model was simply blind to half the objective.

---

## WHAT WAS CHECKED

- every one of the 15 top rows reconstructs exactly from `week + year penalty + chapel + ΔV`,
  through a code path that does not share the search's arithmetic
- every distinct remainder in the top 200 admits a legal 6-semester plan (no `−∞` hiding
  behind a good-looking score)
- `test_weights.py` — **23/23**
- the two search accelerations are *proved*, not assumed: schedule monotonicity is verified
  on 4000 random pairs and the run aborts if violated

### One error found and fixed mid-build (R183)
The first run returned a #1 that **deferred Intro to QRM**. Cause: a hand-typed dict in my
own code claimed `ECO1103/ECO1104` were QRM Major Electives. The catalogue disagreed —
`ECO1104-07-00` has `qcat=None`, `_qrm_me=False` — and `VERIFY.md` item **22b** had that
exact question parked and open. The list overrode the data and manufactured the answer.
Now the item is read off the section and written to `elective_items.json`.

---

## ⚠️ WHAT IS STILL ASSUMED — and would move the answer

| | assumption | if wrong |
|---|---|---|
| **2nd major = 36 cr, at 신촌** | Iden's candidates (Math · Economics · CS) are all 신촌 colleges | a UIC-internal double major changes the campus arithmetic and the free-elective count (12 vs 15) |
| **Language is campus-'any'** | R143 called it 국제-only; R166 widened the pool to non-UIC courses that exist at 신촌 | Language is what #1 defers — this one sits directly under the live decision |
| **the crowding curve transfers** | measured on the Fall 2026 국제 catalogue, applied to 2029 신촌 (G-9) | the *shape* is what the model uses; the absolute level should not be quoted as a fact about 2029 |
| **quota progress is flat at +31.175** | any low-supply item retired early saves the same marginal crowding | it cannot currently distinguish a scarce requirement from an abundant one. R172 warned about losing exactly this signal |
| **the Korean 12-credit ME cap is not enforced** | R152/R105 cap Korean 상경/응통 sections at 4 courses / 12 cr of Major Credit | **same class of gap Iden just caught** — a budget that is priced but not enforced |

**The 8/15 seat check (G-1) is still the only thing that can invalidate the plan outright,
and it still needs Iden to run `fetch_fall2026.py` with a fresh session cookie.**
