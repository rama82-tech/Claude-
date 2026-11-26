"""Evaluate a trained agent (greedy) against baselines on unseen days. python evaluate.py solar_agent [N]"""
import sys, numpy as np, torch, gymnasium as gym
import agent_class as agent, solar_env as S

def load(fn):
    d = torch.load(open(fn + '.tar', 'rb'), weights_only=False)
    st = d[max(d.keys())]
    a = agent.dqn(parameters=st['parameters']); a.load_state(state=st); return a

def episode(act, seed, storm=None, record=False):
    env = S.SolarTrackerEnv(); o, _ = env.reset(seed=seed, options={'storm': storm}); tot = 0; rec = []
    while True:
        a = act(o, env); o2, r, te, tr, info = env.step(a); tot += r
        if record: rec.append(dict(t=env.t - 1, angle=env.angle, sun=env.sun_angle(env.t - 1), cloud=env.cloud, wind=env.wind,
                                   power=info['power'], reward=r, damage=info['damage'], action=a, storm=env.storm))
        o = o2
        if te or tr: return tot, info['damage'], env.energy, rec

fixed = lambda o, e: 0
def oracle(o, e):
    if e.wind > 0.55 or (o[7] > 0.25 and e.wind > 0.35): return 3
    d = e.sun_angle(min(e.t, S.T - 1)) - e.angle
    return 1 if d > 2.5 else 2 if d < -2.5 else 0
def rnd_policy(rng): return lambda o, e: int(rng.integers(4))

if __name__ == '__main__':
    fn = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    ai = load(fn); rng = np.random.default_rng(5)
    pol = {'fixed panel': fixed, 'random (untrained)': rnd_policy(rng), 'trained AI': lambda o, e: ai.act(o), 'expert rule (oracle)': oracle}
    print(f'{"policy":22s} {"mean":>7s} {"p10":>7s} {"min":>7s} {"broken":>7s} {"energy":>7s}')
    for k, f in pol.items():
        rs = [episode(f, 50000 + i) for i in range(N)]
        R = np.array([r[0] for r in rs]); E = np.array([r[2] for r in rs]); br = np.mean([r[1] >= 3 for r in rs]) * 100
        print(f'{k:22s} {R.mean():7.1f} {np.percentile(R,10):7.1f} {R.min():7.1f} {br:6.1f}% {E.mean():7.1f}')
