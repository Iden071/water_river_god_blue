# Ranking weights — GENERATED, do not hand-edit

`python gen_weights.py` regenerates this from the live constants in `rank.py` /
`rank2.py`. **rank.py is the single source of truth.**

Convention: positive = better. Anchor: one 1교시(09:00) day = −10. Only ratios matter.

| 항목 | 값 | 근거 |
|---|---|---|
| 1교시 시작 | **-10 /일** | anchor — 척도 기준점 |
| 2교시 시작 | **-5 /일** | ⚠ [P] 미확인 추정치, 재확인된 적 없음 |
| 점심 없는 날 (3·4·5) | **-6 /일** | '큰 구멍 ≈ 작은 구멍들'에서 도출 |
| 저녁 없는 날 (9·10·11) | **-8 /일** | '점심보다 조금 크게' |
| 연강 L시간 (L≥4) | **−(8+0.8·(L−4)²)** | 'convex, 4h=−8' · 4h -8 · 8h -20.8 |
| 늦은 종료 (마지막 L교시) | **−(L−8)^1.4307** | 9교시 -1 · 13교시 -10.0004 · 14교시 -13.0 |
| 빈 시간 ℓ교시 | **−10·(ℓ/4)²** | '4교시 구멍 ≈ 9시 수업 하루' → ℓ=4 -10 |
| TRIP — 주말 연결 공강일(presence) | **+13** | 월 = 금의 75% (본인 확정) |
| 금요일 추가 | **+4.333** | 학교 행사 · 금 총합 +17.333. 행사시간대 수업 시 VOID (R91) |
| REST — 진짜 공강일(요일 무관) | **+7** | R129 · 온라인 수업이 있으면 0 · 모든 요일 동일 |
| 연속 공강 길이 L | **×(L−2)^1.4** | '4일째는 금요일 하나보다 큼' |
| 학년 2 / 3 / 4 | **-4 / -22.6 / -62.4** | '날카롭게'. null·1학년은 0 |
| MR 역할 (전필) | **+8** | QRM 6개 전필 슬롯. '10보다 낮게' |
| ME 역할 (전선) | **+2.29** | QRM 전선. qcat(QRM 자체 목록)으로 판정 — R102 |
| MB 역할 (전기) | **+0** | R103 삭제 — QRM 요건 칸이 아님 |
| 중국어/일본어 | **+0** | 언어 요건. 이중전공과 무관하므로 유지 |
| 이중전공 보너스 일체 | **삭제** | R103 — 이중전공 미확정 |

## Verification

`python test_weights.py` asserts these still reproduce Iden's elicited statements.
Every claim string there is his actual wording. VERIFY 11 closed 2026-08-06 at
23/23 passing.

## Still unset — see PLANS.md §C

- Slot-deferral values (incl. Language-vs-ME relative value)
- Chapel bonus (wanted, magnitude never set)
- Professor ratings (post-hoc on the shortlist)
- Double-major bonuses (scrapped by R103 pending the major decision)
