"""Print a read-only audit of historical catalogue ingestion.

This script does not generate or mutate repository data.  It exists so CI and developers can
see how many historical observations are parsed, have no listed schedule, or retain an
unresolved schedule under the same canonical parser used for current catalogue data.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.history import load_history_file  # noqa: E402
from timetable_optimizer.sections import (  # noqa: E402
    NoListedSchedule,
    ParsedSchedule,
    UnresolvedSchedule,
)


def counts_for_term(catalog):
    parsed = no_time = unresolved_schedule = 0
    campuses = set()
    for section in catalog.sections:
        if section.campus:
            campuses.add(section.campus)
        if isinstance(section.schedule, ParsedSchedule):
            parsed += 1
        elif isinstance(section.schedule, NoListedSchedule):
            no_time += 1
        elif isinstance(section.schedule, UnresolvedSchedule):
            unresolved_schedule += 1
    return parsed, no_time, unresolved_schedule, campuses


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "past_terms.json"
    history = load_history_file(path)

    print("HISTORICAL CANONICAL INGESTION AUDIT")
    print(f"source: {history.source_name}")
    print(f"sha256: {history.source_fingerprint}")
    print()
    print(
        f"{'term':8s} {'rows':>7s} {'physical':>9s} {'obs?':>6s} "
        f"{'phys?':>6s} {'parsed':>7s} {'no-time':>7s} {'sched?':>7s} campuses"
    )

    for historical_term in history.terms:
        catalog = historical_term.catalog
        parsed, no_time, unresolved_schedule, campuses = counts_for_term(catalog)
        unresolved_observations = sum(
            1 for observation in catalog.observations if observation.section is None
        )
        print(
            f"{historical_term.term:8s} "
            f"{len(catalog.observations):7d} "
            f"{len(catalog.physical_sections):9d} "
            f"{unresolved_observations:6d} "
            f"{len(catalog.unresolved_physical_sections):6d} "
            f"{parsed:7d} "
            f"{no_time:7d} "
            f"{unresolved_schedule:7d} "
            f"{','.join(sorted(campuses)) or '—'}"
        )

    total = history.summary()
    print()
    print(
        "TOTAL "
        f"terms={total.term_count} "
        f"rows={total.observation_count} "
        f"physical={total.physical_section_count} "
        f"unresolved_observations={total.unresolved_observation_count} "
        f"unresolved_physical={total.unresolved_physical_count} "
        f"parsed_schedules={total.parsed_schedule_count} "
        f"no_listed_schedule={total.no_listed_schedule_count} "
        f"unresolved_schedule={total.unresolved_schedule_count} "
        f"campuses={','.join(total.campuses) or '—'}"
    )
    if total.delivery_counts:
        print(
            "delivery_segments: "
            + ", ".join(f"{kind}={count}" for kind, count in total.delivery_counts)
        )


if __name__ == "__main__":
    main()
