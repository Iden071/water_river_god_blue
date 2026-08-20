#!/usr/bin/env python3
"""Print a concrete Stage-4 timetable leaderboard from the existing v3 top-50 candidates.

This is a deliberately limited checkpoint, not a global-optimum claim.  It answers one useful
question now: among the 50 real schedules already materialized by the previous engine, which
weekly timetable shapes look strongest under the current Stage-4 timetable rules?

Known/exact current preference values are used directly.  The two still-unpriced positive
shape families (Friday-event availability and extra weekend-attached free days) are swept over
three archival diagnostic scenarios already present in ``fall_shape_diagnostics``.  Those
scenarios are NOT current preference evidence and are never used for proof pruning.  The
three-period continuous-run term is set to 0 only for this leaderboard, which is optimistic
relative to the user's statement that its true cost is very slight and negative.

Course quality, professor, workload, degree/future consequences, registration risk, travel,
and Chapel timing are intentionally excluded.  The output is therefore a visible timetable-
shape shortlist to guide the real search, not a final registration recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import load_catalog_files
from timetable_optimizer.fall2026_preferences import fall2026_preference_profile
from timetable_optimizer.fall_shape_diagnostics import archived_shape_sensitivity_scenarios
from timetable_optimizer.preferences import EstimateStatus
from timetable_optimizer.timetable_quality import extract_timetable_quality
from timetable_optimizer.timetable_utility import timetable_preference_quantities


ARTICLE_RE = re.compile(r'<article class="c"[^>]*>(.*?)</article>', re.S)
SECTION_RE = re.compile(r'<strong>([A-Z0-9]+-[0-9]{2}-[0-9]{2})</strong>')


@dataclass(frozen=True)
class Candidate:
    old_rank: int
    section_ids: tuple[str, ...]


def parse_old_top50(path: Path, known_ids: set[str]) -> tuple[Candidate, ...]:
    text = path.read_text(encoding="utf-8")
    out: list[Candidate] = []
    for old_rank, article in enumerate(ARTICLE_RE.findall(text), 1):
        ids: list[str] = []
        for section_id in SECTION_RE.findall(article):
            if section_id in known_ids and section_id not in ids:
                ids.append(section_id)
        if ids:
            out.append(Candidate(old_rank, tuple(ids)))
    if not out:
        raise RuntimeError("no candidate cards could be parsed from TOP50_v3.html")
    return tuple(out)


def point_for_dimension(dimension: str, scenario, profile) -> float:
    # Current user statement: a three-period run may be very slightly bad.  Zero is used only
    # as an optimistic display convention here so we do not invent a magnitude.
    if dimension == "three_fixed_period_run":
        return 0.0

    value = profile.value(dimension)
    estimate = value.estimate
    if estimate.status is EstimateStatus.EXACT:
        assert estimate.point is not None
        return estimate.point
    if estimate.status is EstimateStatus.BOUNDED:
        if dimension == "rest_fixed_free_weekday":
            return scenario.rest_value
        if dimension == "weekend_attached_presence_free_day":
            return scenario.first_attached_trip_value
        raise RuntimeError(f"no display-point rule for bounded dimension {dimension}")
    if estimate.status is EstimateStatus.UNMEASURED:
        point = scenario.unresolved_shape_points().get(dimension)
        if point is None:
            raise RuntimeError(f"scenario does not cover active unmeasured dimension {dimension}")
        return point
    raise RuntimeError(f"heuristic timetable dimension unexpectedly active: {dimension}")


def timetable_score(sections, scenario, profile) -> float:
    facts = extract_timetable_quality(tuple(sections))
    quantities = timetable_preference_quantities(facts)
    return sum(
        quantity * point_for_dimension(dimension, scenario, profile)
        for dimension, quantity in quantities.items()
    )


def describe(candidate: Candidate, section_map) -> str:
    lines = []
    for section_id in candidate.section_ids:
        section = section_map[section_id]
        lines.append(
            f"    {section.section_id:<16} {section.course_code:<9} {section.time_text or '[no listed time]'}"
        )
    return "\n".join(lines)


def main() -> None:
    snapshot = load_catalog_files(
        ROOT / "raw_2026F.json",
        program_listings_path=ROOT / "qrm_listings.json",
        listing_program="QRM",
        term="2026F",
    )
    section_map = {section.section_id: section for section in snapshot.sections}
    candidates = parse_old_top50(ROOT / "TOP50_v3.html", set(section_map))
    profile = fall2026_preference_profile()
    scenarios = archived_shape_sensitivity_scenarios()

    rankings: dict[str, list[tuple[float, Candidate]]] = {}
    rank_positions: dict[int, list[int]] = {candidate.old_rank: [] for candidate in candidates}

    for scenario in scenarios:
        scored = [
            (
                timetable_score(
                    [section_map[section_id] for section_id in candidate.section_ids],
                    scenario,
                    profile,
                ),
                candidate,
            )
            for candidate in candidates
        ]
        scored.sort(key=lambda item: (-item[0], item[1].old_rank))
        rankings[scenario.scenario_id] = scored
        for position, (_, candidate) in enumerate(scored, 1):
            rank_positions[candidate.old_rank].append(position)

    consensus = sorted(
        candidates,
        key=lambda candidate: (
            sum(rank_positions[candidate.old_rank]) / len(rank_positions[candidate.old_rank]),
            max(rank_positions[candidate.old_rank]),
            candidate.old_rank,
        ),
    )

    print("STAGE4 VISIBLE LEADERBOARD — EXISTING V3 TOP-50 RESCORED")
    print("WARNING: shortlist checkpoint only; not a global optimum and not a final registration recommendation")
    print("Included: current weekly timetable geometry. Excluded: course/professor/future/registration/travel/Chapel-timing effects.")
    print("Three-period run display cost = 0 only as an optimistic temporary display convention.")
    print(f"Parsed candidate cards: {len(candidates)}")
    print()

    for scenario in scenarios:
        print(f"SCENARIO {scenario.scenario_id}")
        for position, (score, candidate) in enumerate(rankings[scenario.scenario_id][:10], 1):
            print(
                f"  #{position:<2} score={score:8.3f}  old-rank={candidate.old_rank:<2}  sections={','.join(candidate.section_ids)}"
            )
        print()

    print("CONSENSUS TOP 10 BY AVERAGE POSITION ACROSS THE 3 DIAGNOSTIC SCENARIOS")
    for position, candidate in enumerate(consensus[:10], 1):
        positions = rank_positions[candidate.old_rank]
        avg = sum(positions) / len(positions)
        scores = [
            next(score for score, item in rankings[scenario.scenario_id] if item.old_rank == candidate.old_rank)
            for scenario in scenarios
        ]
        print(
            f"\n#{position}  old-rank={candidate.old_rank}  scenario-ranks={positions}  avg-rank={avg:.2f}  timetable-scores={[round(score, 3) for score in scores]}"
        )
        print(describe(candidate, section_map))


if __name__ == "__main__":
    main()
