"""Vetted Fall 2026 preference evidence for the Stage 4 rebuild.

This file is intentionally conservative.  It does not import the legacy ranking
constants as authority.  Instead it re-expresses only preference evidence that
survives the Stage 2/3 audit and current SPEC, preserving intervals, heuristics,
and unresolved dimensions rather than freezing every historical midpoint into
a scalar score.
"""

from __future__ import annotations

from .preferences import (
    PreferenceEstimate,
    PreferenceProfile,
    PreferenceProvenance,
    PreferenceSourceKind,
    PreferenceValue,
)


def _user(source_id: str, description: str) -> PreferenceProvenance:
    return PreferenceProvenance(
        PreferenceSourceKind.USER_INPUT,
        source_id=source_id,
        description=description,
    )


def _derived(source_id: str, description: str, derivation: str) -> PreferenceProvenance:
    return PreferenceProvenance(
        PreferenceSourceKind.DERIVED,
        source_id=source_id,
        description=description,
        derivation=derivation,
    )


def fall2026_preference_profile() -> PreferenceProfile:
    """Return the currently defensible Fall 2026 subjective evidence profile.

    Utility sign convention is positive = better, negative = worse.  The
    historical 09:00-start comparison remains the scale anchor at -10, but
    dimensions whose magnitude was never established remain unmeasured.
    """

    values = (
        PreferenceValue(
            "start_period_1_day",
            PreferenceEstimate.exact(-10.0),
            _user(
                "R-anchor-09-start",
                "One weekday beginning at 09:00 is the historical preference-scale anchor.",
            ),
            "09:00 start day",
        ),
        PreferenceValue(
            "start_period_2_day",
            PreferenceEstimate.exact(-5.0),
            _user(
                "user-confirmed-2026-08-19-period2",
                "User explicitly confirmed a weekday beginning at period 2 (10:00) is worth -5 on the established preference scale, and clarified that the long-standing RULES.md unresolved flag was outdated.",
            ),
            "10:00 start day",
        ),
        PreferenceValue(
            "rest_fixed_free_weekday",
            PreferenceEstimate.bounded(6.0, 8.0),
            _user(
                "R140-rest-bracket",
                "A genuinely fixed-time-free weekday was bracketed between 6 and 8 by comparisons against established anchors.",
            ),
            "True rest weekday",
        ),
        PreferenceValue(
            "weekend_attached_presence_free_day",
            PreferenceEstimate.bounded(12.0, 14.0),
            _derived(
                "R142-trip-from-friday",
                "First weekday added to the weekend-connected no-campus-presence run.",
                "User valued a free Friday at two 09:00 starts (=20) while explicitly separating trip-home value from true rest. Subtracting the preserved rest bracket [6,8] gives trip value [12,14].",
            ),
            "Weekend-attached campus-free day",
        ),
        PreferenceValue(
            "four_fixed_period_run",
            PreferenceEstimate.exact(-8.0),
            _user(
                "R72-four-hour-run",
                "User explicitly retained a four-hour consecutive fixed-time run at -8 on the 09:00-start anchor scale.",
            ),
            "Four-period continuous run",
        ),
        PreferenceValue(
            "late_finish_period_9",
            PreferenceEstimate.exact(-1.0),
            _user(
                "late-finish-17-50",
                "User set a day ending at period 9 (17:50) to -1.",
            ),
            "17:50 finish",
        ),
        PreferenceValue(
            "late_finish_period_13",
            PreferenceEstimate.exact(-10.0),
            _user(
                "late-finish-21-50",
                "User set a day ending at period 13 (21:50) to -10.",
            ),
            "21:50 finish",
        ),
        PreferenceValue(
            "late_finish_period_14",
            PreferenceEstimate.exact(-12.980240898764906),
            _derived(
                "user-recalled-late-finish-curve-2026-08-19",
                "Period-14 (22:50) finish value derived from the already-established late-finish curve recalled and accepted by the user.",
                "Use LatePenalty(p)=-(p-8)^a with anchors period 9=-1 and period 13=-10. These imply a=ln(10)/ln(5)=1.4306765580733933, so period 14 gives -(6^a)=-12.980240898764906.",
            ),
            "22:50 finish",
        ),
        PreferenceValue(
            "dead_gap_quadratic_unit",
            PreferenceEstimate.exact(-0.625),
            _derived(
                "user-confirmed-gap-curve-2026-08-19",
                "User reconfirmed the previously established quadratic dead-gap curve.",
                "GapPenalty(l)=-10*(l/4)^2 = -0.625*l^2. The timetable evaluator supplies l^2 as the quantity for each observed dead gap, so one utility unit is -0.625.",
            ),
            "Quadratic dead-gap unit",
        ),
        PreferenceValue(
            "hard_language_course",
            PreferenceEstimate.heuristic(-10.0),
            _derived(
                "R188-hard-language",
                "A hard language course was described as approximately as costly as one 09:00 start.",
                "Map the approximate comparison to the established -10 anchor, retaining HEURISTIC rather than EXACT status.",
            ),
            "Hard language course",
        ),
        PreferenceValue(
            "missing_lunch",
            PreferenceEstimate.exact(-6.0),
            _user(
                "user-confirmed-2026-08-19-lunch",
                "User explicitly reconfirmed the previously elicited missing-lunch value of -6 on the established preference scale.",
            ),
            "Missing lunch window",
        ),
        PreferenceValue(
            "missing_dinner",
            PreferenceEstimate.exact(-8.0),
            _user(
                "user-confirmed-2026-08-19-dinner",
                "User explicitly reconfirmed the previously elicited missing-dinner value of -8 on the established preference scale.",
            ),
            "Missing dinner window",
        ),
        PreferenceValue(
            "friday_event_window_free",
            PreferenceEstimate.unmeasured(),
            label="Friday event window free",
        ),
        PreferenceValue(
            "weekend_run_curvature",
            PreferenceEstimate.unmeasured(),
            label="Marginal value shape of additional weekend-connected free days",
        ),
        PreferenceValue(
            "course_workload",
            PreferenceEstimate.unmeasured(),
            label="Course workload",
        ),
        PreferenceValue(
            "course_difficulty_general",
            PreferenceEstimate.unmeasured(),
            label="General course difficulty",
        ),
        PreferenceValue(
            "chapel_timing_advantage",
            PreferenceEstimate.unmeasured(),
            label="Timing advantage of completing Chapel now",
        ),
        PreferenceValue(
            "registration_obtainability",
            PreferenceEstimate.unmeasured(),
            label="Registration obtainability",
        ),
        PreferenceValue(
            "mixed_campus_travel_disutility",
            PreferenceEstimate.unmeasured(),
            label="Mixed-campus travel burden",
        ),
        PreferenceValue(
            "target_credit_load_18",
            PreferenceEstimate.unmeasured(),
            label="Preference for an 18-credit academic load",
        ),
    )

    return PreferenceProfile(
        profile_id="fall2026-vetted-stage4c",
        values=values,
        relations=(),
    )
