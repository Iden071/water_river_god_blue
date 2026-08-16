# -*- coding: utf-8 -*-
"""
prof.py — the professor axis.  Iden, 2026-08-16:

  "prof evaluation, has to be done by hand. Not all profs, that would be impossible. Just
   profs that appear in the top 50, plus profs that appear 'frequently' in the top 5000.
   For other profs, just in case we have a better option, give two versions of keeping them
   at 0 (or the default), and then keeping them at the max score so we can visually see
   what changes."

THE CARRIER — same shape as difficulty.py (R137: never ask for 700 per-course ratings)
--------------------------------------------------------------------------------------
Ratings are per PROFESSOR, hand-entered, on [-1, +1] with 0 = neutral/unknown:

    +1  would actively choose this course because of them
     0  neutral, or not yet rated
    -1  would actively avoid

The weight `PROF_W` converts a rating into schedule points. It has NEVER been elicited —
default 10.0, i.e. a +1 professor is worth exactly one 9:00 start (MODEL.md §0 anchor),
which is deliberately a placeholder magnitude and not a measurement. Sweep it before
believing any margin it produces. Same discipline as D_LANG before R188.

⚠️ THE UNRATED DEFAULT IS THE WHOLE POINT OF THIS FILE
`UNRATED` is what an unrated professor scores. Two runs bracket the answer:

    UNRATED = 0.0   pessimistic-neutral: unrated profs add nothing
    UNRATED = 1.0   optimistic:          every unrated prof is as good as the best

If the ranking is the same under both, no unrated professor can change the decision and the
hand-rating work is complete. If it differs, the diff names exactly which professors are
worth rating next — it is a targeting tool, not a scoring trick.

WHY NOT JUST RESCORE THE TOP 50
Because a section that only wins once its professor is credited need not be in the top 50 to
begin with. `sweep_difficulty.py` made that mistake (rescored a fixed candidate set) and is
retired for it; R250 records the same failure in cache form. This module therefore feeds
`research_v3.py`'s SEARCH, not a post-hoc pass.

FILES
  prof_ratings.csv   name,rating,note   — hand-filled. Missing rows score `UNRATED`.
"""
import csv, json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

# [P] NEVER ELICITED. One 9:00 start = 10 (MODEL.md §0). Placeholder magnitude.
PROF_W = float(os.environ.get('PROF_W', 10.0))
# what an UNRATED professor scores, in rating units. 0.0 = neutral, 1.0 = best-possible.
UNRATED = float(os.environ.get('PROF_UNRATED', 0.0))

SHEET = P('prof_ratings.csv')

_RAW = None
_RATINGS = None


def _raw():
    global _RAW
    if _RAW is None:
        r = json.load(open(P('raw_2026F.json'), encoding='utf-8'))
        r = r if isinstance(r, list) else list(r.values())[0]
        _RAW = {f"{x.get('subjtnb')}-{x.get('corseDvclsNo')}-{x.get('prctsCorseDvclsNo')}": x
                for x in r}
    return _RAW


def prof_of(sid):
    """Professor name for a section id. '(none)' for the 12 catalogue rows with no name."""
    r = _raw().get(sid)
    return (str((r or {}).get('cgprfNm') or '').strip() or '(none)')


def ratings():
    """{professor: rating in [-1,+1]}. Absent = unrated (scores UNRATED)."""
    global _RATINGS
    if _RATINGS is None:
        d = {}
        if os.path.exists(SHEET):
            with open(SHEET, encoding='utf-8-sig') as fh:
                for row in csv.DictReader(fh):
                    nm = (row.get('name') or '').strip()
                    val = (row.get('rating') or '').strip()
                    if nm and val:
                        try:
                            d[nm] = max(-1.0, min(1.0, float(val)))
                        except ValueError:
                            pass
        _RATINGS = d
    return _RATINGS


def rating_of(sid):
    return ratings().get(prof_of(sid), UNRATED)


def bonus(sid):
    """Schedule points contributed by this section's professor."""
    return PROF_W * rating_of(sid)


def reset():
    """Re-read the sheet and the env knobs (used by the 0-vs-max comparison)."""
    global _RATINGS
    _RATINGS = None
    _PERSIST.clear()


# ---------------------------------------------------------------------------
# R281 — DEFERRING A COURSE DOES NOT ESCAPE ITS PROFESSOR
# ---------------------------------------------------------------------------
# `bonus()` is charged in the semester the course is TAKEN. `kdefer` carried no professor
# term, so a deferral branch dodged the penalty permanently — a bad professor on a
# single-section requirement bought exactly PROF_W points toward postponing it, even though
# you meet the same person next year.
#
# This is the bug `difficulty.p_hard_if_deferred()` already fixes for the language tier
# (it charges P(hard | deferred) x D_LANG ON the deferral branch). Same shape here:
#
#     carry(requirement) = P(same professor when you take it) x E[bonus of that section]
#
# and `kdefer` subtracts it, so the term CANCELS when persistence is 1.0 — which is the
# correct behaviour: if the professor never changes, when you take the course is irrelevant
# to who teaches it, and the rating must not move the deferral decision at all.
#
# P(same professor) is MEASURED, not assumed: consecutive same-season terms in
# `past_terms.json`, asking whether the course kept at least one of its professors.
# Overall 83.7% (2098/2508). Per requirement: WCiv 4/4, SciRD 4/4, Lang 8/8, LHP 11/12,
# MR 2/4.
_PERSIST = {}


def persistence(codes):
    """P(a course keeps at least one professor year-over-year), measured. None if unobserved."""
    key = tuple(sorted(codes))
    if key in _PERSIST:
        return _PERSIST[key]
    import collections
    import pools_past as PP
    byterm = collections.defaultdict(dict)
    for lab, rs in PP.terms().items():
        for r in rs:
            c = str(r.get('subjtnb') or '')
            p = str(r.get('cgprfNm') or '').strip()
            if c in set(codes) and p:
                byterm[lab].setdefault(c, set()).add(p)
    tot = same = 0
    for a, b in (('2024-2', '2025-2'), ('2025-2', '2026-2'),
                 ('2024-1', '2025-1'), ('2025-1', '2026-1')):
        for c in codes:
            if c in byterm.get(a, {}) and c in byterm.get(b, {}):
                tot += 1
                if byterm[a][c] & byterm[b][c]:
                    same += 1
    _PERSIST[key] = (same / tot) if tot else None
    return _PERSIST[key]


# fallback when a requirement was never observed in two consecutive same-season terms.
# The measured overall rate; NOT a guess — 2098/2508 across the whole catalogue.
PERSIST_DEFAULT = 0.837


def carry(codes, sections):
    """Professor bonus still owed when this requirement is eventually taken.

    `sections` are the current-catalogue section ids for the requirement. You choose among
    them, so the expectation is over the best you would plausibly take — mirroring how
    `kdefer` treats geometry. With one section (WCiv) it is simply that professor's bonus.
    """
    if not sections:
        return 0.0
    p = persistence(codes)
    if p is None:
        p = PERSIST_DEFAULT
    return p * max(bonus(s) for s in sections)


# ---------------------------------------------------------------------------
# the shortlist: who is actually worth rating by hand
# ---------------------------------------------------------------------------
def ranked_rows(state='_v3_parts_f2'):
    """Every ranked candidate with its cross-branch total, best first."""
    import glob
    import fallback as FB
    out = []
    for fp in glob.glob(os.path.join(HERE, state, 'part_*.json')):
        try:
            blob = json.load(open(fp, encoding='utf-8'))
        except Exception:
            continue
        b = blob.get('branch')
        for r in blob.get('rows', []):
            v = FB.total(r, b)
            if v is not None:
                out.append((v, b, r))
    out.sort(key=lambda t: -t[0])
    return out


def sections_of(r):
    return ((r.get('requirements') or []) + (r.get('electives') or [])
            + ([r['chapel']] if r.get('chapel', '-') != '-' else []))


def shortlist(top_n=50, freq_n=5000, freq_thresh=0.05, rows=None):
    """(list of (prof, in_top50, share_of_top5000), counters) — Iden's two criteria."""
    rows = rows if rows is not None else ranked_rows()
    c50 = collections.Counter()
    cN = collections.Counter()
    for v, b, r in rows[:top_n]:
        for s in set(sections_of(r)):
            c50[prof_of(s)] += 1
    n = len(rows[:freq_n])
    for v, b, r in rows[:freq_n]:
        for s in set(sections_of(r)):
            cN[prof_of(s)] += 1
    keep = set(c50) | {p for p, k in cN.items() if n and k / n >= freq_thresh}
    keep.discard('(none)')
    out = [(p, c50.get(p, 0), (cN.get(p, 0) / n) if n else 0.0) for p in keep]
    out.sort(key=lambda t: (-t[1], -t[2], t[0]))
    return out, c50, cN


def write_sheet(top_n=50, freq_n=5000, freq_thresh=0.05, path=None):
    """Create/extend prof_ratings.csv without destroying ratings already entered."""
    path = path or SHEET
    have = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8-sig') as fh:
            for row in csv.DictReader(fh):
                nm = (row.get('name') or '').strip()
                if nm:
                    have[nm] = (row.get('rating', ''), row.get('note', ''))
    sl, c50, cN = shortlist(top_n, freq_n, freq_thresh)
    rows_out = []
    for p, in50, share in sl:
        rating, note = have.get(p, ('', ''))
        rows_out.append({'name': p, 'rating': rating,
                         'in_top50': in50, 'share_top5000': f'{share:.3f}',
                         'courses': '; '.join(sorted(courses_of(p))[:4]), 'note': note})
    with open(path, 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['name', 'rating', 'in_top50', 'share_top5000',
                                           'courses', 'note'])
        w.writeheader()
        w.writerows(rows_out)
    return path, len(rows_out), sum(1 for r in rows_out if r['rating'])


_BYPROF = None


def courses_of(p):
    global _BYPROF
    if _BYPROF is None:
        _BYPROF = collections.defaultdict(set)
        for sid, r in _raw().items():
            nm = (str(r.get('cgprfNm') or '').strip() or '(none)')
            _BYPROF[nm].add(f"{r.get('subjtnb')} {str(r.get('subjtNm') or '')[:24]}")
    return _BYPROF.get(p, set())


if __name__ == '__main__':
    sl, c50, cN = shortlist()
    print(f"PROF_W = {PROF_W}  (never elicited — one 9:00 start = 10)")
    print(f"UNRATED = {UNRATED}\n")
    print(f"{len(sl)} professors worth rating by hand "
          f"(in the top 50, or in >=5% of the top 5000)\n")
    print(f"  {'prof':14s} {'top50':>6s} {'top5000':>8s}  courses")
    for p, in50, share in sl:
        print(f"  {p:14s} {in50:6d} {share*100:7.1f}%  "
              f"{'; '.join(sorted(courses_of(p))[:2])}")
    path, n, done = write_sheet()
    print(f"\nwrote {os.path.basename(path)} — {n} rows, {done} already rated")
    print("Fill the `rating` column: +1 actively want, 0 neutral, -1 actively avoid.")
