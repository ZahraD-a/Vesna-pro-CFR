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

Alice starts with a **neutral OCEAN personality** (all traits = 0.5) and learns over 400 episodes via CFR-based regret matching. Her personality drifts toward the profile that maximises long-run social reward.

**Adaptive colleague reciprocity:**
Colleagues are no longer static. Each colleague observes Alice's behaviour each episode and adjusts their own reciprocity:
- If Alice **declines** → colleague raises reciprocity +0.02 (cap 0.85) to win cooperation back
- If Alice **helps** → colleague drifts slowly back toward their innate tendency (rate 0.003)

**EMA-corrected exploitation detection:**
`BehavioralMemory` tracks observed reciprocity via EMA (α=0.12) rather than a cumulative ratio. This ensures the exploitation flag φ responds to *recent* behaviour: when Carol's adapted reciprocity rises past 0.20, φ deactivates and the β=0.3 boundary bonus is removed — enabling the full regret reversal within 400 episodes.

---

## Key results

### Figure 2 — Personality convergence (10 seeds, 400 episodes)

![Figure 2](results/fig2_personality_regrets.png)

| Panel | Finding |
|-------|---------|
| **(a) Alice personality** | Converges by ep 100: A 0.50→0.66, N 0.50→0.34, C 0.50→0.51 |
| **(b) Bob regrets** | Delay dominates — Bob's moderate reciprocity makes delay optimal |
| **(c) Carol regrets** | decline_carol peaks then reverses; mean crosses zero at ep 222 ± 120 |
| **(d) Dave regrets** | Help dominates massively; decline heavily penalised |
| **(e) Adaptive reciprocity** | Bob and Carol both rise toward 0.82–0.85 by ep 150; Dave hits cap instantly |
| **(f) Growth rate → 0** | Regret-gap growth rate reaches zero by ep 150 — social equilibrium |

### Figure 3 — EMA reversal story (10 seeds, 400 episodes)

![Figure 3](results/fig3_reversal.png)

The EMA fix exposes the full causal chain of the social reversal:

| Panel | Finding |
|-------|---------|
| **(a) ρ_observed(Carol)** | EMA tracks Carol's true adapted reciprocity; rises from 0.10 past the 0.20 threshold by ep ~46 |
| **(b) φ(Carol) flag** | Exploitation flag deactivates at ep 46 ± 12 — β bonus removed |
| **(c) Instantaneous Δ** | Per-episode change in decline_carol regret turns negative after φ off |
| **(d) Cumulative** | decline_carol regret crosses zero at ep 222 ± 120 — reversal confirmed |

---

## Architecture

```
src/agt/
  workplace_cfr_learning.asl   — AgentSpeak scenario (10 interactions/ep x 400 ep)
  vesna/
    Temper.java                — CFR engine: regret matching + softmax + personality update
    BehavioralMemory.java      — Per-colleague memory (EMA reciprocity) + adaptive reciprocity
    via/
      cfr_episode.java         — Episode boundary: CFR update + colleague adaptation + CSV logging
      record_outcome.java      — Reward shaping (alpha/beta/gamma)
    personality/
      PolicyLogger.java        — CSV logging: personality, regrets
```

**Reward shaping** (grounded in MARL literature):
```
r_enhanced = r_base
           + alpha * (reciprocity - 0.5)        # social influence  [Jaques et al. ICML 2019]
           + beta  * 1[decline AND phi_active]   # inequity aversion [Hughes et al. NeurIPS 2018]
           + gamma * (relationship - 0.5)        # potential-based   [Ng et al. ICML 1999]
```

Default: `alpha=0.6`, `beta=0.3`, `gamma=0.2` (configurable via `-Palpha=X` Gradle flag).

**EMA exploitation detection:**
```java
// BehavioralMemory.java — inside if (helped) block
reciprocityRatio = 0.88 * reciprocityRatio + 0.12 * (reciprocated ? 1.0 : 0.0);
isExploitative = reciprocityRatio < 0.2 && timesAsked > 3;
```
α=0.12 gives a ~30-episode convergence window (vs. cumulative ratio which becomes insensitive after ~1000 observations).

---

## Reproducing experiments

**Requirements:** Java 21, Python 3.x with `matplotlib pandas numpy`

```bash
# Single run (seed 0, 400 episodes)
./gradle-8.5/bin/gradle run

# Full 10-seed CFR experiment  ->  results/seed_0..9/
bash tests/run_10_seeds.sh

# Generate Figure 2 (10 seeds, 400 ep)
python tests/plot_figure2.py

# Generate Figure 3 (EMA reversal, 10 seeds, 400 ep)
python tests/plot_figure3.py

# TensorBoard visualisation (mean across seeds)
python tests/log_tensorboard_mean.py
tensorboard --logdir tests/runs/mean_run
```

**Output CSVs** written per seed:

| File | Contents |
|------|----------|
| `personality_evolution.csv` | OCEAN traits + mood + reward per episode |
| `cfr_regrets.csv` | Cumulative regrets for all 9 actions |
| `adapted_reciprocity.csv` | Bob/Carol/Dave adapted reciprocity + carol_observed_ratio + carol_phi per episode |

---

## Repository structure

```
vesna-pro/
  src/agt/                     — Agent source (Java + AgentSpeak)
  src/env/                     — JaCaMo environment artifacts
  results/
    seed_0..9/                 — 10-seed CFR run (400 episodes, EMA fix)
    fig2_personality_regrets.png
    fig3_reversal.png
  tests/
    plot_figure2.py            — Figure 2: personality + regrets (10 seeds)
    plot_figure3.py            — Figure 3: EMA reversal story (4 panels)
    run_10_seeds.sh            — Batch experiment runner
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
