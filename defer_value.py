"""defer_value.py — measure what DEFERRING each fixed requirement is worth, in schedule points.

Iden takes 6 courses either way. Today four of them are forced (QRM1001 · WestCiv · LHP ·
SciRD). Deferring one means swapping that forced pick for a free choice from OPEN.

    defer_value(S) = best_score(slot S freed) − best_score(all four forced)

That is the exact number Iden must weigh against "one more semester of carrying it".
Implemented by injecting a PHANTOM into slot S: a zero-credit section that occupies no
time and no presence, standing for "not taken this semester". Credits are then made up
from OPEN, which is what deferring actually looks like.
"""
import sys, json, copy
import rank2 as R2

PHANTOM = dict(c='DEFER-00-00', code='DEFER', n='(이 요건을 이번 학기에 안 들음)',
               cat=None, qcat=None, yr='1', lang='10', note='', cr=0.0,
               time=[], pres=[], tm=0, pm=0, t='', dept='', kinds=[], _role=0.0)

def run(freed=None):
    """freed = slot name to relax, or None for the baseline."""
    orig = R2.main
    got = {}
    import builtins
    real_print = builtins.print
    builtins.print = lambda *a, **k: None
    try:
        src_main = orig
        # monkeypatch: after pools are built, drop a phantom into the freed slot
        import types, re
        code = open('rank2.py', encoding='utf-8').read()
        marker = "    sig = collections.defaultdict(list)"
        assert marker in code, "pool-build marker moved"
        inject = ("    if _FREED: P[_FREED].append(dict(_PHANTOM))\n" + marker)
        ns = {'_FREED': freed, '_PHANTOM': PHANTOM}
        exec(compile(code.replace(marker, inject, 1), 'rank2_patched', 'exec'), ns)
        out, sig, idx = ns['main']()
        got = (out[0][0], out)
    finally:
        builtins.print = real_print
    return got

if __name__ == '__main__':
    base, _ = run(None)
    print(f"baseline (all four requirements taken now): {base:.2f}\n")
    print(f"{'deferred slot':10s} {'best score':>11s} {'gain':>8s}   meaning")
    for slot, label in [('WCiv','서양문명'), ('LHP','역사/문학'), ('SciRD','과학|RDQM'), ('MR','QRM입문')]:
        sc, _ = run(slot)
        print(f"  {label:9s} {sc:11.2f} {sc-base:+8.2f}   "
              f"{'deferring buys nothing' if sc-base < 0.5 else 'deferring buys real comfort'}")
