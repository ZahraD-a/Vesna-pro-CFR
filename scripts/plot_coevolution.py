#!/usr/bin/env python3
"""Alice and Carol personality co-evolution — 6-panel figure.

Reads the CSVs produced by a single training run and produces a figure
that shows, side by side:

    (a) Alice's OCEAN evolution                   (b) Carol's OCEAN evolution
    (c) Agreeableness crossover (Alice vs Carol)
    (d) Alice's cumulative regret per Carol-plan  (e) Carol's cumulative regret
    (f) Carol's reciprocity adaptation

All OCEAN traits are plotted on the [-1, +1] range used by Pro-AgentSpeak(L).
"""

import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Resolve paths relative to the project root so the script works whether it's
# invoked from the root or from inside the scripts/ directory.
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "coevolution_1000ep.png"
os.makedirs(OUT.parent, exist_ok=True)

alice      = pd.read_csv(ROOT / "personality_evolution.csv")
carol      = pd.read_csv(ROOT / "carol_personality_evolution.csv")
alice_reg  = pd.read_csv(ROOT / "cfr_regrets.csv")
carol_reg  = pd.read_csv(ROOT / "carol_cfr_regrets.csv")
adapt      = pd.read_csv(ROOT / "adapted_reciprocity.csv")

traits       = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
trait_labels = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
colors       = ["#E74C3C", "#27AE60", "#3498DB", "#F39C12", "#9B59B6"]

carol_col = {t: f"carol_{t}" for t in traits}

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle(
    "Alice and Carol Co-Evolution via CFR Regret Matching (1000 episodes, trait range [-1, +1])",
    fontsize=14, fontweight="bold", y=0.995,
)

# (a) Alice's OCEAN evolution
ax = axes[0, 0]
for trait, label, c in zip(traits, trait_labels, colors):
    ax.plot(alice["episode"], alice[trait], label=label, color=c, linewidth=2, alpha=0.85)
ax.axhline(0.0, color="grey", linestyle=":", alpha=0.5)
ax.set_title("(a) Alice -- OCEAN evolution", fontweight="bold")
ax.set_xlabel("Episode"); ax.set_ylabel("Trait value")
ax.set_ylim(-1, 1); ax.grid(True, alpha=0.3)
ax.legend(loc="center right", fontsize=8)

# (b) Carol's OCEAN evolution
ax = axes[0, 1]
for trait, label, c in zip(traits, trait_labels, colors):
    col = carol_col[trait]
    if col in carol.columns:
        ax.plot(carol["episode"], carol[col], label=label, color=c, linewidth=2, alpha=0.85)
ax.axhline(0.0, color="grey", linestyle=":", alpha=0.5)
ax.set_title("(b) Carol -- OCEAN evolution", fontweight="bold")
ax.set_xlabel("Episode"); ax.set_ylabel("Trait value")
ax.set_ylim(-1, 1); ax.grid(True, alpha=0.3)
ax.legend(loc="center right", fontsize=8)

# (c) Agreeableness crossover
ax = axes[0, 2]
ax.plot(alice["episode"], alice["agreeableness"],
        label="Alice Agreeableness", color="#2980B9", linewidth=2.4)
ax.plot(carol["episode"], carol[carol_col["agreeableness"]],
        label="Carol Agreeableness", color="#C0392B", linewidth=2.4)
ax.axhline(0.0, color="grey", linestyle=":", alpha=0.6)
ax.set_title("(c) Agreeableness crossover -- Alice vs Carol", fontweight="bold")
ax.set_xlabel("Episode"); ax.set_ylabel("Agreeableness")
ax.set_ylim(-1, 1); ax.grid(True, alpha=0.3)
ax.legend(loc="best", fontsize=9)

# (d) Alice's cumulative regret per Carol-plan
ax = axes[1, 0]
for col, label, c in [
    ("help_alice",    "help_alice (help Carol)",      "#27AE60"),
    ("decline_alice", "decline_alice (decline)",      "#E74C3C"),
    ("teach_alice",   "teach_alice (mentor)",         "#F39C12"),
]:
    if col in alice_reg.columns:
        ax.plot(alice_reg["episode"], alice_reg[col], label=label,
                color=c, linewidth=1.8, alpha=0.9)
ax.axhline(0.0, color="grey", linestyle="--", alpha=0.6)
ax.set_title("(d) Alice -- cumulative regret vs Carol", fontweight="bold")
ax.set_xlabel("Episode"); ax.set_ylabel("Cumulative regret")
ax.grid(True, alpha=0.3); ax.legend(loc="best", fontsize=9)

# (e) Carol's cumulative regret
ax = axes[1, 1]
for col, label, c in [
    ("carol_help_regret",        "help (reciprocate Alice)", "#27AE60"),
    ("carol_decline_regret",     "decline",                  "#E74C3C"),
    ("carol_reciprocate_regret", "reciprocate",              "#3498DB"),
]:
    if col in carol_reg.columns:
        ax.plot(carol_reg["episode"], carol_reg[col], label=label,
                color=c, linewidth=1.8, alpha=0.9)
ax.axhline(0.0, color="grey", linestyle="--", alpha=0.6)
ax.set_title("(e) Carol -- cumulative regret vs Alice", fontweight="bold")
ax.set_xlabel("Episode"); ax.set_ylabel("Cumulative regret")
ax.grid(True, alpha=0.3); ax.legend(loc="best", fontsize=8)

# (f) Reciprocity adaptation
ax = axes[1, 2]
if "carol_adapted" in adapt.columns:
    ax.plot(adapt["episode"], adapt["carol_adapted"],
            label="Carol adapted reciprocity", color="#C0392B", linewidth=2.2)
if "carol_observed_ratio" in adapt.columns:
    ax.plot(adapt["episode"], adapt["carol_observed_ratio"],
            label="Observed cooperation ratio",
            color="#2980B9", linewidth=1.8, linestyle="--", alpha=0.85)
ax.axhline(0.5, color="grey", linestyle=":", alpha=0.5)
ax.set_title("(f) Carol -- reciprocity adaptation", fontweight="bold")
ax.set_xlabel("Episode"); ax.set_ylabel("Reciprocity")
ax.set_ylim(0, 1); ax.grid(True, alpha=0.3)
ax.legend(loc="best", fontsize=9)

plt.tight_layout()
plt.savefig(OUT, dpi=200, bbox_inches="tight")
print(f"Saved: {OUT}")


def endpoint_summary(df, columns, title):
    df = df.sort_values("episode")
    first, last = df.iloc[0], df.iloc[-1]
    print(f"\n=== {title} ===")
    print(f"{'Trait':<22}{'Start':>10}{'End':>10}{'Delta':>10}")
    for col, label in columns:
        s, e = float(first[col]), float(last[col])
        print(f"{label:<22}{s:>+10.3f}{e:>+10.3f}{e - s:>+10.3f}")


endpoint_summary(alice,
                 [(t, t.capitalize()) for t in traits],
                 "Alice (1000 episodes)")
endpoint_summary(carol,
                 [(carol_col[t], t.capitalize()) for t in traits],
                 "Carol (1000 episodes)")
