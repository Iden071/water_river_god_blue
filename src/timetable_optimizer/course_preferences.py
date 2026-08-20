"""Course-level subjective evidence for Stage 4C.

This layer is intentionally *not* a course scorer.  It preserves manual user inputs and
missing information without converting them into timetable utility unless a conversion has
actually been established.

The legacy professor model used a hand-entered rating on [-1,+1], then multiplied it by
``PROF_W = 10``.  Its own documentation says that 10-point conversion was never elicited.
Stage 4 therefore preserves the rating itself but does not carry that multiplier forward.

Likewise, an explicit professor rating of ``0`` is different from a blank/unrated row.
Unknown workload, difficulty, and subject interest remain unmeasured rather than receiving
zero utility by default.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from io import StringIO
from math import isfinite
from typing import Mapping

from .preferences import PreferenceEstimate, PreferenceValue
from .sections import Section


class CoursePreferenceError(ValueError):
    """Course-level preference evidence violates the Stage 4 contract."""


class ProfessorRatingStatus(str, Enum):
    """Whether a professor's manual rating is actually known."""

    RATED = "rated"
    LISTED_UNRATED = "listed_unrated"
    NOT_LISTED = "not_listed"
    NO_PROFESSOR_LISTED = "no_professor_listed"


@dataclass(frozen=True)
class ProfessorRatingRecord:
    """One row from the manual professor-rating sheet.

    ``rating=None`` means the row exists but has not been rated yet.  An explicit ``0.0``
    is a genuine neutral rating and must never be conflated with ``None``.
    """

    name: str
    rating: float | None
    source_id: str
    note: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise CoursePreferenceError("professor rating record requires a nonblank name")
        if not self.source_id.strip():
            raise CoursePreferenceError("professor rating record requires a source_id")
        if self.rating is not None:
            if not isfinite(self.rating):
                raise CoursePreferenceError("professor rating must be finite")
            if not -1.0 <= self.rating <= 1.0:
                raise CoursePreferenceError(
                    "manual professor rating must lie in [-1, +1]; do not clamp silently"
                )

    @property
    def status(self) -> ProfessorRatingStatus:
        return (
            ProfessorRatingStatus.RATED
            if self.rating is not None
            else ProfessorRatingStatus.LISTED_UNRATED
        )


@dataclass(frozen=True)
class ProfessorRatingLookup:
    """Result of looking up one section's listed professor."""

    professor: str
    status: ProfessorRatingStatus
    rating: float | None = None
    source_id: str | None = None
    note: str = ""

    @property
    def is_rated(self) -> bool:
        return self.status is ProfessorRatingStatus.RATED


@dataclass(frozen=True)
class ProfessorRatingBook:
    """Validated manual professor ratings with explicit unrated state."""

    records: tuple[ProfessorRatingRecord, ...]

    def __post_init__(self) -> None:
        names = [record.name for record in self.records]
        if len(names) != len(set(names)):
            raise CoursePreferenceError(
                "professor rating sheet contains duplicate professor names"
            )

    def lookup(self, professor: str) -> ProfessorRatingLookup:
        name = str(professor or "").strip()
        if not name:
            return ProfessorRatingLookup(
                professor="",
                status=ProfessorRatingStatus.NO_PROFESSOR_LISTED,
            )

        hits = [record for record in self.records if record.name == name]
        if not hits:
            return ProfessorRatingLookup(
                professor=name,
                status=ProfessorRatingStatus.NOT_LISTED,
            )

        record = hits[0]
        return ProfessorRatingLookup(
            professor=name,
            status=record.status,
            rating=record.rating,
            source_id=record.source_id,
            note=record.note,
        )

    @property
    def rated_names(self) -> frozenset[str]:
        return frozenset(record.name for record in self.records if record.rating is not None)

    @property
    def listed_unrated_names(self) -> frozenset[str]:
        return frozenset(record.name for record in self.records if record.rating is None)


def parse_professor_ratings_csv(
    text: str,
    *,
    source_id: str = "prof_ratings.csv",
) -> ProfessorRatingBook:
    """Parse the manual professor sheet without coercing bad/missing values.

    Auxiliary shortlist columns (``in_top50``, ``share_top5000``, ``courses``) are accepted
    but deliberately ignored as preference evidence.  They describe why a professor was
    selected for rating, not how desirable that professor is.
    """

    if not source_id.strip():
        raise CoursePreferenceError("professor rating source_id must be nonblank")

    clean = text.lstrip("\ufeff")
    reader = csv.DictReader(StringIO(clean))
    if reader.fieldnames is None or "name" not in reader.fieldnames or "rating" not in reader.fieldnames:
        raise CoursePreferenceError("professor rating CSV requires name and rating columns")

    records: list[ProfessorRatingRecord] = []
    seen: set[str] = set()
    for row_number, row in enumerate(reader, start=2):
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        if name in seen:
            raise CoursePreferenceError(
                f"duplicate professor {name!r} in rating sheet at row {row_number}"
            )
        seen.add(name)

        raw_rating = str(row.get("rating") or "").strip()
        rating: float | None
        if not raw_rating:
            rating = None
        else:
            try:
                rating = float(raw_rating)
            except ValueError as exc:
                raise CoursePreferenceError(
                    f"invalid professor rating {raw_rating!r} for {name!r}"
                ) from exc

        records.append(
            ProfessorRatingRecord(
                name=name,
                rating=rating,
                source_id=f"{source_id}:{row_number}:{name}",
                note=str(row.get("note") or "").strip(),
            )
        )

    return ProfessorRatingBook(tuple(records))


def _unmeasured(dimension_id: str, label: str) -> PreferenceValue:
    return PreferenceValue(
        dimension_id=dimension_id,
        estimate=PreferenceEstimate.unmeasured(),
        label=label,
    )


@dataclass(frozen=True)
class SectionCoursePreferenceEvidence:
    """Course-level preference evidence attached to one concrete section."""

    section_id: str
    course_code: str
    professor: ProfessorRatingLookup
    subject_interest: PreferenceValue
    workload_utility: PreferenceValue
    difficulty_utility: PreferenceValue

    @property
    def unresolved_dimensions(self) -> frozenset[str]:
        unresolved: set[str] = set()
        if not self.professor.is_rated:
            unresolved.add("professor_rating")
        if self.subject_interest.estimate.status.value == "unmeasured":
            unresolved.add("subject_interest")
        if self.workload_utility.estimate.status.value == "unmeasured":
            unresolved.add("workload")
        if self.difficulty_utility.estimate.status.value == "unmeasured":
            unresolved.add("difficulty")
        # Even a known [-1,+1] professor rating has no defensible conversion to the
        # timetable utility scale yet.  Keep that missing conversion visible.
        unresolved.add("professor_rating_to_utility")
        return frozenset(unresolved)


def assess_section_course_preferences(
    section: Section,
    professor_ratings: ProfessorRatingBook,
    *,
    subject_interest: Mapping[str, PreferenceValue] | None = None,
    workload_utility: Mapping[str, PreferenceValue] | None = None,
    difficulty_utility: Mapping[str, PreferenceValue] | None = None,
) -> SectionCoursePreferenceEvidence:
    """Attach manual course evidence without inventing missing values.

    Per-course mappings are keyed by course code.  They are optional because Stage 4 must
    be able to represent a perfectly valid candidate whose burden/interest has not yet been
    measured.  No title-based or reputation-based inference is performed here.
    """

    code = section.course_code
    subject_interest = subject_interest or {}
    workload_utility = workload_utility or {}
    difficulty_utility = difficulty_utility or {}

    return SectionCoursePreferenceEvidence(
        section_id=section.section_id,
        course_code=code,
        professor=professor_ratings.lookup(section.professor),
        subject_interest=subject_interest.get(
            code,
            _unmeasured(f"subject_interest::{code}", f"Subject interest for {code}"),
        ),
        workload_utility=workload_utility.get(
            code,
            _unmeasured(f"workload_utility::{code}", f"Workload utility for {code}"),
        ),
        difficulty_utility=difficulty_utility.get(
            code,
            _unmeasured(f"difficulty_utility::{code}", f"Difficulty utility for {code}"),
        ),
    )
