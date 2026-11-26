# Solar AI: an agent that learns to run a solar panel from zero

A DQN agent learns, with no hand-written rules, to run a single-axis solar tracker: follow the sun, cope with clouds, and flatten the panel before a storm damages it. It reuses `agent_class.py` from the uploaded lunar-lander repo unchanged. Only the environment is new.


## Files
| File | What it is |
|---|---|
| `solar_ai_training.mp4` | 54 s video: setup, learning curve, same stormy day for fixed / untrained / trained, results |
| `solar_env.py` | the environment `SolarTracker-v0` (gymnasium) |
| `agent_class.py` | DQN agent, copied unmodified from the uploaded repo |
| `train_solar.py` | trains an agent from scratch (`python train_solar.py --f solar_agent --overwrite --verbose`) |
| `evaluate.py`, `make_results.py` | test on unseen days against baselines, write `results.json` |
| `make_video.py` | renders the video from the trained model (PIL + ffmpeg) |
| `solar_agent.tar` | the trained model (seed 0). `solar_agent_training_data.h5`, `train_log.txt`: its training record |
| `seeds/` | four more independent trainings (seeds 1-4) |
| `results.json` | all measured numbers |

## The task
- One episode is one daylight day: 144 steps of 5 minutes. Storms hit about half the days.
- Sees (8 numbers): time of day, sun elevation, sun angle minus panel angle, panel angle, cloud cover, wind, wind trend.
- Actions: rotate east, rotate west, hold, stow flat.
- Reward: harvested power each step, minus 0.01 per motor move. If wind > 0.8 and the panel is tilted more than 15 degrees, it takes -5 per step; after 3 damaged steps the panel breaks (-50, episode ends).
- Training stops when, over the last 30 days, the mean reward is above 87 and the worst day above 50.

## Results: 300 days never seen in training (higher score is better)
| Policy | mean score | worst 10% | panel broken |
|---|---|---|---|
| Fixed panel (never moves) | 47.4 | -32.4 | 22.0% |
| Random moves | 66.7 | 52.9 | 3.3% |
| **Trained AI, seed 0 (featured)** | **82.2** | 63.7 | 0.0% |
| Trained AI, average of 5 seeds | 83.2 | 64.7 | 1.2% |
| Expert rule (hand-written, sees the same inputs) | 89.6 | 69.1 | 0.0% |

Per seed, the mean score was 82.2, 86.9, 81.8, 77.9 and 87.3, and the panel broke on 0, 0, 4.3, 1.3 and 0.3% of days.

## Caveats
- This is a simulation. Sun, cloud and wind are simple models I wrote. The agent has not touched real hardware, and the numbers say nothing about a real installation.
- The trained AI reaches about 93% of the hand-written expert, not more. It is not guaranteed safe: two of the five trainings broke the panel on more than 1% of days. Do not use it as a safety system.
- Featured model: seed 0, the first one trained, not the best. The demo day (seed 912) was picked as a typical storm day where the fixed panel breaks.
- The first early-stopped model (stopping rule of 20 days, mean above 85) scored 81.8 with 4% broken panels, so I tightened the stopping rule.
