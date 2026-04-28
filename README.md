# Vesna-Pro-CFR: Learning Social Personalities via Counterfactual Regret

This repository implements **experience-driven propensity learning** for BDI agents, extending Pro-AgentSpeak(L) with Counterfactual Regret Minimization so that personality traits evolve from interaction history rather than staying fixed at design time.

## Table of Contents

- [1.0 Abstract](#10-abstract)
- [1.1 Mathematical Notation](#11-mathematical-notation)
- [1.2 Introduction](#12-introduction)
- [2.0 Background](#20-background)
- [2.1 AgentSpeak(L) and Pro-AgentSpeak(L)](#21-agentspeakl-and-pro-agentspeakl)
- [2.2 Counterfactual Regret Minimization](#22-counterfactual-regret-minimization)
- [3.0 Methodology](#30-methodology)
- [3.1 Personality Learning Loop](#31-personality-learning-loop)
- [3.2 Design Choices](#32-design-choices)
- [4.0 Experiments](#40-experiments)
- [4.1 Installation](#41-installation)
- [4.2 How to Run](#42-how-to-run)
- [4.3 Results](#43-results)
- [4.4 Discussion](#44-discussion)
- [4.5 Future Work](#45-future-work)
- [5.0 Conclusion](#50-conclusion)
- [6.0 References](#60-references)

## 1.0 Abstract

Pro-AgentSpeak(L) equips BDI agents with personality traits that guide plan selection through compatibility measures. However, personality remains static, fixed at design time, which limits agent adaptation across long-horizon, non-stationary interactions. This work introduces experience-driven propensity learning by extending Pro-AgentSpeak(L) with Counterfactual Regret Minimization (CFR). The agent accumulates regret across repeated decision cycles per context, projecting that regret onto its personality vector. Propensities drift toward the dispositions that past experience consistently favoured, while the compatibility-based selection mechanism operates unchanged on the evolved profile. An empirical case study using a workplace scenario with three colleagues of different reciprocity structures shows that learned propensities yield coherent, stable, and context-specialised behaviour emerging purely from regret accumulation without any explicit programming.

## 1.1 Mathematical Notation

The agent maintains an immutable personality vector and a mutable mood vector, both in $[-1, +1]^d$:

$$A_t : \mathcal{P}r \longrightarrow [-1, +1]$$

Plan selection uses the dot-product compatibility measure:

$$\text{Compat}_{\bullet}(A_t, A_p) = \frac{1}{2|\mathcal{P}r_p|} \left( \sum_{pr \in \mathcal{P}r_p} A_t(pr) \cdot A_p(pr) + |\mathcal{P}r_p| \right)$$

Instantaneous counterfactual regret for each unchosen plan $p'$:

$$\text{reg}_t(I_\kappa, p') = \hat{v}(I_\kappa, p') - \hat{v}(I_\kappa, p)$$

Regret-matching weight expressing how strongly experience attests plan $p$ was the right choice:

$$\sigma_\kappa(p) = \frac{[R^T(I_\kappa, p)]^+}{\sum_{p' \in I_\kappa} [R^T(I_\kappa, p')]^+}$$

Personality gradient across all contexts and plans:

$$\nabla_T(pr) = \sum_{\kappa \in \mathcal{K}} \sum_{p \in I_\kappa} \sigma_\kappa(p) \cdot \bigl(A_p(pr) - A_t(pr)\bigr)$$

Personality update at episode boundary:

$$A_{t+1}(pr) = \text{clip}\bigl(A_t(pr) + \eta \cdot \nabla_T(pr)\bigr), \quad pr \in \mathcal{P}r_{\text{immute}}$$

## 1.2 Introduction

Alice shares an office with three colleagues. Bob is a senior developer, demanding but fair, who reciprocates when Alice invests in his work. Carol is a junior developer who asks often and rarely gives back. Dave is a product manager who is generous with recognition and always reciprocates.

In standard Pro-AgentSpeak(L), Alice's personality is fixed at design time. She would help Carol indefinitely even as Carol exploits her, because her agreeableness never changes. This work changes that: by accumulating regret over which plans she wishes she had chosen, Alice's personality gradually shifts. After many episodes, she treats Dave warmly, stays balanced with Bob, and sets boundaries with Carol, not because she was programmed to, but because experience shaped her propensities.

The mechanism is deliberately general. It applies to any BDI agent whose plans carry propensity annotations and whose decision points can be partitioned into observable contexts. The plan library, compatibility measure, mood post-effects, and BDI reasoning cycle from Pro-AgentSpeak(L) remain untouched. Only the immutable personality ceases to be a design-time constant.

## 2.0 Background

### 2.1 AgentSpeak(L) and Pro-AgentSpeak(L)

AgentSpeak(L) is a logic programming language for BDI agents interpreted by the Jason platform. Plans have the form:

```
p ::= te : ctxt <- h
```

where `te` is a triggering event, `ctxt` is a context guard checked against the belief base, and `h` is the plan body.

**Pro-AgentSpeak(L)** (Gatti et al., 2026) extends this by annotating plans with OCEAN personality weights:

```prolog
@help_alice[temper([agreeableness(0.8), conscientiousness(0.2), ...])]
+!choose_alice_response_to_carol : true <- +strategy(help_alice).
```

The agent's personality vector $A_t \in [-1,+1]^5$ is scored against each applicable plan's annotation via the compatibility measure. The plan with the highest compatibility score is most likely to be selected. Mood (mutable propensities) updates after each plan execution via post-effects; personality (immutable propensities) stays fixed until this work.

**OCEAN traits** used throughout:

| Letter | Trait |
|---|---|
| O | Openness |
| C | Conscientiousness |
| E | Extraversion |
| A | Agreeableness |
| N | Neuroticism |

### 2.2 Counterfactual Regret Minimization

CFR (Zinkevich et al., 2008) decomposes global regret into per-information-set regrets and applies regret matching independently at each one. The average strategy converges to an $\varepsilon$-Nash equilibrium in two-player zero-sum games at rate $O(1/\sqrt{T})$.

This work borrows two properties from CFR:

1. **Per-information-set regret:** the same algorithm learns context-sensitive behaviour when different decision situations are placed in different information sets.
2. **Regret-matching weights:** instead of using these weights to construct a mixed strategy over actions as in standard CFR, we use them to weight a gradient on the personality vector.

The regret baseline used here differs from canonical CFR. Instead of comparing unchosen actions against the expected value of the current mixed strategy $v(\sigma_t)$, we compare against the running-average value of the action actually taken. This makes the estimator stable under non-stationarity, which matters here because Carol's reciprocity adapts in response to Alice's behaviour.

## 3.0 Methodology

### 3.1 Personality Learning Loop

At each reasoning cycle the agent:

1. Observes the current decision context $\kappa \in \mathcal{K} = \{\text{bob}, \text{carol}, \text{dave}\}$
2. Selects a plan via Pro-AgentSpeak(L)'s $S_{Ap}$ using current personality $A_t$
3. Executes the plan and observes the outcome
4. Computes a shaped reward: $r = r_{\text{base}} + \psi(p, \kappa, T(\kappa))$
5. Updates the running-mean reward $\hat{v}(I_\kappa, p)$ and cumulative regret $R^T(I_\kappa, \cdot)$

At each episode boundary:

6. Computes regret-matching weights $\sigma_\kappa(p)$ for all contexts and plans
7. Computes the personality gradient $\nabla_T(pr)$ for each immutable trait
8. Updates personality: $A_{t+1}(pr) = \text{clip}(A_t(pr) + \eta \cdot \nabla_T(pr))$

**Two learning agents:**

| Agent | CFR type | Starts at | Adapts via |
|---|---|---|---|
| Alice | Self-CFR (60,000 iterations) | $(0,0,0,0,0)$ neutral | Own plan regrets across all 3 contexts |
| Carol | Observational CFR (20,000 iterations) | $A=-0.4$ exploitative | Regret over Alice's actions toward her |

**Two static partners:**

| Agent | Reciprocity | Adapts via |
|---|---|---|
| Bob | innate 0.40 | Rule-based `adaptedReciprocity` only |
| Dave | innate 0.90 | Rule-based `adaptedReciprocity` only |

### 3.2 Design Choices

1. **Dot-product compatibility:** favours polarity alignment between agent personality and plan annotation, tolerant of magnitude differences.
2. **COMA-style counterfactual baseline:** running-mean reward per action rather than $v(\sigma_t)$, stable under Carol's non-stationary reciprocity.
3. **Reward shaping:** potential-based shaping amplifies the contrast between contexts without changing the optimal policy.

```
r_enhanced = r_base
           + alpha * (reciprocity - 0.5)           # reciprocity signal
           + beta  * 1[decline AND exploitative]   # boundary-setting reward
           + gamma * (relationship - 0.5)          # relationship potential
```

Defaults: `alpha=0.6`, `beta=0.3`, `gamma=0.2`.

4. **Two timescales:** mood post-effects fire after every plan execution (fast); personality gradient updates fire only at episode end (slow). This separation prevents transient noise from destabilising long-term character.
5. **Action naming convention:** all action names follow `actor_verb_recipient` (e.g. `alice_help_carol`, `carol_reciprocate_alice`) so directionality is always explicit in the code.

## 4.0 Experiments

### 4.1 Installation

**Requirements:** Java 21, Python 3.10+

```bash
# Clone the repository
git clone https://github.com/ZahraD-a/Vesna-pro-CFR.git
cd Vesna-pro-CFR

# Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows

pip install numpy pandas matplotlib
```

### 4.2 How to Run

**Single run** (seed 0, 2000 episodes):

```bash
./gradlew run
```

**Full 10-seed experiment** (~5 min per seed):

```bash
bash tests/run_10_seeds.sh
```

**Debug mode** (attach Cursor/VS Code debugger on port 5005):

```bash
./gradlew debugRun
# then press F5 in Cursor and select "Attach to Vesna (port 5005)"
```

**Generate figures:**

```bash
# Per-agent OCEAN personality trajectories
python scripts/agent_personality_plot_overtime.py

# Alice self-CFR regret (Bob, Carol, Dave contexts)
python scripts/regret_per_agent.py

# Carol observational CFR regret (standalone)
python scripts/carol_vs_alice_cfr.py

# Rule-based reciprocity dynamics (Bob and Dave)
python scripts/plot_reciprocity.py

# Alpha sensitivity sweep
python scripts/plot_alpha_sweep.py
```

**Output CSVs per seed:**

| File | Resolution | Contents |
|---|---|---|
| `personality_evolution.csv` | per-episode | Alice OCEAN + mood + total reward |
| `carol_personality_evolution.csv` | per-episode | Carol OCEAN |
| `cfr_regrets.csv` | per-episode | Alice cumulative regrets (9 actions) |
| `carol_cfr_regrets.csv` | per-episode | Carol cumulative regrets (3 actions) |
| `cfr_trace.csv` | per-iteration | Alice full trace: $t$, episode, person, action, reward, 9 regrets |
| `carol_cfr_trace.csv` | per-iteration | Carol full trace: $t$, episode, action, reward, 3 regrets |
| `adapted_reciprocity.csv` | per-episode | Per-colleague reciprocity dynamics |

### 4.3 Results

Key results across 10 seeds × 2000 episodes (60,000 CFR iterations for Alice):

| Quantity | Start | End (mean ± std) |
|---|---|---|
| Alice Agreeableness | 0.00 | +0.26 ± 0.10 |
| Alice Neuroticism | 0.00 | -0.62 ± 0.03 |
| Carol Agreeableness | -0.40 | +0.36 ± 0.009 |
| Carol Neuroticism | 0.00 | -0.51 ± 0.002 |
| Carol adapted reciprocity | 0.10 | 0.61 ± 0.07 |
| Carol exploitative flag deactivation | n/a | episode 47 ± 42 |
| Alice P(decline given Carol) | ~0.91 | ~0.12 |

**Alice's personality trajectory:**
- Agreeableness rises toward Dave (consistently reciprocal) and stabilises with Bob (fair)
- Conscientiousness rises toward Carol (exploitative early on), with professional boundaries emerging
- Neuroticism drops sharply across all contexts as stable, low-variance plan selections are preferred

**Carol co-evolves:** starting exploitative (A = -0.4), Carol's agreeableness rises to +0.36 as Alice's declining behaviour trains her toward reciprocation. The cooperative equilibrium is not programmed; it emerges from two agents learning simultaneously.

### 4.4 Discussion

The asymmetry between Alice and Carol is intentional. Alice runs self-CFR: she optimises her own utility over her plan space. Carol runs observational CFR: she attributes responses to Alice's actions and adjusts her reciprocity accordingly. This produces the social-trust-reversal dynamic where Carol transitions from exploitative to cooperative once Alice's declining rate drops below a threshold.

Bob and Dave provide stable reference points. Bob's moderate reciprocity keeps Alice balanced; Dave's high reciprocity reinforces cooperative plans. Neither runs CFR; their behaviour is governed by a simple hand-coded rule that nudges `adaptedReciprocity` proportionally based on Alice's decisions.

The regret update is not canonical CFR. The setting violates the two-player zero-sum assumption: the game is general-sum, Carol is non-stationary, and action selection follows BDI personality-similarity rather than regret matching. The convergence target here is no-regret stationarity in personality space, a stable mutual best-response, not Nash equilibrium.

### 4.5 Future Work

1. Extend to more than three colleagues with different social archetypes.
2. Explore curriculum learning: start with static partners and introduce adaptive ones gradually.
3. Apply to non-social domains such as navigation, resource allocation, and negotiation.
4. Investigate transfer: can a personality learned in one social environment generalise to another?
5. Replace the hand-coded reward shaping with a learned potential function.

## 5.0 Conclusion

This work shows that BDI personality and data-driven learning can be combined cleanly. By projecting counterfactual regret onto the OCEAN trait space rather than onto action probabilities, the agent develops a believable social character that emerges purely from interaction history. The plan library, reasoning cycle, and compatibility measure from Pro-AgentSpeak(L) remain unchanged; only the personality they operate on becomes dynamic.

The office scenario demonstrates that coherent, context-specialised social behaviour arises without explicit programming. Alice learns to cooperate with Dave, stay balanced with Bob, and set limits with Carol, all from a neutral starting point, through 2,000 episodes of repeated interaction.

## 6.0 References

| ID | Reference |
|---|---|
| [1] | Gatti, A., Mascardi, V., Ferrando, A., Stucchi, A. (2026). *VEsNA-Pro: Exploiting BDI Agents with Propensities for Emergent Narrative*. AAMAS 2026. |
| [2] | Zinkevich, M., Johanson, M., Bowling, M., Piccione, C. (2008). *Regret Minimization in Games with Incomplete Information*. NeurIPS. |
| [3] | Hart, S., Mas-Colell, A. (2000). *A Simple Adaptive Procedure Leading to Correlated Equilibrium*. Econometrica 68(5). |
| [4] | Foerster, J. et al. (2018). *Counterfactual Multi-Agent Policy Gradients*. AAAI. |
| [5] | Rao, A. S. (1996). *AgentSpeak(L): BDI Agents Speak Out in a Logical Computable Language*. MAAMAW. |
| [6] | Bordini, R. H., Hübner, J. F., Wooldridge, M. (2007). *Programming Multi-Agent Systems in AgentSpeak using Jason*. Wiley. |
| [7] | Ng, A., Harada, D., Russell, S. (1999). *Policy Invariance Under Reward Transformations*. ICML. |
| [8] | McCrae, R. R., John, O. P. (1992). *An Introduction to the Five-Factor Model and Its Applications*. Journal of Personality 60(2). |
| [9] | Bowling, M. et al. (2015). *Heads-up Limit Hold'em Poker is Solved*. Science 347(6218). |
