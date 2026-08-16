# -*- coding: utf-8 -*-
"""k_reference.py — the REFERENCE DISTRIBUTION of K over the mask space.

⭐ THE REFORMULATION. K(section, n) depends only on the section's TIME MASK, never on which
course it is. So the uncertainty does not need stratifying by course at all: every requirement
reduces to "which mask will it have in its receiving term?", and the cost of any mask is one
exactly-computable function, shared across all of them.

That makes the sample space enumerable instead of hand-picked: at 국제 the ≥3h mask space is
small enough to run EXHAUSTIVELY, so there is no sampling error there at all. 신촌 is sampled.
"""
import json, os, sys, time, random, statistics
import b1_curve as B

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, 'k_reference.json')


def run(campus, loads=(3, 4, 5), sample=None, seed=0, budget=150):
    base = {tuple(k.split('|')[0:1]) + (int(k.split('|')[1]),): tuple(v)
            for k, v in json.load(open(os.path.join(HERE, 'b1_base.json'), encoding='utf-8')).items()}
    pool = B.pool_for(campus)
    masks = list(pool)
    if sample and sample < len(masks):
        random.Random(seed).shuffle(masks)
        masks = masks[:sample]
    out = {}
    if os.path.exists(P) and os.path.getsize(P):
        out = json.load(open(P, encoding='utf-8'))
    out.setdefault(campus, {})
    t0 = time.time()
    for i, g in enumerate(masks):
        key = str(g[0])
        if key in out[campus]:
            continue
        rec = {}
        for n in loads:
            v, _nd, ok = B.best_week([tuple(g)], n, pool, node_cap=30_000_000)
            b, _ = base[(campus, n + 1)]
            rec[str(n)] = None if v is None else round(b - v, 4)
        out[campus][key] = rec
        json.dump(out, open(P, 'w'), indent=0)
        if time.time() - t0 > budget:
            print(f"  ... stopped after {len(out[campus])} masks ({time.time()-t0:.0f}s)", flush=True)
            break
    done = len(out[campus]); print(f"{campus}: {done}/{len(pool)} masks measured", flush=True)
    for n in loads:
        v = sorted(r[str(n)] for r in out[campus].values() if r.get(str(n)) is not None)
        if not v:
            continue
        q = lambda p: v[min(len(v) - 1, int(p * len(v)))]
        print(f"   n={n}: min {v[0]:7.2f} | p10 {q(.10):7.2f} | median {q(.50):7.2f} | "
              f"p90 {q(.90):7.2f} | max {v[-1]:7.2f}   (n={len(v)})", flush=True)
    return out


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else '국제',
        sample=int(sys.argv[2]) if len(sys.argv) > 2 else None,
        budget=float(sys.argv[3]) if len(sys.argv) > 3 else 150)
