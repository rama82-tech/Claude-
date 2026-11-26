"""Evaluates everything on 300 unseen days and writes results.json (used by the video + report)."""
import json, numpy as np, evaluate as E
N = 300; rng = np.random.default_rng(5)
def stats(f):
    rs = [E.episode(f, 50000 + i) for i in range(N)]
    R = np.array([r[0] for r in rs])
    return dict(mean=float(R.mean()), p10=float(np.percentile(R, 10)), min=float(R.min()),
                broken_pct=float(np.mean([r[1] >= 3 for r in rs]) * 100), energy=float(np.mean([r[2] for r in rs])))
out = {'n_days': N, 'baselines': {'fixed panel': stats(E.fixed), 'random (untrained)': stats(E.rnd_policy(rng)), 'expert rule': stats(E.oracle)}, 'seeds': {}}
for name, fn in [('seed 0 (featured)', 'solar_agent')] + [(f'seed {s}', f'seeds/agent_{s}') for s in (1, 2, 3, 4)]:
    ai = E.load(fn); out['seeds'][name] = stats(lambda o, e: ai.act(o))
S = out['seeds'].values()
out['ai_avg'] = {k: float(np.mean([s[k] for s in S])) for k in ('mean', 'p10', 'energy', 'broken_pct')}
json.dump(out, open('results.json', 'w'), indent=1); print(json.dumps(out, indent=1))
