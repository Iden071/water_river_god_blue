# -*- coding: utf-8 -*-
"""build_vsim_table.py — R214. Precompute the SIMULATED V for every state the ranker asks for.

⭐ THE REALISATION THAT MAKES WIRING-IN POSSIBLE.
`rank4.V(state)` is already memoised on `state = (frozenset deferred, sorted tuple of
elective items)`. The elective items come from only three values — FREE / ECO1101 / ME — so
the KEY SPACE IS TINY: 32 deferral subsets x (multisets of size nslots) is a few hundred
states, not a few thousand candidates. The reason the corrected V "could not be wired into
the search" was never the search — it was that I was calling it per candidate in my head
instead of per state.

So: compute `continuation_sim.best_plan` once per state, cache to disk, and let rank4.V read
the table. The ranker then optimises the CORRECTED objective directly, and `FINAL_ranked4.csv`
stops being a ranking the model itself disbelieves.

Resumable: re-run until it prints DONE. Writes `vsim_table.json`.
"""
import json, os, sys, time, itertools
from defer_value2 import remainder_after, ALL_REQS
import continuation_sim as CS
import rank4

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, 'vsim_table.json')
OPTS = ('FREE', 'ECO1101', 'ME')
N_ACADEMIC = rank4.N_ACADEMIC

# ⭐ EVERY deferral subset. Not a hand-written list — R212: the branch set was PREDECIDED,
# which silently defined 'defer two or more' out of existence. The powerset is computed.
SUBSETS = [frozenset(c) for k in range(len(ALL_REQS) + 1)
           for c in itertools.combinations(ALL_REQS, k)]


def states():
    for d in SUBSETS:
        nslots = N_ACADEMIC - (len(ALL_REQS) - len(d))
        if nslots < 0:
            continue
        for combo in itertools.combinations_with_replacement(OPTS, nslots):
            yield (d, tuple(sorted(combo)))


def key_str(st):
    d, items = st
    return ('+'.join(sorted(d)) or '-') + '|' + '+'.join(items)


def main(budget_s=150.0):
    table = {}
    if os.path.exists(PATH) and os.path.getsize(PATH):
        table = json.load(open(PATH, encoding='utf-8'))
    todo = [st for st in states() if key_str(st) not in table]
    total = sum(1 for _ in states())
    print(f"{len(table)}/{total} cached, {len(todo)} to go", flush=True)
    t0 = time.time()
    done = 0
    for st in todo:
        if time.time() - t0 > budget_s:
            break
        d, items = st
        taken = [x for x in ALL_REQS if x not in d]
        rem = remainder_after(taken, [], chapel=True)
        for k in items:
            rem[k] = max(0, rem[k] - 1)
        res = CS.best_plan(rem)
        # INFEASIBLE is recorded as a large negative, never as a missing key — a missing key
        # would let the ranker fall back to the proxy without saying so.
        table[key_str(st)] = res['value'] if res else -1e6
        done += 1
    json.dump(table, open(PATH, 'w'), indent=0)
    left = total - len(table)
    print(f"wrote {len(table)}/{total}  (+{done} this pass, {time.time()-t0:.0f}s)")
    print("DONE" if left == 0 else f"{left} REMAINING — run again")


if __name__ == '__main__':
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 150.0)
