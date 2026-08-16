> ⚠️ **PARTLY SUPERSEDED 2026-08-07 — see `HANDOFF_2026-08-07.md` §2 for the current list.**
> Closed since this was written: **D-1** (withdrawn — it was never a preference, R146/R165) ·
> **D-2** (dead — R160 proved it cannot change the ranking) · **D-3** (answered, REST = 7.0) ·
> **D-4** (2교시 confirmed) · **D-6** (ME competes; measured at 2.29, R150/R152) ·
> **D-8** (double major confirmed, R147).
> Still open and still Iden's: **D-5** seminar cost · **D-7** professor ratings ·
> **D-9** 신촌 free-day rule · **D-10** campus dominance · plus the four new factors in the
> handoff — **risk**, **difficulty**, **availability-over-time**, **quota enforcement**.

# WHAT WE NEED — current as of 2026-08-07 (rewritten end of session)
**Registration: 2026-08-25, 09:00–17:00 KST. 18 days.**

Supersedes the morning version of this file, which is now wrong in several places
(D-1 was withdrawn, D-3 was answered, D-2 was partly answered). Companion to `RULES.md`
(settled, R1–R146), `VERIFY.md` (being checked), `PLANS.md` (deferred).

**The critical path is on me, not on Iden.** Two builds block a trustworthy ranking. Only
two small values are genuinely owed by Iden, and neither is hard.

---

## THE ONE BLOCKER — B-1 · the receiving semester

Everything about deferral hangs on a number that does not exist yet.

Deferring a requirement out of Fall 2026 **gains** schedule quality here (measured, R142:
+14 to +33 raw depending on which one) and **costs** two things:
1. the year-gap penalty — **now computed** (R146: −2.67 to −15.08 for QRM입문 by landing year);
2. the schedule quality lost in the semester that **receives** it — **not computed**.

Without (2) the comparison is one-sided, and every deferral verdict the ranker produces is
untrustworthy. This is why QRM입문 got three different answers in one session (R143 → R144).

**Build:** model a future 국제 Spring using the Fall 2026 국제 pool as a stand-in, and for each
deferral option compute the best achievable week there given what it must already carry
(QRM3003, plus whatever was deferred). Then deferral = gain here − loss there − year gap.
The convexity measured in R144 predicts the loss there is *smaller* than the gain here while
that semester is near-empty, and grows sharply as it fills. That prediction is testable.

⚠️ Until B-1 exists, **do not present a ranking as final**, and do not draw conclusions from
the current deferral pattern.

---

## ALSO MINE — in priority order

| # | item | why it matters | blocked on |
|---|---|---|---|
| **B-2** | Replace R117's `DEFER` table with the computed year-gap cost (R145/R146) | the table is a fitted inheritance from a superseded scale; the replacement is derived | B-1 |
| **B-3** | Add the 4 UIC Seminar sections to the pool | the model still contradicts Iden (R131). No separate defer cost needed any more — the year penalty prices them (chart yr 2–4) | nothing — **do this first** |
| **B-4** | RISK term: thin future supply | 1 신촌 SciRD section, 2 신촌 LHP. Countable from offering history, **not** a preference — must not be folded into the year penalty | nothing |
| **B-5** | Re-run the 9 remaining 2-deferral pairs | R121 only partially re-verified after R129 (R132) | B-2 |
| **B-6** | Pull Fall 2026 per-학년 quotas after 8/14 | a 1학년 share of 0 makes registration **impossible**, not merely hard (R134) | calendar |
| **B-7** | `RUN_EXP` sensitivity: does [1.2, 1.6] change the top-50? | if not, D-2 dies and Iden never answers it | nothing |
| **B-8** | Add STP3007 to the QRM chart map (R133) | completeness; not offered this Fall, so no current effect | nothing |

---

## OWED BY IDEN — both small

### V-1 · the 2교시 penalty has never once been confirmed
Live: **−5** for a day starting at 10:00, against **−10** for one starting at 9:00. Flagged
`[P] 미확인 추정치` since the first session. It is the **only** schedule constant with no
statement behind it, and it fires on a large share of timetables.

> **Need:** is a 10:00 start half as bad as a 9:00 start, or less than that?

### V-2 · does Major Elective progress compete for a slot?
`defer_costs.json` carries **−8.43** for ME but nothing uses it — ME appears only as a +6
bonus on electives. So "make progress on the 24 ME credits" is currently a nice-to-have,
not a requirement that can win a slot.

> **Need:** should ME compete with the five requirements for one of the six slots, or stay a
> tiebreak among electives? It changes what the 6th course is.

---

## OWED BY IDEN — but NOT blocking Fall 2026

Recorded so they are not lost. All three matter for the four-year layer; none changes this
semester's answer, because Fall 2026 is 국제 regardless.

- **V-3 · 신촌 free-day rule.** At 국제 you dorm, so a free day only pays if it is part of a
  block worth travelling for. At 신촌 you commute daily from home, so *every* free day saves a
  round trip, isolated ones included. Opposite structures; the model has only the dorm one.
- **V-4 · confirm campus still dominates.** R126 pinned "one 신촌 semester > a 월+금 week" to a
  ceiling of 63 that has since moved (R129/R142). The conclusion probably survives — you said
  "much much much more preferable" — but the justification as written no longer holds.
- **V-5 · double major.** Mathematics · Economics · (low) CS. December. Sets the ME and
  free-elective quotas the whole multi-semester layer runs on.

---

## ANSWERED TODAY — for the record

| | was | now | how |
|---|---|---|---|
| rest value of a genuinely empty weekday | 4.70 | **7.00** | bracketed by 3 comparisons (R140) |
| one weekend-attached day at home | 18.75 | **13.00** | "a free Friday = two 9am starts" (R142) |
| Friday events bonus | 6.25 | **4.333** | preserves the older "월 = 금의 75%" — cross-checks (R142) |
| how sharply length scales | 1.6 | **1.4** `[P]` | bracket [1.2, 1.6]; Iden: *"can't quantify tbh"* (R142) |
| 학년 penalty | one-sided | **two-sided** | early/late = 1.5, late scales sharply (R145/R146) |
| deferral cost | 7 fitted anchors | **derived from chart year** | R146 supersedes R117 |

**Withdrawn today:** D-1 (never a preference — it is a computation, R143/R146) · the block-
grouping question (alternating weeks are not in the choice set — a timetable repeats every
week) · the increment questions (R141 — ask about states, compute differences).

---

## THE HONEST STATUS
Every schedule constant now traces to something Iden said, except `2교시` (V-1) and the
magnitude of `RUN_EXP` (bracketed, may not matter — B-7). The requirement/deferral side is
half-built: the year-gap arm is derived and live, the receiving-semester arm does not exist.
**Nothing here is ready to register from yet.** The gap is B-1, and it is 18 days out.
