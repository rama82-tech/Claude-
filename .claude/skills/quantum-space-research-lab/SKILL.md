---
name: quantum-space-research-lab
description: Build, verify and plot quantum and space-physics simulations in Python. Covers quantum circuits, entanglement, variational and quantum machine learning models, spin chains and quantum sensors, plus orbital mechanics, satellite orbits, space weather, solar wind, geomagnetic storms and solar flares. Physics checks such as normalization, unit consistency and conservation laws run before any result is reported. Use this skill whenever the user wants to simulate, model, predict or visualize anything quantum or space-related, even if they only say "run my quantum-space pipeline", "model a LEO satellite", "predict Kp from solar wind", "make a Bell state" or "train a QML classifier", and they don't mention verification.
---

# Quantum Space Research Lab

Turn a quantum or space research question into working code, tests that check the physics, a labeled chart and a short honest report. It's easy to produce plots that look plausible but are physically wrong, or numbers that look real but were made up. This workflow is designed to catch both.

## The five phases

The workflow is written as five roles, but they are **phases of one agent's work**, run in order. Don't spawn parallel subagents for them. That costs many times the tokens and adds nothing, because the phases depend on each other. Use subagents only if the user explicitly asks for them.

### 1. Plan (CEO)

Before writing code, restate the question in 2–4 lines and split it into three tracks:

- **Quantum:** circuits, states, Hamiltonians, variational and QML models.
- **Space:** orbits, forces, space-weather features, physical constraints.
- **Data and plots:** loading data, the training or simulation loop, charts.

A question may need only one or two tracks. Skip the tracks it doesn't need, and don't invent work to fill them.

Decide on the data source up front and write it down:

- **Real public data.** Name the source and the URL. Good defaults:
  - NOAA SWPC JSON feeds (`services.swpc.noaa.gov`) for solar wind, Kp and X-ray flux.
  - NASA OMNIWeb for historical solar wind and IMF.
  - CelesTrak (`celestrak.org`) for TLE and GP orbital elements.
  - NASA DONKI for flare and CME event lists.
- **Synthetic benchmark.** Generate it with a fixed random seed. Label it `SYNTHETIC` in the file names, the chart title and the report.

If real data was requested but the download fails (blocked network, 4xx/5xx error, bad format), **stop and say so**. Then offer a synthetic run as an option, clearly labeled. Never quietly swap in made-up or hard-coded numbers and present the results as if they came from the real source. That is the most damaging failure this workflow can produce, because the output looks fine and is wrong.

### 2. Build

Use this project layout, so every run looks the same and is easy to review:

```
<project>/
├── quantum/       # quantum track modules
├── space/         # space track modules
├── analysis/      # data loading, run/training loop, plotting
├── tests/         # pytest physics and QA checks
├── plots/         # saved PNG charts
└── results.md     # final report (phase 5)
```

Create only the folders the plan needs. Put a `run.py` (or `main.py`) at the root that reproduces everything with a single command.

**Quantum track**

- Use PennyLane or Qiskit if they are installed, or if the user asks for them and installing works. Otherwise write the simulation directly in NumPy and SciPy: state vectors, gate matrices and Kronecker products are enough for up to about 12 qubits. Say which backend you used and why. A NumPy simulation is perfectly valid. A crash because Qiskit isn't installed is not.
- Fix random seeds so results can be reproduced.

**Space track**

- Use SI units throughout (m, s, kg, m³/s²), with any conversions done at the edges: inputs in km or nT, outputs in km, hours or degrees. If `astropy.units` is available, use it at function boundaries. If not, put units in variable names and docstrings (`r_m`, `v_mps`).
- Take constants from one place, such as `scipy.constants`, or a single `constants.py` with cited values: μ_Earth = 3.986004418e14 m³/s², R_Earth = 6.3781e6 m.
- To integrate orbits, use a symplectic or high-order method (`scipy.integrate.solve_ivp` with `method="DOP853"` and `rtol≈1e-10`). Plain Euler steps make energy drift and will fail the conservation checks below.

**Data and plots**

- Every chart needs a title, labeled axes **with units**, a legend if it has more than one series, and the `SYNTHETIC` tag if it applies. Save charts as PNG files in `plots/` at 150 dpi or more. Use a non-interactive backend (`matplotlib.use("Agg")`) so the code runs headless.
- For ML or QML: hold out a test split, and report test metrics alongside a simple baseline (a majority class, a persistence forecast or a linear model). Without a baseline, an accuracy number tells you nothing.

### 3. Verify (physics QA)

This phase decides whether the results are right. If the code and the math disagree, the math wins, even when the code "looks right". Write the tests in `tests/` and run `pytest -q` after each significant code change. If a test fails, fix the physics, not the test. If a tolerance genuinely needs loosening, explain why in the report.

`scripts/physics_checks.py` (in this skill's folder) contains ready-made assertions. Import it or copy from it rather than rewriting them:

| Check | Function | Typical tolerance |
|---|---|---|
| State vector has norm 1 | `assert_normalized(psi)` | 1e-10 |
| Probabilities are non-negative and sum to 1 | `assert_probabilities(p)` | 1e-10 |
| Density matrix is Hermitian, has trace 1 and is positive semidefinite | `assert_valid_density_matrix(rho)` | 1e-10 |
| Gate or evolution operator is unitary | `assert_unitary(U)` | 1e-10 |
| Specific orbital energy is conserved | `assert_conserved(energy_series, rtol)` | 1e-6 for a two-body orbit |
| Angular momentum is conserved | `assert_conserved(h_series, rtol)` | 1e-6 |
| Data is real, not filler | `assert_no_fabricated_fallback(df)` | — |

Pick the checks that fit the physics. Atmospheric drag breaks energy conservation, for example, so check instead that energy *decreases* over time. Also add at least one **known-answer test**: a case with an analytic answer, such as a Bell state's ⟨ZZ⟩ = 1, a circular orbit's period T = 2π√(a³/μ), or a Rabi oscillation's frequency.

Also check the data-loading code: a failed fetch must raise an error or exit non-zero. Look for `except: pass`, hard-coded arrays standing in for downloaded data, and `np.random` called inside a function that claims to load real data. Remove any of these you find.

### 4. Run

Run `python run.py` and `pytest -q`. Capture the numbers and the pytest summary line. Both have to come from actual runs, not from what you expect them to say.

### 5. Report (CEO summary)

Write `results.md`, and give the user a short version in chat:

```markdown
# <Question in one line>

**Data:** <source + URL + date range>  |  or  **Data: SYNTHETIC (seed=N)**
**Backend:** <NumPy / PennyLane / Qiskit …>

## Key results
- <metric>: <value with units>  (baseline: <value>)
- …

## Verification
- pytest: <N passed, M failed>  — <list the physics checks that ran>

## Charts
- plots/<file>.png — <one-line description>

## Limitations
- <assumptions, simplifications, what was not modeled>

## Next experiment
- <one concrete, specific step>
```

Keep it honest. If something failed or was skipped, say so here rather than leaving it out.

## Keeping costs down

- Start small: few qubits, short time spans, small datasets. Scale up only after the tests pass.
- Do all prototyping in software or cloud notebooks. Suggest hardware (a real QPU, lab equipment) only once a simulation shows something worth testing physically.
