# Stage 4 visible timetable leaderboard — 2026-08-20

This is the first deliberately **user-visible result checkpoint** after the Stage 4 rebuild began.

It is **not yet the final global timetable ranking**. It rescored the 50 real timetable candidates already materialized in `TOP50_v3.html` using the current Stage-4 weekly-timetable geometry model.

Included here:
- current confirmed start-time, late-finish, gap, meal, four-period-run, fixed-free-day, and first weekend-attached-day preferences;
- three diagnostic versions of the still-unpriced Friday/weekend shape, solely to test ranking stability;
- a temporary optimistic display value of 0 for the very small unresolved three-period-run penalty.

Not included yet:
- course/professor preference;
- workload/difficulty;
- downstream degree/future-semester effects;
- registration obtainability/fallback strategy;
- mixed-campus travel cost;
- Chapel timing value.

Therefore this answers:

> Among the 50 previously generated real schedules, which **weekly timetable shapes** currently look strongest?

It does not answer the final registration decision yet.

## Main result

The same top 9 order survives all three diagnostic Friday/weekend scenarios. The old v3 rank #4 is now #1 on weekly timetable quality in all three.

| current weekly rank | old v3 rank | low scenario | middle scenario | high scenario |
|---:|---:|---:|---:|---:|
| 1 | 4 | 24.819 | 30.891 | 38.357 |
| 2 | 10 | 22.944 | 29.016 | 36.482 |
| 3 | 16 | 19.194 | 25.266 | 32.732 |
| 4 | 17 | 18.819 | 24.891 | 32.357 |
| 5 | 21 | 17.944 | 24.016 | 31.482 |
| 6 | 22 | 17.944 | 24.016 | 31.482 |
| 7 | 25 | 17.319 | 23.391 | 30.857 |
| 8 | 30 | 16.819 | 22.891 | 30.357 |
| 9 | 33 | 16.498 | 22.570 | 30.036 |
| 10 | 32 | 14.569 | 20.641 | 28.107 |

## #1 current weekly-timetable candidate

Old v3 rank #4:

- `QRM1001-01-00` — 목4,5,6
- `UIC1561-01-00` — 월7,8 / 수7
- `UIC1551-01-00` — 화7 / 목8,9
- `UIC2151-12-00` — 수1,2,3
- `YCE1253-01-00` — 화5,6 / 목4
- `STA2102-05-00` — 월5,6 / 수6
- `YCA1006-02-00` — 화3

Its weekly-timetable rank is **1 / 1 / 1** across the three diagnostic shape scenarios.

## #2

Old v3 rank #10:

- `QRM1001-01-00` — 목4,5,6
- `UIC1561-01-00` — 월7,8 / 수7
- `UIC1551-01-00` — 화7 / 목8,9
- `UIC2151-12-00` — 수1,2,3
- `YCH1605-01-00` — 화4 / 목5,6
- `STA2102-05-00` — 월5,6 / 수6
- `YCA1006-02-00` — 화3

Weekly rank: **2 / 2 / 2**.

## #3

Old v3 rank #16:

- `QRM1001-01-00` — 목4,5,6
- `UIC1561-01-00` — 월7,8 / 수7
- `UIC1551-01-00` — 화7 / 목8,9
- `UIC2151-12-00` — 수1,2,3
- `YCK1998-03-00` — 월7,8 / 수8
- `STA2102-05-00` — 월5,6 / 수6
- `YCA1006-02-00` — 화3

Weekly rank: **3 / 3 / 3**.

## #4

Old v3 rank #17:

- `QRM1001-01-00` — 목4,5,6
- `UIC1561-01-00` — 월7,8 / 수7
- `UIC1551-01-00` — 화7 / 목8,9
- `UIC2151-12-00` — 수1,2,3
- `YCI1901-01-00` — 화8,9 / 목7
- `STA2102-05-00` — 월5,6 / 수6
- `YCA1006-02-00` — 화3

Weekly rank: **4 / 4 / 4**.

## #5

Old v3 rank #21:

- `QRM1001-01-00` — 목4,5,6
- `UIC1561-01-00` — 월7,8 / 수7
- `UIC1551-01-00` — 화7 / 목8,9
- `UIC2151-12-00` — 수1,2,3
- `YCE1253-01-00` — 화5,6 / 목4
- `STA2102-05-00` — 월5,6 / 수6
- `YCA1006-01-00` — 화2

Weekly rank: **5 / 5 / 5**.

## What this tells us already

The old v3 ordering was not simply the current weekly-timetable ordering. The current timetable model strongly favors a repeated backbone among these old finalists:

- `QRM1001-01-00`
- `UIC1561-01-00`
- usually `UIC1551-01-00`
- `UIC2151-12-00`
- `STA2102-05-00`
- Chapel (`YCA1006-02-00` is favored over `-01-00` in the top four)

The main variation near the top is the remaining course (`YCE1253`, `YCH1605`, `YCK1998`, `YCI1901`, etc.). That is exactly where course value, degree consequences, registration feasibility, and professor/workload evidence should now be concentrated.

## Next concrete output

The next milestone is not another general architecture audit. It is a **larger current candidate leaderboard generated from the Stage-4 search itself**, followed by targeted validation of only the courses that survive near the top.
