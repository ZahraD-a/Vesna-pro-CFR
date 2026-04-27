# VEsNA-Pro — Co-evolutionary Personality Learning

Extension of the Pro-AgentSpeak(L) BDI agent framework with **regret-matching personality learning** and **adaptive reciprocity**, producing emergent cooperation between two co-evolving agents.

---

## What this does

A BDI agent (Alice) and a peer agent (Carol) work together in a simulated office over **2000 episodes**. Each episode contains 30 plan-decision interactions for Alice (10 per colleague), so Alice's total **CFR iteration count $T = 60{,}000$**. Carol's CFR fires once per Carol-context interaction (10 per episode → $T_{\text{Carol}} = 20{,}000$). Cumulative regret is updated once per iteration; the plot scripts use iteration $t$ as the time axis. Both agents update their **OCEAN personality vectors** through the regret-matching loop; both observe each other's actions and adjust. The remaining colleagues (Bob, Dave) are static partners that provide reward context.

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

## Key results — 10 seeds × 2000 episodes (60 000 CFR iterations)

All paper figures use **CFR iteration `t`** as the X-axis (Leduc convention; `t = episode × 30 record_outcome calls/episode`).

| Quantity | Start ($t=0$) | End ($t=60{,}000$, mean ± std) |
|---|---|---|
| Alice Agreeableness | −0.01 | **+0.26 ± 0.10** |
| Alice Neuroticism | 0.00 | −0.62 ± 0.03 |
| Carol Agreeableness | −0.40 (init) | **+0.36 ± 0.009** |
| Carol Neuroticism | 0.00 | −0.51 ± 0.002 |
| Carol Conscientiousness | −0.20 (init) | +0.20 ± 0.000 (saturates at action-profile fixed point) |
| Carol adapted reciprocity | 0.10 (innate) | 0.61 ± 0.07 |
| Bob adapted reciprocity | 0.40 (innate) | 0.69 ± 0.04 |
| Dave adapted reciprocity | 0.90 (innate) | 0.87 ± 0.00 (saturates near 0.85 cap) |
| Carol exploitative flag `φ` deactivation iteration | — | **`t ≈ 1410 ± 1260`** ($\sim$ ep 47 ± 42, range 1–116) |
| Carol observed help-rate from Alice | 0.00 | 0.62 ± 0.03 |

**Two-agent CFR design (asymmetric by intent).** Alice's CFR state lives in `Temper`; Carol's in `BehavioralMemory.PersonMemory`. Alice optimises her own utility over her plan space; Carol's regret tracks the action she attributes to Alice's behaviour (`help_alice → reciprocate`, `decline_alice → decline`, `teach_alice → help`). The asymmetry is intentional: Carol's role is observational reciprocity, not independent utility maximisation. See `record_carol_cfr.java` for the mapping and the per-iteration regret stream.

**Note on Bob/Dave reciprocity adaptation (fig4).** Bob and Dave do *not* run CFR. Their `adaptedReciprocity` is updated by a hand-coded rule in `BehavioralMemory.adaptReciprocity` — when Alice declines, the colleague raises reciprocity proportional to remaining capacity; when Alice helps, it drifts back toward innate. This is a *separate mechanism* from the CFR personality learning that runs on Alice and Carol. fig4 shows this rule-based dynamic; CFR-driven personality learning is shown in fig1 (OCEAN traits) and fig2 (cumulative regret).

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

Defaults: `alpha=0.6`, `beta=0.3`, `gamma=0.2` (override at run time via `-Palpha=X`). The 10-seed × 2000-episode results above were produced at these defaults.

The α coefficient sweep `{0.4, 0.6, 1.0, 1.5}` is reported in `results/alpha/figD_alpha_sensitivity.png` and `results/alpha/figE_OCEAN_alpha_sensitivity.png` — phase-transition timing scales with α, but the equilibrium location in trait space is α-invariant.

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

**Generate the four publication figures** (each reads from `results/seed_*/` and writes into themed subfolders):

```bash
python scripts/plot_paper_figures.py     # fig1 (OCEAN x4 agents) -> results/ocean/
                                          # fig2 (per-agent x per-context regret) -> results/regret/
python scripts/plot_reciprocity.py       # fig4 (rule-based reciprocity) -> results/reciprocity/
python scripts/plot_alpha_sweep.py       # figD + figE -> results/alpha/
```

All scripts use the **CFR iteration** convention on the X-axis (`t = episode × 30`).

**TensorBoard view** (per-seed traces + cross-seed mean/std):

```bash
python scripts/log_multiseed_tensorboard.py
tensorboard --logdir runs/multiseed --port 6006
# open http://127.0.0.1:6006/
```

**Output CSVs written per seed:**

| File | Resolution | Contents |
|---|---|---|
| `personality_evolution.csv` | per-episode | Alice OCEAN + mood + total reward |
| `carol_personality_evolution.csv` | per-episode | Carol OCEAN |
| `cfr_regrets.csv` | per-episode | Alice cumulative regrets (9 actions) |
| `carol_cfr_regrets.csv` | per-episode | Carol cumulative regrets (help / decline / reciprocate) |
| `cfr_trace.csv` | **per-iteration** | Alice's full CFR trace: $t$, episode, person, action, reward, all 9 cumulative regrets — one row per CFR iteration |
| `carol_cfr_trace.csv` | **per-iteration** | Carol's full CFR trace: $t$, episode, action, reward, 3 cumulative regrets |
| `adapted_reciprocity.csv` | per-episode | Bob / Carol / Dave adapted + innate ratios, Carol observed ratio, Carol exploitation flag |

---

## Repository structure

```
vesna-pro/
  src/agt/                                         BDI sources (Java + AgentSpeak)
  src/env/                                         JaCaMo environment artifacts
  scripts/
    plot_paper_figures.py                          fig1 (4-agent OCEAN) + fig2 (per-agent regret)
    plot_reciprocity.py                            fig4 (rule-based reciprocity, non-CFR)
    plot_alpha_sweep.py                            figD + figE (alpha sensitivity)
    log_multiseed_tensorboard.py                   writes runs/multiseed/{seed_NN, mean, std}/
    run_alpha_sweep.sh                             4 alphas x 5 seeds, 2000 ep each
  tests/
    run_10_seeds.sh                                10-seed batch runner (seeds 0..9, 2000 ep)
  results/
    seed_0..9/                                     per-seed CSV outputs of the 10-seed run
    ocean/                                         OCEAN trait figures
      fig1_personality_4agents.png                 (4-agent OCEAN over 60 000 iterations)
    regret/                                        per-agent, per-context cumulative CFR regret
      fig2_regret_per_agent.png                    2x2: Alice vs Bob/Carol/Dave + Carol vs Alice
    reciprocity/                                   rule-based reciprocity (non-CFR mechanism)
      fig4_adaptive_reciprocity.png
    alpha/                                         alpha sensitivity sweep
      alpha_0_4/, alpha_0_6/, alpha_1_0/, alpha_1_5/   per-alpha CSV outputs
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
