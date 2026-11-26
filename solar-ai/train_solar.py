#!/usr/bin/env python
"""Train a DQN agent (agent_class.py from the lunar-lander repo) to run the SolarTracker-v0 environment from zero.
   python train_solar.py --f solar_agent [--seed 0] [--overwrite]
Outputs: <f>.tar (model snapshots), <f>_training_data.h5 (per-episode stats), <f>_execution_time.txt"""
import argparse, os, time, random
import numpy as np, torch, gymnasium as gym
import agent_class as agent
import solar_env  # registers SolarTracker-v0

p = argparse.ArgumentParser()
p.add_argument('--f', default='solar_agent'); p.add_argument('--seed', type=int, default=0)
p.add_argument('--overwrite', action='store_true'); p.add_argument('--verbose', action='store_true')
a = p.parse_args()
for fn in (f'{a.f}.tar', f'{a.f}_training_data.h5'):
    if os.path.exists(fn) and not a.overwrite: raise RuntimeError(f'{fn} exists, use --overwrite')
random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
env = gym.make('SolarTracker-v0')
parameters = {
    'N_state': 8, 'N_actions': 4,
    'discount_factor': 0.97, 'N_memory': 20000, 'training_stride': 4, 'batch_size': 64, 'saving_stride': 50,
    'n_episodes_max': 1500, 'n_solving_episodes': 30,
    'solving_threshold_min': 50., 'solving_threshold_mean': 87.,   # oracle controller: mean 92, worst day 62
    'd_epsilon': 1.5e-4, 'epsilon_1': 0.05,
    'target_net_update_tau': 0.02,
}
my_agent = agent.dqn(parameters=parameters)
t0 = time.time()
res = my_agent.train(environment=env, verbose=a.verbose, model_filename=f'{a.f}.tar', training_filename=f'{a.f}_training_data.h5')
dt = time.time() - t0
open(f'{a.f}_execution_time.txt', 'w').write(str(dt))
print(f'done: {len(res["epsiode_returns"])} episodes, {dt:.0f}s, completed={res["training_completed"]}')
