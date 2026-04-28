#!/usr/bin/env python3
"""Mood vs Personality over time.

Mood (stress, satisfaction, social_energy) resets each episode and reflects
immediate emotional reactions to plan execution. Personality (OCEAN traits)
drifts slowly via CFR and captures long-term character change.

This plot shows both on the same time axis so the contrast between the two
timescales is visible: mood fluctuates episode to episode while personality
trends steadily across hundreds of episodes.

Reads results/seed_<n>/personality_evolution.csv

Produces:
    results/ocean/mood_vs_personality.png
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT    = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT     = RESULTS / "ocean"
OUT.mkdir(parents=True, exist_ok=True)

ITER_PER_EP = 30
N_MARKERS   = 11

PERSONALITY_TRAITS = ["openness", "conscientiousness", "extraversion",
                      "agreeableness", "neuroticism"]
MOOD_TRAITS        = ["stress", "satisfaction", "social_energy"]

PERSONALITY_COLORS = {
    "openness":          "#7D3C98",
    "conscientiousness": "#27AE60",
    "extraversion":      "#E67E22",
    "agreeableness":     "#1F3A93",
    "neuroticism":       "#B22222",
}
MOOD_COLORS = {
    "stress":        "#E74C3C",
    "satisfaction":  "#2ECC71",
    "social_energy": "#3498DB",
}
PERSONALITY_MARKERS = {
    "openness": "^", "conscientiousness": "o", "extraversion": "s",
    "agreeableness": "D", "neuroticism": "v",
}
MOOD_MARKERS = {
    "stress": "x", "satisfaction": "+", "social_energy": "*",
}
PERSONALITY_LABELS = {
    "openness": "O", "conscientiousness": "C", "extraversion": "E",
    "agreeableness": "A", "neuroticism": "N",
}
MOOD_LABELS = {
    "stress":        "Stress (unused — no plan carries a stress effect)",
    "satisfaction":  "Satisfaction",
    "social_energy": "Social Energy",
}


def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)


def collect_seeds():
    out = {}
    for d in sorted(RESULTS.glob("seed_*")):
        try:
            s = int(d.name.split("_")[1])
        except (IndexError, ValueError):
            continue
        out[s] = d
    return out


def load_seed(seed_dir):
    p = seed_dir / "personality_evolution.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df["episode"] = pd.to_numeric(df["episode"], errors="coerce")
    df = df.dropna(subset=["episode"]).astype({"episode": int})
    return df.sort_values("episode")


def smooth(arr, window=21):
    if arr is None or len(arr) < window:
        return arr
    return pd.Series(arr).rolling(window, min_periods=1, center=True).median().to_numpy()


def stack(per_seed, col, grid):
    rows = []
    for df in per_seed.values():
        if df is None or col not in df.columns:
            continue
        rows.append(np.interp(grid,
                              df["episode"].to_numpy(),
                              df[col].to_numpy(dtype=float)))
    return np.vstack(rows) if rows else None


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    per_seed = {s: load_seed(d) for s, d in seeds.items()}
    per_seed = {s: df for s, df in per_seed.items() if df is not None}

    max_eps = max(int(df["episode"].max()) for df in per_seed.values())
    grid    = np.arange(1, max_eps + 1)
    x       = grid * ITER_PER_EP
    markevery = max(1, len(x) // N_MARKERS)

    print(f"Loaded {len(per_seed)} seeds: {max_eps} episodes.")

    fig, (ax_pers, ax_mood) = plt.subplots(2, 1, figsize=(12, 9),
                                            sharex=True)
    fig.suptitle("Personality (slow drift) vs Mood (fast fluctuation)\n"
                 f"mean ± std across {len(per_seed)} seeds, "
                 f"{max_eps * ITER_PER_EP} CFR iterations",
                 fontsize=13, fontweight="bold")

    for trait in PERSONALITY_TRAITS:
        s = stack(per_seed, trait, grid)
        if s is None:
            continue
        m  = smooth(s.mean(axis=0))
        sd = smooth(s.std(axis=0))
        c  = PERSONALITY_COLORS[trait]
        mk = PERSONALITY_MARKERS[trait]
        ax_pers.plot(x, m, color=c, linewidth=1.4,
                     marker=mk, markersize=6, markevery=markevery,
                     markerfacecolor=c, markeredgecolor=c,
                     label=PERSONALITY_LABELS[trait])
        ax_pers.fill_between(x, m - sd, m + sd, color=c, alpha=0.10, linewidth=0)

    ax_pers.axhline(0.0, color="grey", linewidth=0.5, linestyle="--")
    ax_pers.set_ylabel("Trait value")
    ax_pers.set_ylim(-1.05, 1.05)
    ax_pers.set_title("Personality (OCEAN) — updated once per episode via CFR gradient",
                      fontsize=11)
    ax_pers.legend(loc="upper right", fontsize=9, frameon=False,
                   ncol=5, handlelength=1.5)
    style_ax(ax_pers)

    for trait in MOOD_TRAITS:
        s = stack(per_seed, trait, grid)
        if s is None:
            continue
        # No smoothing for mood — it should appear noisy, showing episode-to-episode
        # fluctuation that results from stochastic plan selection within each episode.
        m  = s.mean(axis=0)
        sd = s.std(axis=0)
        c  = MOOD_COLORS[trait]
        mk = MOOD_MARKERS[trait]
        ax_mood.plot(x, m, color=c, linewidth=0.8,
                     marker=mk, markersize=5, markevery=markevery,
                     markerfacecolor=c, markeredgecolor=c,
                     label=MOOD_LABELS[trait])
        ax_mood.fill_between(x, m - sd, m + sd, color=c, alpha=0.15, linewidth=0)

    ax_mood.axhline(0.0, color="grey", linewidth=0.5, linestyle="--")
    ax_mood.set_ylabel("Trait value")
    ax_mood.set_xlabel(r"CFR iteration  $t$")
    ax_mood.set_ylim(-1.05, 1.05)
    ax_mood.set_title("Mood (stress, satisfaction, social energy) — updated after every plan execution, reset each episode",
                      fontsize=11)
    ax_mood.legend(loc="lower right", fontsize=9, frameon=False,
                   ncol=3, handlelength=1.5)
    style_ax(ax_mood)

    plt.tight_layout()
    out = OUT / "mood_vs_personality.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
