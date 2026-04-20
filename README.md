# VEsNA-Pro — CFR Personality Learning

Extension of the VEsNA-Pro BDI agent framework with **Counterfactual Regret Minimization (CFR)** for emergent personality evolution and adaptive colleague reciprocity.

> Paper submitted to **EUMAS 2026**: *"VEsNA-Pro: Exploiting BDI Agents with Propensities for Emergent Narrative"*

---

## What this does

A BDI agent (Alice) works in a simulated office with three colleagues of contrasting social profiles:

| Colleague | Type | Innate reciprocity |
|-----------|------|--------------------|
| **Bob** | Senior co-worker | 0.40 (moderate) |
| **Carol** | Exploitative peer | 0.10 (low) |
| **Dave** | Reciprocal collaborator | 0.90 (high) |

Alice starts with a **neutral OCEAN personality** (all traits = 0.5) and learns over 300 episodes via CFR-based regret matching. Her personality drifts toward the profile that maximises long-run social reward.

**New — Adaptive colleague reciprocity:**
Colleagues are no longer static. Each colleague observes Alice's behaviour each episode and adjusts their own reciprocity:
- If Alice **declines** → colleague raises reciprocity +0.02 (cap 0.85) to win cooperation back
- If Alice **helps** → colleague drifts slowly back toward their innate tendency (rate 0.003)

This closes a full mutual-adaptation loop and produces a genuine emergent social equilibrium.

---

## Key results

### Figure 2 — Personality convergence (10 seeds, 300 episodes)

![Figure 2](results/fig2_personality_regrets.png)

| Panel | Finding |
|-------|---------|
| **(a) Alice personality** | Converges by ep 100: C 0.50→0.69, N 0.50→0.12, A 0.50→0.40 |
| **(b) Bob regrets** | Delay dominates — Bob's moderate reciprocity makes delay optimal |
| **(c) Carol regrets** | Decline peaks then flattens as Carol adapts; growth rate → 0 |
| **(d) Dave regrets** | Help dominates massively (+750); decline is heavily penalised |
| **(e) Adaptive reciprocity** | Bob and Carol both rise to 0.84 by ep 150; Dave hits cap instantly |
| **(f) Growth rate → 0** | Regret-gap growth rate reaches zero by ep 150 — social equilibrium confirmed |

### Figure 3 — Reversal at 800 episodes (3 seeds)

![Figure 3](results/fig3_reversal.png)

Running to 800 episodes reveals the **full social loop closing**:

- Carol's reciprocity saturates at 0.84 by ep 150
- `help_carol` cumulative regret (deeply negative early on) climbs back and **crosses zero at ep 608 ± 61**
- Alice transitions from *regretting past cooperation* to *regretting past refusals* — a reversal impossible in static-colleague scenarios
- Agreeableness (A) recovers toward 0.51 as social pressure from Carol dissolves

---

## Architecture

```
src/agt/
  workplace_cfr_learning.asl   — AgentSpeak scenario (10 interactions/ep x 300 ep)
  vesna/
    Temper.java                — CFR engine: regret matching + softmax + personality update
    BehavioralMemory.java      — Per-colleague memory + adaptive reciprocity
    via/
      cfr_episode.java         — Episode boundary: CFR update + colleague adaptation
      record_outcome.java      — Reward shaping (alpha/beta/gamma)
    personality/
      PolicyLogger.java        — CSV logging: personality, regrets, adapted reciprocity
```

**Reward shaping** (grounded in MARL literature):
```
r_enhanced = r_base
           + alpha * (reciprocity - 0.5)        # social influence  [Jaques et al. ICML 2019]
           + beta  * 1[decline AND exploitative] # inequity aversion [Hughes et al. NeurIPS 2018]
           + gamma * (relationship - 0.5)        # potential-based   [Ng et al. ICML 1999]
```

Default: `alpha=0.6`, `beta=0.3`, `gamma=0.2` (configurable via `-Palpha=X` Gradle flag).

---

## Reproducing experiments

**Requirements:** Java 21, Python 3.x with `matplotlib pandas numpy`

```bash
# Single run (seed 0, 300 episodes)
./gradle-8.5/bin/gradle run

# Full 10-seed CFR experiment  ->  results/seed_0..9/
bash tests/run_10_seeds.sh

# Static baseline (no learning)  ->  results/static/seed_0..9/
bash tests/run_10_seeds.sh static

# Generate Figure 2 (10 seeds, 300 ep)
python tests/plot_figure2.py

# Extended 800-episode run for Figure 3
# 1. Set max_episodes(800) in src/agt/workplace_cfr_learning.asl
# 2. Run 3 seeds and save to results/reversal/
# 3. Generate Figure 3:
python tests/plot_figure3.py

# Alpha sensitivity (alpha in {0.4, 0.6, 0.8}, 3 seeds each)
bash tests/run_alpha_sensitivity.sh

# TensorBoard visualisation (mean across seeds)
python tests/log_tensorboard_mean.py
tensorboard --logdir tests/runs/mean_run
```

**Output CSVs** written per seed:

| File | Contents |
|------|----------|
| `personality_evolution.csv` | OCEAN traits + mood + reward per episode |
| `cfr_regrets.csv` | Cumulative regrets for all 9 actions |
| `adapted_reciprocity.csv` | Bob/Carol/Dave adapted reciprocity per episode |

---

## Repository structure

```
vesna-pro/
  src/agt/                     — Agent source (Java + AgentSpeak)
  src/env/                     — JaCaMo environment artifacts
  results/
    seed_0..9/                 — 10-seed CFR run (300 episodes)
    reversal/seed_0..2/        — 3-seed extended run (800 episodes)
    fig2_personality_regrets.png
    fig3_reversal.png
  tests/
    plot_figure2.py            — Figure 2: personality + regrets (10 seeds)
    plot_figure3.py            — Figure 3: reversal story (800 ep)
    run_10_seeds.sh            — Batch experiment runner (CFR or static)
    run_alpha_sensitivity.sh   — Sensitivity analysis over alpha
    cfr_tensorboard.py         — TensorBoard event file writer
    log_tensorboard_mean.py    — Log mean-across-seeds to TensorBoard
  vesna.jcm                    — JaCaMo project configuration
  build.gradle                 — Gradle build (Java 21, JaCaMo 1.2)
```

---

## References

- Zinkevich et al. (2008) — Regret Minimization in Games with Incomplete Information. *NeurIPS*.
- Ng et al. (1999) — Policy Invariance Under Reward Transformations. *ICML*.
- Hughes et al. (2018) — Inequity Aversion Improves Cooperation in Intertemporal Social Dilemmas. *NeurIPS*.
- Jaques et al. (2019) — Social Influence as Intrinsic Motivation for Multi-Agent Deep RL. *ICML*.
- Roberts et al. (2008) — Evaluating Five Factor Theory and Social Investment Perspectives. *J. Research in Personality*.
- Auer et al. (2002) — Finite-Time Analysis of the Multiarmed Bandit Problem. *Machine Learning*.
