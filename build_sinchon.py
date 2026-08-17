# -*- coding: utf-8 -*-
"""
build_sinchon.py — unattended, resumable rebuild of the WHOLE cost table (1640 cells).

WHY THIS EXISTS
`partition.py` is chunk-resumable: each run appends what it finishes to partition.json and
exits. That is fine for the 국제 half (fast pools) but the 신촌 pools are ~4x larger, and the
That does not fit in an interactive session, so it runs here instead: launch it, walk away.
PICKS no longer means "first N pinned-geometry products". Every legal placement is now scored
at SCREEN_CAP, and PICKS is how many of the best survivors get re-scored at NODE_CAP.

WHAT THIS REPLACED
Originally the 국제 half was built at PICKS=6 and the 신촌 half at PICKS=2, an asymmetry that
understated 신촌. That is moot now: red-team F3 showed the whole placement search was wrong on
both halves, and the day-spread ordering that replaced it did not predict week value either
(국제S Seminar+ME+ME: placement #1 = -7.167, best of 6 = 6.658). Both halves are being rebuilt
under the two-stage search.

Measured on four 신촌 entries (R299):
    신촌F ME            33.069 -> 33.069     unchanged
    신촌F ECO2101       42.053 -> 42.053     unchanged
    신촌F ECO2102+MR5   38.374 -> 38.374     unchanged
    신촌S Chapel+ME     24.124 -> 26.558     +2.434
so it bites on a minority of entries, but when it bites it is worth ~10%.

⚠️ WHAT THAT MEANS FOR THE CURRENT ANSWER, BEFORE THIS FINISHES
The bias has a known SIGN and it is one-sided: only 신촌 is understated. The standing plan is
5 신촌 / 1 국제 — it was chosen WHILE 신촌 was handicapped, so correcting the handicap can only
reinforce it. The campus plan is therefore robust to this rebuild.
The deferral verdict is NOT provably robust: Fall 2026 is 국제 so its week score does not move,
but each branch's remainder is scored through 신촌 cells, and branches differ in how
신촌-suited their remainders are. Re-run the verdict after this completes.

RUN:
    python build_sinchon.py            # loops until done, prints progress, safe to Ctrl-C
    python build_sinchon.py --status   # just report how far along it is
Resume by re-running.
⛔ The previous version of this line claimed "nothing is lost on interrupt; partition.json is
only ever appended to." That was FALSE and the red team caught it: save() rewrote the whole
file, non-atomically, once per entry, and load() swallowed the resulting decode error and
returned an EMPTY table — a silent total wipe that this runner's stall guard could not see,
because after a wipe the child does do work and the entry count does move. save() is now
atomic (tmp + os.replace) and load() refuses to run on corruption. The claim is now true.
"""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
ENV = dict(os.environ, NODE_CAP='600000', MAX_PIN='3', PICKS='3',
           BUDGET='3600', PYTHONIOENCODING='utf-8')


def built():
    try:
        d = json.load(open(P('partition.json'), encoding='utf-8'))
    except Exception:
        return 0, 0
    c = d.get('cost', {})
    return sum(1 for k in c if k.startswith('신촌')), sum(1 for k in c if k.startswith('국제'))


TOTAL = 1640          # 410 combos x (국제S, 국제F, 신촌S, 신촌F)


def main():
    # ⛔ was `tgt = 820`, 신촌 only. Red-team F3 is a defect in the TABLE BUILDER, not in one
    # campus: the islice truncation mis-evaluated every multi-item cell, so the 820 국제
    # entries are wrong too and the whole table is being rebuilt. F4 (chapel) is 신촌-only,
    # F3 is not.
    tgt = TOTAL
    s0, i0 = built()
    if '--status' in sys.argv:
        print(f'{s0+i0}/{tgt}   (신촌 {s0}, 국제 {i0})')
        return
    print(f'start: {s0+i0}/{tgt} built  (신촌 {s0}, 국제 {i0})')
    t0 = time.time()
    stall = 0
    while True:
        _s, _i = built(); n_before = _s + _i
        if n_before >= tgt:
            print('\nDONE — full cost table rebuilt under the two-stage search.')
            print('Now re-run, in this order:')
            print('   python partition_verdict.py')
            print('   python partition_clickorder.py')
            print('   python render_v3_top50.py')
            print('all three with SINCHON_BONUS=30 set.')
            return
        # ⛔ this used to be stdout=DEVNULL, stderr=DEVNULL. When partition.py crashed on
        # launch the runner reported "stalled, no progress in 3 runs" and threw away the one
        # thing that would have explained it. Never discard a child's stderr in a loop whose
        # only failure signal is "nothing happened".
        t_run = time.time()
        r = subprocess.run([sys.executable, P('partition.py')], env=ENV,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, encoding='utf-8', errors='replace')
        dt = time.time() - t_run
        _s, _i = built(); n = _s + _i
        # a healthy chunk takes minutes; an instant exit means it died before doing any work
        if r.returncode != 0 or (n == n_before and dt < 20):
            print(f'\npartition.py exited after {dt:.1f}s with code {r.returncode} '
                  f'and built nothing. Its output:\n')
            out = (r.stdout or '').strip() or '(no output at all)'
            print('\n'.join(out.splitlines()[-25:]))
            return
        if n == n_before:
            stall += 1
            if stall >= 3:
                print(f'\nstalled at {n}/{tgt} after {dt:.0f}s runs. Last output:\n')
                print('\n'.join((r.stdout or '').strip().splitlines()[-25:]))
                return
        else:
            stall = 0
        el = time.time() - t0
        rate = (n - s0) / el if el > 0 and n > s0 else 0
        eta = (tgt - n) / rate / 3600 if rate else float('nan')
        print(f'  {n}/{tgt}   elapsed {el/60:6.1f} min   eta {eta:5.1f} h', flush=True)


if __name__ == '__main__':
    main()
