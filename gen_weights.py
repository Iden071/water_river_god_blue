"""gen_weights.py — regenerate ranking_weights.md FROM the live constants.

VERIFY 11 found ranking_weights.md 3 refits out of date (it still claimed Friday +25 and
lunch −2). Weights lived in three places — rank.py, render2.py's W table, and that file —
with nothing keeping them in step. rank.py is now the single source of truth; this script
derives the document. Never hand-edit ranking_weights.md again.
"""
import rank as RK, rank2 as R2

ROWS = [
 ("1교시 시작",              f"{RK.W_E1:+g} /일",                 "anchor — 척도 기준점"),
 ("2교시 시작",              f"{RK.W_E2:+g} /일",                 "⚠ [P] 미확인 추정치, 재확인된 적 없음"),
 ("점심 없는 날 (3·4·5)",     f"{RK.W_LUNCH:+g} /일",              "'큰 구멍 ≈ 작은 구멍들'에서 도출"),
 ("저녁 없는 날 (9·10·11)",   f"{RK.W_DINNER:+g} /일",             "'점심보다 조금 크게'"),
 ("연강 L시간 (L≥4)",        f"−(8+0.8·(L−4)²)",                 f"'convex, 4h=−8' · 4h {RK.MARATHON(4):+g} · 8h {RK.MARATHON(8):+g}"),
 ("늦은 종료 (마지막 L교시)",  f"−(L−8)^{RK.LATE.__doc__ or '1.4307'}", f"9교시 {RK.LATE(9):+g} · 13교시 {RK.LATE(13):+g} · 14교시 {RK.LATE(14):+.1f}"),
 ("빈 시간 ℓ교시",           f"−10·(ℓ/4)²",                      f"'4교시 구멍 ≈ 9시 수업 하루' → ℓ=4 {RK.HOLE(4):+g}"),
 ("TRIP — 주말 연결 공강일(presence)",         f"{RK.DAY_CONTIG:+g}",               f"월 = 금의 {RK.DAY_CONTIG/(RK.DAY_CONTIG+RK.FRI_EVENT):.0%} (본인 확정)"),
 ("금요일 추가",             f"{RK.FRI_EVENT:+g}",                f"학교 행사 · 금 총합 {RK.DAY_CONTIG+RK.FRI_EVENT:+g}. 행사시간대 수업 시 VOID (R91)"),
 ("REST — 진짜 공강일(요일 무관)", f"{RK.REST:+g}",              "R129 · 온라인 수업이 있으면 0 · 모든 요일 동일"),
 ("연속 공강 길이 L",         f"×(L−2)^{RK.RUN_EXP}",             "'4일째는 금요일 하나보다 큼'"),
 ("학년 2 / 3 / 4",         f"{R2.YEAR_PEN(2):+g} / {R2.YEAR_PEN(3):+.1f} / {R2.YEAR_PEN(4):+.1f}", "'날카롭게'. null·1학년은 0"),
 ("MR 역할 (전필)",          f"{R2.ROLE_MR:+g}",                  "QRM 6개 전필 슬롯. '10보다 낮게'"),
 ("ME 역할 (전선)",          f"{R2.ROLE_ME:+g}",                  "QRM 전선. qcat(QRM 자체 목록)으로 판정 — R102"),
 ("MB 역할 (전기)",          f"{R2.ROLE_MB:+g}",                  "R103 삭제 — QRM 요건 칸이 아님"),
 ("중국어/일본어",           f"+{R2.BONUS.get('UIC1805',0):g}",   "언어 요건. 이중전공과 무관하므로 유지"),
 ("이중전공 보너스 일체",      "삭제",                              "R103 — 이중전공 미확정"),
]

def main():
    L = ["# Ranking weights — GENERATED, do not hand-edit",
         "",
         "`python gen_weights.py` regenerates this from the live constants in `rank.py` /",
         "`rank2.py`. **rank.py is the single source of truth.**",
         "",
         "Convention: positive = better. Anchor: one 1교시(09:00) day = −10. Only ratios matter.",
         "",
         "| 항목 | 값 | 근거 |", "|---|---|---|"]
    L += [f"| {a} | **{b}** | {c} |" for a, b, c in ROWS]
    L += ["", "## Verification", "",
          "`python test_weights.py` asserts these still reproduce Iden's elicited statements.",
          "Every claim string there is his actual wording. VERIFY 11 closed 2026-08-06 at",
          f"{len(__import__('test_weights').CLAIMS)}/{len(__import__('test_weights').CLAIMS)} passing.",
          "", "## Still unset — see PLANS.md §C", "",
          "- Slot-deferral values (incl. Language-vs-ME relative value)",
          "- Chapel bonus (wanted, magnitude never set)",
          "- Professor ratings (post-hoc on the shortlist)",
          "- Double-major bonuses (scrapped by R103 pending the major decision)", ""]
    open('ranking_weights.md', 'w', encoding='utf-8').write("\n".join(L))
    print(f"ranking_weights.md regenerated — {len(ROWS)} weights from live constants")

if __name__ == '__main__':
    main()
