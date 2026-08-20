# STAGE 4 SHAPE DIAGNOSTIC — 2026-08-19

This file records a **one-time diagnostic**, not a truth source and not proof evidence.
`SPEC.md` and explicit current user confirmations remain authoritative.

The purpose was to answer a narrow question before asking for any more preference information:
**do the three still-unresolved timetable-shape families actually appear in real exact Fall
candidates, and can the archival parameter uncertainty move utility enough to be worth caring
about?**

---

## Method

Source candidate family:

- real Fall 2026 catalogue
- freshman-registration screened resolved core: 176 sections
- exact bitset DFS backend
- first 500,000 emitted feasible candidates
- diagnostic lens retained only candidates with at least 12 known ordinary credits
  - this 12-credit floor is **not** a model constraint
  - 499,996 candidates remained
  - 4 were below the diagnostic floor
- no schedule-unresolved candidates were skipped in this resolved-core batch

The 500,000 candidates are an **exact DFS prefix, not a random or representative sample**.
Counts can prove that a feature occurs in the exact family; they cannot estimate its global
frequency or whether the eventual optimum depends on it.

Shape values were supplied only by `fall_shape_diagnostics.py`, reconstructing the old
R140-era provisional scenarios:

- first attached trip/home value 12 / 13 / 14
- weekend exponent 1.2 / 1.4 / 1.6
- Friday-event value 4 / 13/3 / 14/3
- long-run correction beyond the confirmed four-period -8 anchor = 0 in every archival
  scenario, because the legacy model treated every >=4-period run as the same -8 marathon

These are **diagnostic scenarios only**.  They are deliberately not `PreferenceValue`s or
`ProofUpperBound`s and cannot enter proof-safe pruning.

GitHub Actions source: Stage 4 foundational tests run #496, successful.

---

## One-time 500k-prefix result

Family activation counts among the 499,996 diagnostic candidates:

| conceptual family | prefix candidates activating it |
|---|---:|
| Friday event-window value | 231,699 |
| long continuous-run shape beyond four periods | 263,102 |
| weekend-attached run shape beyond first weekday | 14,435 |

Again, these ratios are **not population estimates**; DFS order is highly structured.

Observed state dimensions in this prefix:

| state | activations |
|---|---:|
| Friday event free | 231,699 |
| long-run delta, length 5 | 93,834 |
| long-run delta, length 6 | 16,440 |
| long-run delta, length 7 | 5,388 |
| long-run delta, length 8 | 174,526 |
| long-run delta, length 9 | 10,170 |
| weekend extra total, 2 attached weekdays | 14,435 |

No length-10..15 long-run state or 3..5-attached-weekday weekend state happened to appear in
this prefix.  That is **not** evidence that those states are globally impossible.

Maximum low-vs-high archival scenario spread observed in the prefix:

- **13.538 utility points**
- example candidate section IDs:
  - `ANT2105-01-00`
  - `ASP2010-01-00`
  - `ASP2022-01-00`
  - `ASP2033-01-00`

---

## What this tells us

### 1. None of the three conceptual families can simply be deleted as dead code

Friday-event and long-run states appear extensively in this exact prefix.  Weekend-run
curvature appears less often here, but it does occur.

### 2. The weekend-run family is potentially material

Within the old provisional 1.2..1.6 exponent / 12..14 trip-value family, the unresolved shape
can help move an observed timetable by roughly the same order as a 09:00-start anchor.
That is large enough that we should not silently freeze the old midpoint.

This does **not** say the final recommendation is sensitive to the weekend shape; course,
degree, future, registration, and global-search effects are not represented by this prefix
spread.

### 3. Friday parameter uncertainty looks numerically small *within the archival family*

The old Friday-event point ranges only from 4 to 14/3, a spread of about 0.667, and the Friday
feature can activate at most once per timetable.  If the current preference still lies near
that archival family, fine calibration is unlikely to matter much.

But this is not yet a proof ceiling: the archival relation has not been re-confirmed under the
current authority rules.

### 4. The long-run family is the opposite problem: high exposure, no archival sensitivity range

The old model used a flat >=4-period marathon penalty, so all three archival scenarios assign
zero *additional* correction beyond the confirmed four-period -8 anchor.  Therefore a zero
spread here means only "the legacy model had no shape," not "the true shape cannot matter."

A one-sided statement such as "a 5+ continuous run is never better than an otherwise identical
four-period run" would immediately give every long-run delta a proof-safe upper ceiling of 0,
but that statement has **not** been promoted merely because it is intuitive.

---

## Engineering consequence

The next proof dependency remains **one-sided optimistic ceilings**, not precise point scores:

1. Friday-event value upper ceiling
2. long-run correction upper ceiling(s)
3. weekend-attached extra-total upper ceiling(s)

The new `fall_upper_bound_readiness.py` and `fall_intrinsic_branch_bound.py` are already wired
so these ceilings can be supplied without inventing lower bounds or point estimates.  Until
then the real branch bound returns `INPUT_BLOCKED` rather than pruning unsafely.

Registration obtainability remains a separate risk/contingency layer and is not being turned
into a preference penalty to make this audit pass.

---

## CI policy after this one-time audit

Running shape analysis over all 500,000 candidates increased the full test suite substantially,
so the recurring CI smoke now reuses only the first 50,000 already-generated candidates.
The structural 500,000-candidate bitset benchmark itself remains unchanged.  The larger result
above is preserved here so it does not need to be recomputed on every commit.
