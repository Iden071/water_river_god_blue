# -*- coding: utf-8 -*-
"""
test_partition.py — the assertions that would have caught red-team reply #2.

WHY THIS FILE EXISTS (R306)
`test_v3.py` asserts nothing about the parser, the cost table, or the cache keys. R49 was
reintroduced twice across three modules; R250 has now recurred three times (`_v3` branch
cache, `fetch_mileage` resume cache, `_future_cache`), each time in a file no test looks at.
Findings F1–F5 were all invisible to the suite.

DESIGN CONSTRAINT: this must run against a PARTIAL cost table, because its main job is to
guard a 24–40 h rebuild. Every table test is therefore an invariant over whatever cells exist,
never a completeness count — except T7, which only fires once the table claims to be done.

RUN:  python test_partition.py            # all
      python test_partition.py -k cache   # substring filter
Exit code is the number of failures.
"""
import io, json, os, sys, contextlib, itertools, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

with contextlib.redirect_stdout(io.StringIO()):      # these modules are chatty on import
    import partition as PT
    import partition_solve as PS
    import plan_model as PM

FAILS = []


def _bits(mask):
    """(day, period) pairs out of a time mask. parse() returns a mask, seg_blocks returns
    pairs — comparing them requires saying so out loud."""
    return {(d_, p_) for d_ in range(7) for p_ in range(1, 16)
            if (mask >> (d_ * 16 + p_)) & 1}


def check(name, cond, detail=''):
    (print(f'  ok   {name}') if cond else
     (FAILS.append(name), print(f'  FAIL {name}\n         {detail}')))


def table():
    return json.load(open(P('partition.json'), encoding='utf-8'))


# ---------------------------------------------------------------- T1  (red-team F3)
def t1_no_ok_without_value():
    """An 'OK' cell with no value is indistinguishable from IMPOSSIBLE to the solver.

    That conflation is precisely what R288 exists to prevent, and it is how 72 cells with
    real placements — measured up to 29.498, against a 5.325 branch margin — were silently
    dropped from the DP. A cell that could not be measured must say so in its verdict.
    """
    bad = [k for k, v in table()['cost'].items() if v[2] == 'OK' and v[0] is None]
    check('T1 no cell is OK-with-no-value', not bad,
          f'{len(bad)} cells, e.g. {bad[:3]}')


def t2_never_measured_is_never_exact():
    """`best_exact` was initialised True and left untouched when no product was evaluated,
    so cells that were never measured at all were stamped `exact`. A value of None can never
    be exact."""
    bad = [k for k, v in table()['cost'].items() if v[0] is None and v[1] is True
           and v[2] == 'OK']
    check('T2 unvalued cells are not stamped exact', not bad, f'{len(bad)} cells: {bad[:3]}')


def t3_no_cell_beats_its_own_baseline():
    """R291's invariant. A semester CARRYING obligations cannot score better than the same
    semester carrying nothing; if it does, the obligation is not consuming what it should.
    This is the check that caught the chapel slot bug."""
    d = table()
    bad = []
    for k, v in d['cost'].items():
        if v[0] is None:
            continue
        camp, sea, _ = k.split('|', 2)
        base = (d['base'].get(f'{camp}|{sea}') or [None])[0]
        if base is not None and v[0] > base + 1e-6:
            bad.append((k, v[0], base))
    check('T3 no valued cell exceeds its baseline', not bad, f'{bad[:3]}')


# ---------------------------------------------------------------- T4  (red-team F2 / R250)
def t4_cache_key_separates_bonus_and_table():
    """The third recurrence of R250. `_future_cache.json` was keyed on the remainder alone
    and shared by three programs running at two different bonuses — the verdict read the
    renderer's 30.0 values while itself running at 0.0, a 150-point error. A cached future is
    only comparable to another under the SAME bonus and the SAME cost table."""
    d = table()
    rem = {'Chapel': 2, 'ME': 3}
    old = PS.SINCHON_BONUS
    try:
        PS.SINCHON_BONUS = 0.0
        k0 = PS.cache_key(rem, d)
        PS.SINCHON_BONUS = 30.0
        k30 = PS.cache_key(rem, d)
    finally:
        PS.SINCHON_BONUS = old
    check('T4a bonus is in the cache key', k0 != k30, 'same key at bonus 0 and 30')

    d2 = json.loads(json.dumps(d))
    d2['cost']['국제|S|__probe__'] = [1.0, True, 'OK', 0.0]
    check('T4b table identity is in the cache key',
          PS.cache_key(rem, d) != PS.cache_key(rem, d2),
          'key unchanged after the cost table changed')


def t5_no_consumer_rolls_its_own_key():
    """Every consumer must go through PS.cache_key. The bug was three hand-rolled copies of
    `tuple(sorted(rem.items()))`, two of which were right about the bonus and one of which
    was not."""
    bad = []
    for f in ('render_v3_top50.py', 'partition_clickorder.py', 'partition_verdict.py'):
        src = open(P(f), encoding='utf-8').read()
        if 'cache_key' not in src:
            bad.append(f'{f}: never calls PS.cache_key')
        for ln, line in enumerate(src.splitlines(), 1):
            if 'tuple(sorted(rem.items()))' in line and not line.lstrip().startswith('#'):
                bad.append(f'{f}:{ln} hand-rolled key')
    check('T5 all three consumers use the shared key', not bad, '; '.join(bad))


def t6_consumers_agree_on_the_bonus():
    """partition_verdict never set SINCHON_BONUS and silently ran at the 0.0 default while
    its two peers ran at 30.0."""
    bad = [f for f in ('render_v3_top50.py', 'partition_clickorder.py', 'partition_verdict.py')
           if 'SINCHON_BONUS' not in open(P(f), encoding='utf-8').read()]
    check('T6 every consumer sets SINCHON_BONUS explicitly', not bad, f'silent: {bad}')


# ---------------------------------------------------------------- T7  (red-team F4)
def t7_weekend_option_makes_an_item_free():
    """A weekend section costs nothing, pins nothing and consumes no academic slot, so it
    weakly dominates every weekday alternative. The builder used to take the free option only
    when NO weekday option remained — inverting `geoms()`'s own "you choose your section"
    semantics and over-charging 신촌 chapel ~6.1/semester on the 신촌 side of a campus
    comparison whose entire margin is a hand-set bonus."""
    d = table()
    bad = []
    for camp, sea in (('국제', 'S'), ('국제', 'F'), ('신촌', 'S'), ('신촌', 'F')):
        gg = PT.geoms(PM.codes_for('Chapel', camp, sea), camp, sea)
        if not gg:
            continue
        wk = [g for g in gg.values()
              if any((g[0] >> (dd * 16 + pp)) & 1 for dd in range(5) for pp in range(1, 15))]
        if len(wk) == len(gg):
            continue                      # no weekend option here; nothing to assert
        cell = d['cost'].get(f'{camp}|{sea}|Chapel')
        base = (d['base'].get(f'{camp}|{sea}') or [None])[0]
        if cell and cell[0] is not None and base is not None and abs(cell[0] - base) > 1e-6:
            bad.append(f'{camp}{sea} chapel {cell[0]} != base {base}')
    check('T7 items with a weekend option are charged nothing', not bad, '; '.join(bad))


# ---------------------------------------------------------------- T8  (red-team F1)
def t8_corrupt_table_refuses_to_load():
    """load() used to swallow the decode error and return an EMPTY table, so one interrupted
    write silently wiped the file and the builder rebuilt from scratch — invisible to
    build_sinchon's stall guard, which only watches whether the entry count moves."""
    real = PT.OUT
    tmp = tempfile.mkdtemp()
    probe = os.path.join(tmp, 'partition.json')
    open(probe, 'w').write('{"base": {}, "cost": {"a": [1,')      # truncated
    try:
        PT.OUT = probe
        try:
            PT.load()
            ok, why = False, 'load() returned instead of refusing'
        except SystemExit:
            ok, why = True, ''
        except Exception as e:
            ok, why = False, f'raised {type(e).__name__}, expected SystemExit'
    finally:
        PT.OUT = real
    check('T8 corrupt table refuses to load', ok, why)


def t9_save_is_atomic():
    """A whole-file rewrite executed once per entry, hundreds of times a run, is a wipe
    waiting for an interrupt. save() must land via a rename, not a truncating open()."""
    src = open(P('partition.py'), encoding='utf-8').read()
    i = src.find('def save(')
    body = src[i:i + 600]
    check('T9 save() lands atomically via os.replace', 'os.replace' in body,
          'save() still rewrites the target in place')


# ---------------------------------------------------------------- T10  (R264)
def t10_parsers_agree():
    """R264: pools_past.parse split on commas, so '월3,4,수3(수4)' yielded the token
    '수3(수4)', and '화1,2,목1(목2)' FABRICATED hour 목12. 25.4% of sections were affected.
    Both parsers now delegate to seg_blocks; this asserts they have not drifted apart."""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            import pools_past as PP, build_canonical as BC
    except Exception as e:
        return check('T10 parser agreement', False, f'import failed: {e}')
    adversarial = ['월3,4,수3(수4)', '화1,2,목1(목2)', '수6,7(수8,9)', '금7(금8,9,10,11)',
                   '(화3,4)/목3,4', '화3(화4)/목3,4', '월16', '월0', '토1,2', '일3']
    bad = []
    for s in adversarial:
        try:
            # parse() returns a MASK; seg_blocks returns {(day, period)} for ONE segment.
            a = sorted(_bits(PP.parse(s)))
            b = set()
            for seg in s.split('/'):
                b |= {(d_, p_) for d_, p_ in BC.seg_blocks(seg) if 1 <= p_ <= 15}
            b = sorted(b)
        except Exception as e:
            bad.append(f'{s}: {type(e).__name__}: {e}'); continue
        if a != b:
            bad.append(f'{s}: pools_past {a} != seg_blocks {b}')
    check('T10 parsers agree on the adversarial set', not bad, '; '.join(bad[:3]))


def t11_no_fabricated_hours():
    """The specific R264 symptom: a digit-join across a comma produced hour 12 out of
    '목1(목2)'. Every parsed period must be a real 1–15 slot."""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            import pools_past as PP
    except Exception as e:
        return check('T11 no fabricated hours', False, str(e))
    bad = []
    for s in ('화1,2,목1(목2)', '월3,4,수3(수4)', '금7(금8,9,10,11)'):
        for d_, p_ in _bits(PP.parse(s)):
            if not (0 <= d_ <= 6 and 1 <= p_ <= 15):
                bad.append(f'{s} -> day {d_} period {p_}')
    # the exact R264 symptom: 목12 fabricated by joining digits across a comma
    if (3, 12) in _bits(PP.parse('화1,2,목1(목2)')):
        bad.append('화1,2,목1(목2) still fabricates 목12')
    check('T11 no parsed period falls outside 1-15', not bad, '; '.join(bad))


# ---------------------------------------------------------------- T12
def t12_availability_is_a_whitelist():
    """availability() gained a fourth verdict (STALE, R298). Both consumers must accept only
    'OK' rather than enumerating the verdicts they know, so a fifth one cannot slip through
    the wrong branch."""
    bad = []
    for f, pat in (('partition.py', "if av != 'OK'"),
                   ('partition_solve.py', "!= 'OK'")):
        if pat not in open(P(f), encoding='utf-8').read():
            bad.append(f'{f}: no whitelist test found')
    check('T12 availability is filtered by whitelist', not bad, '; '.join(bad))


def t13_table_matches_current_availability():
    """Cells are cached across sessions but availability() changes (R298/R299 moved
    ECO2102|국제|F to STALE). A cell holding a real value for a placement the current rules
    forbid is a trap for any consumer that reads the table without re-checking."""
    bad = []
    for k, v in table()['cost'].items():
        if v[0] is None:
            continue
        camp, sea, combo = k.split('|', 2)
        for it in combo.split('+'):
            if PT.availability(it, camp, sea) != 'OK':
                bad.append(k); break
    check('T13 no valued cell contradicts current availability', not bad,
          f'{len(bad)} stale cells, e.g. {bad[:3]}')


TESTS = [t1_no_ok_without_value, t2_never_measured_is_never_exact,
         t3_no_cell_beats_its_own_baseline, t4_cache_key_separates_bonus_and_table,
         t5_no_consumer_rolls_its_own_key, t6_consumers_agree_on_the_bonus,
         t7_weekend_option_makes_an_item_free, t8_corrupt_table_refuses_to_load,
         t9_save_is_atomic, t10_parsers_agree, t11_no_fabricated_hours,
         t12_availability_is_a_whitelist, t13_table_matches_current_availability]


def main():
    kf = None
    if '-k' in sys.argv:
        kf = sys.argv[sys.argv.index('-k') + 1]
    n = len(table()['cost'])
    print(f'cost table has {n} cells — invariant tests hold at any size\n')
    for t in TESTS:
        if kf and kf not in t.__name__:
            continue
        try:
            t()
        except Exception as e:
            FAILS.append(t.__name__)
            print(f'  ERROR {t.__name__}: {type(e).__name__}: {e}')
    print(f'\n{len(FAILS)} failing' if FAILS else '\nall clean')
    return len(FAILS)


if __name__ == '__main__':
    sys.exit(main())
