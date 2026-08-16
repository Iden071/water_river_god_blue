# -*- coding: utf-8 -*-
"""
build_audit_package.py — emit a self-contained package for an independent auditor.

WHY IT IS GENERATED, NOT WRITTEN
--------------------------------
Every serious defect found on 2026-08-09 was a place where PROSE and CODE disagreed, and in
every case the prose was mine and the code was right (or vice versa) with nothing checking.
So this package is **extracted from the source at build time**. If it is stale it is because
someone edited code without re-running it, and the timestamps will say so.

The auditor should treat `RULES.md` as *evidence of what was said*, never as evidence of what
the model *does*. Those came apart four separate times today.

Emits into audit/ :
    AUDIT_BRIEF.md    what to look for, and the failure modes already known
    CONSTANTS.md      every live constant, its value, provenance tag, and source line
    ELICITED.md       every quoted statement by Iden, with rule number, for cross-checking
    OBJECTIVE.md      the scoring function written out term by term
    MANIFEST.md       every file, what it is, and whether it is live or superseded
"""
import os, re, json, csv, subprocess, sys, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'audit')
os.makedirs(OUT, exist_ok=True)

LIVE_CODE = ['rank.py', 'rank2.py', 'rank3.py', 'rank4.py', 'rank4_branch.py',
             'continuation.py', 'plan_model.py', 'difficulty.py', 'risk.py',
             'tiebreak.py', 'defer_value2.py']
VIEWS = ['render_top50.py', 'render_alternatives.py']
TESTS = ['test_weights.py', 'test_retired.py', 'verify_rank4.py']
SWEEPS = ['sweep_difficulty.py', 'sweep_sinchon.py', 'sweep_sinchon_pref.py',
          'sweep_break.py', '_crowd_curve.py']
DATA = ['canonical_2026F.json', 'raw_2026F.json', 'mileage_history.json',
        'crowding.json', 'availability.json', 'elective_items.json',
        'FINAL_ranked4.csv']
SUPERSEDED = ['FINAL_ranked3.csv', 'defer_costs.json', 'risk.json',
              'FINAL_ranked4_narrowlang.csv']


def constants():
    """Every module-level numeric constant in the live code, with its comment context."""
    rows = []
    pat = re.compile(r'^([A-Z][A-Z0-9_]{2,})\s*=\s*(.+?)\s*(?:#(.*))?$')
    for f in LIVE_CODE:
        p = os.path.join(HERE, f)
        if not os.path.exists(p):
            continue
        lines = open(p, encoding='utf-8').read().split('\n')
        for i, ln in enumerate(lines):
            m = pat.match(ln)
            if not m:
                continue
            name, val, cmt = m.group(1), m.group(2), (m.group(3) or '').strip()
            # keep only things an auditor can actually argue with: numbers, and small
            # literal collections of them. Drop paths, comprehensions and derived objects —
            # a noisy inventory costs the auditor more than it gives.
            v = val.strip()
            numeric = re.fullmatch(r"-?\d+(\.\d+)?", v) or \
                      re.fullmatch(r"float\(os\.environ\.get\([^)]*,\s*-?\d+(\.\d+)?\)\)", v) or \
                      re.fullmatch(r"[\{\(\[][^\]\}\)]{0,80}[\]\}\)]", v) or \
                      re.fullmatch(r"-?\d+(\.\d+)?\s*/\s*-?\d+(\.\d+)?", v) or \
                      'lambda' in v
            if not numeric or name in ('HERE', 'OUT'):
                continue
            if len(val) > 90:
                val = val[:87] + '...'
            # provenance: walk UPWARD through the contiguous comment block. A fixed
            # 4-line window missed the tag on every constant with a long rationale — which
            # is precisely the set of constants an auditor most needs tagged correctly.
            j, block = i - 1, []
            while j >= 0 and (lines[j].lstrip().startswith('#') or not lines[j].strip()):
                if lines[j].strip():
                    block.append(lines[j])
                elif block:
                    break
                j -= 1
            ctx = ' '.join(block + [cmt])
            tag = ('[P]' if 'NEVER ELICITED' in ctx or '[P]' in ctx or 'PROVISIONAL' in ctx else
                   '[D]' if '[D]' in ctx or 'DERIVED' in ctx else
                   '[E]' if '[E]' in ctx or 'ELICITED' in ctx or 'Iden' in ctx else
                   '[M]' if '[M]' in ctx or 'MEASURED' in ctx or '수강편람' in ctx or '제도안내' in ctx else
                   '[?]')
            rows.append((f, i + 1, name, val, tag, cmt[:70]))
    return rows


def elicited():
    """Every quoted statement attributed to Iden in RULES.md, with its rule number."""
    s = open(os.path.join(HERE, 'RULES.md'), encoding='utf-8').read()
    out, rule = [], '?'
    for ln in s.split('\n'):
        m = re.match(r'^## (R\d+)\.', ln)
        if m:
            rule = m.group(1)
        for q in re.findall(r'[""“”]([^""“”\n]{20,240})[""“”]', ln):
            out.append((rule, q.strip()))
        m2 = re.match(r'^>\s*\*?(.{20,240})', ln)
        if m2 and 'Iden' not in ln:
            out.append((rule, m2.group(1).strip(' *')))
    # ⛔ F1/F2 (external audit). Two faults, both in this extractor:
    #  · rules with NO quoted text produced ZERO rows, so provenance pointers cited in the
    #    code (R111, R117, R121, R128, R201) did not resolve in the artifact. Worse, R108 —
    #    which REFUTES the auditor's own F5 — was dropped for exactly this reason, and the
    #    auditor could not see the refutation. A lossy view hid its own counter-evidence.
    #  · rule IDs are NOT unique: R86-R91 each head two separate blocks.
    # Fix: emit a row for EVERY rule heading (title as the statement when there is no
    # quote), and mark duplicated IDs.
    heads, dup = [], set()
    _seen_id = set()
    for ln in s.split('\n'):
        m = re.match(r'^## (R\d+)\.\s*(.*)$', ln)
        if m:
            rid, title = m.group(1), m.group(2).strip()
            if rid in _seen_id:
                dup.add(rid)
            _seen_id.add(rid)
            heads.append((rid, title))
    globals()['_DUP_IDS'] = sorted(dup)
    globals()['_N_RULES'] = len(heads)

    seen, ded = set(), []
    for r, q in out:
        # normalise before de-duping: the same sentence appears both bare and quoted,
        # and with markdown emphasis, which defeated a raw prefix key.
        k = re.sub(r'[^0-9A-Za-z가-힣]', '', q).lower()[:60]
        if not k or k in seen:
            continue
        seen.add(k)
        ded.append((r, q.strip(' *\"')))
    # ⛔ THE FALLBACK MUST RUN *AFTER* DE-DUPLICATION. Running it before let a rule whose
    # only quotes duplicated an earlier rule's end up with ZERO rows anyway — which is how
    # R95 and R145 still failed the A3 assertion after the first fix. Caught by the
    # assertion, not by inspection: exactly what the assertion is for.
    covered = {r for r, _ in ded}
    for rid, title in heads:
        if rid not in covered:
            ded.append((rid, f'[no quoted statement — rule title] {title}'))
    ded.sort(key=lambda rq: int(rq[0][1:]))
    return ded


def run(cmd):
    try:
        p = subprocess.run([sys.executable] + cmd, cwd=HERE, capture_output=True,
                           text=True, timeout=200)
        return p.stdout.strip().split('\n')[-6:]
    except Exception as e:
        return [f'(could not run: {e})']


def build():
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    # ---- CONSTANTS.md
    rows = constants()
    tally = collections.Counter(r[4] for r in rows)
    h = [f"# LIVE CONSTANTS — extracted from source at {stamp}\n",
         "Provenance tags are inferred from surrounding comments and may be wrong; the",
         "file:line is authoritative. **Anything tagged `[P]` or `[?]` is where an auditor",
         "should look first.**\n",
         f"Totals: {dict(tally)}\n",
         "| file:line | constant | value | tag | note |", "|---|---|---|---|---|"]
    for f, i, n, v, t, c in sorted(rows, key=lambda r: (r[4] != '[P]', r[4] != '[?]', r[0])):
        h.append(f"| `{f}:{i}` | `{n}` | `{v}` | {t} | {c} |")
    open(os.path.join(OUT, 'CONSTANTS.md'), 'w', encoding='utf-8').write('\n'.join(h))

    # ---- ELICITED.md
    e = elicited()
    h = [f"# EVERY RECORDED STATEMENT BY IDEN — extracted from RULES.md at {stamp}\n",
         "**This is the highest-value artefact in the package.** Five defects on 2026-08-09",
         "were found by noticing that a statement here had no corresponding term in the code.",
         "One *false* defect was found the same way — R202, where the statement says the",
         "factor does **not** matter and the absence of a term was correct.\n",
         "For each line below, the audit question is:",
         "**is this expressed anywhere in the objective, and if not, should it be?**\n",
         f"{len(e)} rows covering {globals().get('_N_RULES', 0)} rule headings.\n",
         (f"⛔ **DUPLICATED RULE IDS — not unique keys:** {globals().get('_DUP_IDS')}. "
          f"`test_retired.py` addresses claims by ID.\n" if globals().get('_DUP_IDS') else ""),
         "⚠️ Rows marked *[no quoted statement]* carry the rule TITLE, because a rule can "
         "be load-bearing without quoting anyone — R108 refutes a whole class of objection "
         "and quotes nobody. An earlier build dropped those and an external auditor was "
         "misled by the omission.\n",
         "| rule | statement |", "|---|---|"]
    for r, q in e:
        qq = q.replace('|', '/')
        h.append(f"| {r} | {qq} |")
    open(os.path.join(OUT, 'ELICITED.md'), 'w', encoding='utf-8').write('\n'.join(h))

    # ---- MANIFEST.md
    def sz(f):
        p = os.path.join(HERE, f)
        return f"{os.path.getsize(p):,}" if os.path.exists(p) else "MISSING"
    h = [f"# MANIFEST — {stamp}\n", "## LIVE — the model", "| file | bytes |", "|---|---|"]
    for f in LIVE_CODE: h.append(f"| `{f}` | {sz(f)} |")
    h += ["\n## VIEWS — derived outputs (4 of today's defects lived here)",
          "| file | bytes |", "|---|---|"]
    for f in VIEWS: h.append(f"| `{f}` | {sz(f)} |")
    h += ["\n## TESTS", "| file | bytes |", "|---|---|"]
    for f in TESTS: h.append(f"| `{f}` | {sz(f)} |")
    h += ["\n## SWEEPS — how unelicited constants were bounded",
          "| file | bytes |", "|---|---|"]
    for f in SWEEPS: h.append(f"| `{f}` | {sz(f)} |")
    h += ["\n## DATA", "| file | bytes |", "|---|---|"]
    for f in DATA: h.append(f"| `{f}` | {sz(f)} |")
    h += ["\n## ⛔ SUPERSEDED — do not read as current",
          "| file | bytes | why |", "|---|---|---|",
          f"| `FINAL_ranked3.csv` | {sz('FINAL_ranked3.csv')} | rank3 output; rank4 replaced it (R182) |",
          f"| `defer_costs.json` | {sz('defer_costs.json')} | R117's fitted table, replaced by continuation.py |",
          f"| `risk.json` | {sz('risk.json')} | superseded by risk.py; read by nothing |",
          f"| `FINAL_ranked4_narrowlang.csv` | {sz('FINAL_ranked4_narrowlang.csv')} | pre-R187 2-course language pool |"]
    open(os.path.join(OUT, 'MANIFEST.md'), 'w', encoding='utf-8').write('\n'.join(h))

    # ---- OBJECTIVE.md
    import continuation, difficulty, rank4, risk, tiebreak
    h = [f"# THE OBJECTIVE, TERM BY TERM — {stamp}\n",
         "```",
         "score(timetable) = week            # fast_score(time mask, presence mask)",
         "                 + Σ year penalty  # EARLY arm only; taken_in_year hardcoded to 1",
         "                 + chapel          # +10 taken / -4.2 not",
         "                 + difficulty      # -D_LANG x tier steps x GPA_GATE_MULT",
         "                 + defer_difficulty# -P(hard) x D_LANG   if Language is deferred",
         "                 + [ V(remainder) - V(reference) ]",
         "",
         "V(remainder) = max over feasible placements into semesters 3-8 of",
         "                 Σ year_gap_pen(semester_year, chart_year)   # BOTH arms live here",
         "               - Σ crowding(low-supply courses in that semester)",
         "               + SINCHON_SEMESTER_VALUE x (number of 신촌 semesters)",
         "  subject to: campus · term · <=6 courses · <=1 chapel · >=1 국제 Spring (QRM3003)",
         "            · Korean ME cap (<=4 at 신촌) · the 72-point mileage budget",
         "  = -infinity if no feasible placement exists",
         "```\n",
         "## The numbers that carry the most weight, and their status\n",
         "| constant | value | status |", "|---|---|---|",
         f"| `D_LANG` | {difficulty.D_LANG} | **[E]** elicited (R188) — landed ON a switching threshold |",
         f"| `SINCHON_SEMESTER_VALUE` | {continuation.SINCHON_SEMESTER_VALUE} | **[E]** confirmed (R201). Robust: any value >= 40 gives the same answer |",
         f"| `SINCHON_PER_COURSE` | {continuation.SINCHON_PER_COURSE} | ⚠️ **[D] DERIVED** by equating a commuting hour with a dead campus hour. **The single load-bearing assumption under #1.** Bracket [12,22] |",
         f"| `GPA_GATE_MULT` | {difficulty.GPA_GATE_MULT} | **[P]** never elicited; 1.0 = inert |",
         f"| `KOREAN_ME_COURSE_CAP` | {continuation.KOREAN_ME_COURSE_CAP} | **[M]** QRM graduation table |",
         f"| `MILEAGE_BUDGET` | {risk.MILEAGE_BUDGET} | **[M]** 제도안내 |",
         f"| `ALLOWANCE` (tie-break ⓗ) | {tiebreak.ALLOWANCE} | **[M]** 수강편람; corrects R86's 19 |",
         "\n## ⚠️ Known to be a proxy",
         "The crowding curve is measured on the **Fall 2026 국제** catalogue and applied to",
         "신촌 semesters in 2029. Right instrument, wrong population (G-9).\n"]
    open(os.path.join(OUT, 'OBJECTIVE.md'), 'w', encoding='utf-8').write('\n'.join(h))
    print(f"wrote audit/ — CONSTANTS ({len(rows)}), ELICITED ({len(e)}), MANIFEST, OBJECTIVE")


if __name__ == '__main__':
    build()
