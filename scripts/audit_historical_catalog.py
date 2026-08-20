"""Print a read-only audit of historical catalogue ingestion.

This script does not generate or mutate repository data.  It exists so CI and developers can
see how many historical observations are parsed, have no listed schedule, or retain an
unresolved schedule under the same canonical parser used for current catalogue data.

It also diagnoses repeated section ids whose source observations disagree.  Those diagnostics
are intentionally observational: they do not choose which fields are intrinsic to a physical
section or silently reconcile conflicts.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import fields
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from timetable_optimizer.catalog import ReconciliationKind  # noqa: E402
from timetable_optimizer.history import load_history_file  # noqa: E402
from timetable_optimizer.sections import (  # noqa: E402
    NoListedSchedule,
    ParsedSchedule,
    Section,
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


def conflict_diagnostics(history):
    field_counts = Counter()
    pattern_counts = Counter()
    pattern_samples = defaultdict(list)
    conflicts_with_unparsed_observation = 0

    section_field_names = [field.name for field in fields(Section)]

    for historical_term in history.terms:
        catalog = historical_term.catalog
        observations_by_id = defaultdict(list)
        for observation in catalog.observations:
            if observation.section_id:
                observations_by_id[observation.section_id].append(observation)

        for record in catalog.physical_sections:
            if record.reconciliation is not ReconciliationKind.CONFLICT:
                continue
            group = observations_by_id[record.section_id]
            sections = [observation.section for observation in group]
            if any(section is None for section in sections):
                conflicts_with_unparsed_observation += 1
                pattern = ("<unparsed observation>",)
            else:
                different = []
                for name in section_field_names:
                    values = [getattr(section, name) for section in sections]
                    if any(value != values[0] for value in values[1:]):
                        different.append(name)
                        field_counts[name] += 1
                pattern = tuple(different) or ("<no Section-field difference>",)

            pattern_counts[pattern] += 1
            if len(pattern_samples[pattern]) < 4:
                pattern_samples[pattern].append(f"{historical_term.term}:{record.section_id}")

    return field_counts, pattern_counts, pattern_samples, conflicts_with_unparsed_observation


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

    field_counts, patterns, samples, unparsed = conflict_diagnostics(history)
    print()
    print("DUPLICATE-SECTION CONFLICT DIAGNOSTICS")
    print(f"conflicts containing an unparsed observation: {unparsed}")
    print(
        "fields differing across conflict groups: "
        + (", ".join(f"{name}={count}" for name, count in field_counts.most_common()) or "none")
    )
    for pattern, count in patterns.most_common(12):
        print(
            f"  {count:4d}  {', '.join(pattern)}"
            f"   samples={'; '.join(samples[pattern])}"
        )


if __name__ == "__main__":
    main()
