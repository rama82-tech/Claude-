"""SolarTracker-v0: a gymnasium environment where an AI learns to run a single-axis solar tracker.

One episode = one daylight day (144 steps of 5 minutes, sunrise to sunset).
Goal: harvest as much energy as possible while keeping the panel safe.

Actions (4):  0 hold | 1 rotate +5 deg (west) | 2 rotate -5 deg (east) | 3 stow (flatten, 15 deg/step)
Observation (8): sin/cos of time of day, sun elevation, (sun angle - panel angle), panel angle,
                 cloud cover, wind speed, wind trend.
Reward per step: harvested power (0..1) - 0.01 per motor move.
Storm rule: if wind > 0.8 and the panel is tilted more than 15 deg the panel takes damage:
            -5 reward per step; after 3 damaged steps the panel breaks (episode ends, -50).
"""
import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces

T = 144
MAX_ANGLE = 60.0
STORM_WIND = 0.8
SAFE_TILT = 15.0


class SolarTrackerEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, p_storm=0.5):
        self.p_storm = p_storm
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(-1.0, 1.0, (8,), np.float32)
        self.rng = np.random.default_rng()

    # ------------------------------------------------------------- helpers
    def sun_angle(self, t):
        return -75.0 + 150.0 * t / (T - 1)          # degrees, east (-) to west (+)

    def _obs(self):
        t = self.t
        ts = self.sun_angle(min(t, T - 1))
        e = max(0.0, math.cos(math.radians(ts)))
        trend = (self.wind - self.prev_wind) * 5
        o = [math.sin(2 * math.pi * t / T), math.cos(2 * math.pi * t / T), e,
             np.clip((ts - self.angle) / 90.0, -1, 1), self.angle / MAX_ANGLE,
             self.cloud, self.wind, np.clip(trend, -1, 1)]
        return np.array(o, dtype=np.float32)

    def power(self, t, angle, cloud):
        ts = self.sun_angle(t)
        e = max(0.0, math.cos(math.radians(ts))) ** 0.5
        return e * (1 - 0.75 * cloud) * max(0.0, math.cos(math.radians(ts - angle)))

    # ------------------------------------------------------------- gym API
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        r = self.rng
        force_storm = (options or {}).get("storm")
        self.t = 0
        self.angle = float(r.uniform(-30, 30))
        self.damage = 0
        self.cloud_base = float(r.uniform(0.0, 0.6))
        self.cloud = self.cloud_base
        has_storm = r.random() < self.p_storm if force_storm is None else bool(force_storm)
        self.storm = None
        if has_storm:
            start = int(r.integers(30, 100)); length = int(r.integers(12, 26))
            self.storm = (start, length)
        self.wind = 0.15; self.prev_wind = 0.15
        self.energy = 0.0
        return self._obs(), {}

    def _wind_at(self, t):
        base = 0.2 + 0.05 * math.sin(t / 7.0)
        if self.storm:
            s, L = self.storm
            if s <= t < s + 8: base += (0.95 - base) * (t - s + 1) / 8        # ramp up
            elif s + 8 <= t < s + L: base = 0.95                              # peak
            elif s + L <= t < s + L + 5: base = 0.95 - 0.75 * (t - s - L + 1) / 5   # ramp down
        return float(np.clip(base + self.rng.normal(0, 0.02), 0, 1))

    def step(self, action):
        moved = 0
        if action == 1: self.angle += 5; moved = 1
        elif action == 2: self.angle -= 5; moved = 1
        elif action == 3:
            if abs(self.angle) > 1e-6: moved = 1
            self.angle -= math.copysign(min(15.0, abs(self.angle)), self.angle)
        self.angle = float(np.clip(self.angle, -MAX_ANGLE, MAX_ANGLE))
        # weather evolves
        self.cloud = float(np.clip(self.cloud + 0.1 * (self.cloud_base - self.cloud) + self.rng.normal(0, 0.03), 0, 1))
        self.prev_wind = self.wind
        self.wind = self._wind_at(self.t)
        p = self.power(self.t, self.angle, self.cloud)
        reward = p - 0.01 * moved
        terminated = False
        if self.wind > STORM_WIND and abs(self.angle) > SAFE_TILT:
            self.damage += 1; reward -= 5.0
            if self.damage >= 3: reward -= 50.0; terminated = True
        else:
            self.energy += p
        self.t += 1
        truncated = self.t >= T
        return self._obs(), float(reward), terminated, truncated, {"power": p, "damage": self.damage}


gym.register(id="SolarTracker-v0", entry_point=SolarTrackerEnv)
