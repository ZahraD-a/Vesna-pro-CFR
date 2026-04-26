# VEsNA-Pro — Co-evolutionary Personality Learning

Extension of the Pro-AgentSpeak(L) BDI agent framework with **regret-matching personality learning** and **adaptive reciprocity**, producing emergent cooperation between two co-evolving agents.

---

## What this does

A BDI agent (Alice) and a peer agent (Carol) work together in a simulated office over 2000 episodes. Both agents update their **OCEAN personality vectors** through the regret-matching loop; both observe each other's actions and adjust. The remaining colleagues (Bob, Dave) are static partners that provide reward context.

| Agent | Type | Initial OCEAN | Reciprocity |
|---|---|---|---|
| **Alice** | CFR-style learner | all traits = 0.0 (neutral) | — |
| **Bob** | static partner | profile from `help_bob` action | innate 0.40 |
| **Carol** | CFR-style learner with adaptive reciprocity | O=+0.2, C=−0.2, E=+0.2, **A=−0.4**, N=0.0 (mildly exploitative) | innate 0.10 (low) |
| **Dave** | static partner | profile from `help_dave` action | innate 0.90 |

Personality and mood share the **original Pro-AgentSpeak(L) range `[-1, +1]`**, where +1 = strongly embodies the trait, −1 = strongly negates, 0 = neutral.

**Adaptive colleague reciprocity:** every colleague tracks Alice's recent decisions and adjusts a per-colleague reciprocity ratio:
- If Alice **declines** → colleague raises reciprocity proportional to remaining capacity (asymptotes toward soft cap **0.85**)
- If Alice **helps** → colleague drifts slowly back toward their innate tendency (rate 0.003)

**The regret update is not canonical CFR.** Each step we compute, for every action `a` available in the current decision context:

```
r_t(a) = E_hist[r | a]  −  E_hist[r | chosen],   a ≠ chosen
r_t(chosen) = 0
R_T(I, a) ← R_T(I, a) + r_t(a)        (Hart & Mas-Colell 2000 regret matching)
```

The historical-mean baseline `E_hist[r | a]` plays the role of the COMA counterfactual baseline (Foerster et al. AAAI 2018, Eq. 5) — it is bandit-stable under non-stationarity, where Zinkevich (2008)'s `v(σ_t)` would be ill-defined because Carol's reciprocity is adapting. The convergence target is **no-regret stationarity in personality space** (a stable mutual best-response between two adaptive agents), **not Nash equilibrium**.

The novel mechanism is the projection from cumulative regrets onto OCEAN trait space (`Temper.updatePersonalityFromCFR`): the gradient of each trait is the regret-matching-weighted sum of the action profiles' contributions to that trait.

---

## Key results — 10 seeds × 2000 episodes

| Quantity | Start | End (mean ± std) |
|---|---|---|
| Alice Agreeableness | −0.01 | **+0.28 ± 0.12** |
| Alice Neuroticism | 0.0 | −0.62 ± 0.04 |
| Carol Agreeableness | −0.38 (init) | **+0.55 ± 0.09** |
| Carol Neuroticism | 0.0 | −0.46 ± 0.02 |
| Carol adapted reciprocity | 0.10 (innate) | 0.59 ± 0.06 |
| Bob adapted reciprocity | 0.40 (innate) | 0.67 ± 0.02 |
| Dave adapted reciprocity | 0.90 (innate) | 0.87 ± 0.00 (saturates near cap) |
| Phase-transition episode (peak `decline_alice` regret) | — | 398 ± 172 |
| Alice `P(decline | Carol)` | ≈ 0.85 | ≈ 0.05 |

**Headline finding (Figure 3, phase portrait).** The joint trajectory in `(Carol Agreeableness, Alice Agreeableness)` space starts in the non-cooperative lower-left quadrant `(−0.38, −0.01)` and converges to a tight cooperative cluster in the upper-right `(+0.55±0.09, +0.28±0.12)`. The closed loop of regret-matching personality projection × adaptive reciprocity produces this mutual best-response **with no explicit coordination signal**.

---

## Architecture

```
src/agt/
  workplace_cfr_learning.asl   — Scenario: max_episodes(2000), 10 interactions/ep,
                                  9 plan annotations in [-1,+1] OCEAN range
  vesna/
    Temper.java                — Regret-matching engine, COMA-style counterfactual
                                  baselines, projection onto OCEAN, [-1,+1] range
    BehavioralMemory.java      — Per-colleague memory, adaptive reciprocity
                                  (asymptotic to 0.85 cap), exploitation flag
    HelpScenarioConfig.java    — Action OCEAN profiles in [-1,+1], static partner
                                  reliability/reciprocity values
    via/
      cfr_episode.java         — Episode boundary: CFR projection + reciprocity
                                  drift + CSV logging
      record_outcome.java      — Reward shaping (alpha/beta/gamma)
      record_carol_cfr.java    — Carol's CFR pipeline (mirrors Alice's)
    personality/
      PolicyLogger.java        — CSV logging: personality, regrets, reciprocity
```

**Reward shaping** (potential-based, grounded in MARL literature):

```
r_enhanced = r_base
           + alpha * (reciprocity   - 0.5)              [Jaques et al. ICML 2019]
           + beta  * 1[decline AND exploitation_flag]   [Hughes et al. NeurIPS 2018]
           + gamma * (relationship  - 0.5)              [Ng et al. ICML 1999]
```

Defaults: `alpha=1.0`, `beta=0.3`, `gamma=0.2` (override at run time via `-Palpha=X`).

The α coefficient sweep `{0.4, 0.6, 1.0, 1.5}` is reported in `figD_alpha_sensitivity.png` and `figE_OCEAN_alpha_sensitivity.png` — phase-transition timing scales with α (≈ 233 → 672 across the range), but the equilibrium location in trait space is α-invariant.

---

## Reproducing experiments

**Requirements:** Java 21, Python 3.x with `matplotlib pandas numpy`, optional `tensorboard` for diagnostics.

```bash
# Single run (uses seed and episode count from vesna.jcm + workplace_cfr_learning.asl)
./gradle-8.5/bin/gradle run

# Full 10-seed CFR run -> results/seed_0..9/  (~5 min/seed at 2000 ep)
bash tests/run_10_seeds.sh

# Alpha sensitivity sweep (4 alphas x 5 seeds) -> results/alpha_<v>/seed_<n>/
bash scripts/run_alpha_sweep.sh
```

**Generate the four publication figures** (each reads from `results/seed_*/` and writes to `results/`):

```bash
python scripts/plot_paper_figures.py     # fig1 + fig2
python scripts/plot_phase_portrait.py    # fig3 (headline)
python scripts/plot_reciprocity.py       # fig4
python scripts/plot_alpha_sweep.py       # figD + figE  (alpha sensitivity)
```

**TensorBoard view** (per-seed traces + cross-seed mean/std):

```bash
python scripts/log_multiseed_tensorboard.py
tensorboard --logdir runs/multiseed --port 6006
# open http://127.0.0.1:6006/
```

**Output CSVs written per seed:**

| File | Contents |
|---|---|
| `personality_evolution.csv` | Alice OCEAN + mood + total reward per episode |
| `carol_personality_evolution.csv` | Carol OCEAN per episode |
| `cfr_regrets.csv` | Alice cumulative regrets for all 9 actions (3 per colleague) |
| `carol_cfr_regrets.csv` | Carol cumulative regrets for help / decline / reciprocate |
| `adapted_reciprocity.csv` | Bob / Carol / Dave adapted + innate ratios, Carol observed ratio, Carol exploitation flag |

---

## Repository structure

```
vesna-pro/
  src/agt/                                         BDI sources (Java + AgentSpeak)
  src/env/                                         JaCaMo environment artifacts
  scripts/
    plot_paper_figures.py                          fig1 (4-agent OCEAN) + fig2 (no-regret + behavior)
    plot_phase_portrait.py                         fig3 (Carol A vs Alice A, headline)
    plot_reciprocity.py                            fig4 (per-colleague reciprocity + consistency)
    plot_cfr_per_agent.py                          per-agent regret panels (diagnostic)
    plot_alpha_sweep.py                            figD + figE (alpha sensitivity)
    plot_multiseed.py                              alternative multi-seed view (diagnostic)
    log_multiseed_tensorboard.py                   writes runs/multiseed/{seed_NN, mean, std}/
    run_alpha_sweep.sh                             4 alphas x 5 seeds, 2000 ep each
  tests/
    run_10_seeds.sh                                10-seed batch runner (seeds 0..9)
  results/
    seed_0..9/                                     per-seed CSV outputs of the 10-seed run
    alpha_0_4/, alpha_0_6/, alpha_1_0/, alpha_1_5/ alpha-sweep outputs
    fig1_personality_4agents.png
    fig2_convergence_behavior.png
    fig3_phase_portrait.png                        (headline figure)
    fig4_adaptive_reciprocity.png
    figD_alpha_sensitivity.png
    figE_OCEAN_alpha_sensitivity.png
  runs/multiseed/                                  TensorBoard event files (per-seed + mean + std)
  vesna.jcm                                        JaCaMo project (agent definition, seed)
  build.gradle                                     Gradle build (Java 21, JaCaMo 1.2)
```

---

## Theoretical positioning

This work is **not** a contribution to canonical CFR. The setting violates each assumption canonical CFR is built on:

1. The game is **general-sum and cooperative**, not two-player zero-sum.
2. The opponent (Carol) is **non-stationary by design** — her reciprocity adapts in response to Alice's actions.
3. **Action selection is BDI personality-similarity**, not regret matching `R⁺(I,a)/Σ R⁺`.
4. **Cumulative regrets are projected onto OCEAN trait space**, not directly onto action probabilities. This is the contribution.

> **Note on the average strategy.** `strategySum` (in `Temper.InformationSet`) accumulates a *1-hot indicator of the chosen action* per visit, not the full mixed strategy distribution. This gives an empirical visit frequency rather than the canonical CFR average strategy `σ̄_T(I,a) = Σ_t π_t(I)σ_t(I,a) / Σ_t π_t(I)` (Zinkevich 2008, Theorem 1). Since action selection here is BDI similarity, not regret matching, the canonical average-strategy convergence theorem does not apply; the empirical frequency is the right diagnostic for this setting.

The appropriate theoretical reference points are:
- **Hart & Mas-Colell (2000)** — regret matching as a no-regret learning primitive
- **Foerster et al. (COMA, 2018)** — counterfactual advantage with action-conditional baselines
- **Hofbauer & Sigmund**-style co-evolutionary dynamics, replicator framing
- **Folk theorem** of repeated games — cooperation through repeated reciprocity

Convergence target: **no-regret stationarity / stable mutual best-response in personality space**.

---

## References

- Hart, S. & Mas-Colell, A. (2000) — A Simple Adaptive Procedure Leading to Correlated Equilibrium. *Econometrica* 68(5).
- Zinkevich, M. et al. (2008) — Regret Minimization in Games with Incomplete Information. *NeurIPS*.
- Foerster, J. et al. (2018) — Counterfactual Multi-Agent Policy Gradients (COMA). *AAAI*.
- Ng, A. et al. (1999) — Policy Invariance Under Reward Transformations. *ICML*.
- Hughes, E. et al. (2018) — Inequity Aversion Improves Cooperation in Intertemporal Social Dilemmas. *NeurIPS*.
- Jaques, N. et al. (2019) — Social Influence as Intrinsic Motivation for Multi-Agent Deep RL. *ICML*.
- Roberts, B. et al. (2008) — Evaluating Five Factor Theory and Social Investment Perspectives. *J. Research in Personality*.
