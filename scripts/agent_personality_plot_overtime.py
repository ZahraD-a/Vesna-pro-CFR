#!/usr/bin/env python3
"""Per-agent OCEAN personality trajectories over CFR iterations.

Reads results/seed_<n>/personality_evolution.csv (Alice) and
results/seed_<n>/carol_personality_evolution.csv (Carol), plus
hardcoded static stances for Bob and Dave from HelpScenarioConfig.

Produces:
    results/ocean/agent_personality_plot_overtime.png
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

OCEAN = ["openness", "conscientiousness", "extraversion",
         "agreeableness", "neuroticism"]
OCEAN_LABELS = {
    "openness": "O", "conscientiousness": "C", "extraversion": "E",
    "agreeableness": "A", "neuroticism": "N",
}
OCEAN_COLORS = {
    "openness":          "#7D3C98",
    "conscientiousness": "#27AE60",
    "extraversion":      "#E67E22",
    "agreeableness":     "#1F3A93",
    "neuroticism":       "#B22222",
}
OCEAN_MARKERS = {
    "openness":          "^",
    "conscientiousness": "o",
    "extraversion":      "s",
    "agreeableness":     "D",
    "neuroticism":       "v",
}
N_MARKERS = 11

BOB_HELP_STANCE  = {"openness": -0.2, "conscientiousness":  0.4,
                    "extraversion":  0.0, "agreeableness":   0.6,
                    "neuroticism":  -0.4}
DAVE_HELP_STANCE = {"openness":  0.4, "conscientiousness":  0.01,
                    "extraversion":  0.2, "agreeableness":   0.0,
                    "neuroticism":  -0.8}


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
    out = {}
    for key, fname in [("alice", "personality_evolution.csv"),
                       ("carol", "carol_personality_evolution.csv")]:
        p = seed_dir / fname
        if p.exists():
            df = pd.read_csv(p)
            df["episode"] = pd.to_numeric(df["episode"], errors="coerce")
            df = df.dropna(subset=["episode"]).astype({"episode": int})
            out[key] = df.sort_values("episode")
    return out


def stack_on_grid(per_seed, df_key, value_col, grid):
    rows = []
    for d in per_seed.values():
        df = d.get(df_key)
        if df is None or value_col not in df.columns:
            continue
        rows.append(np.interp(grid,
                              df["episode"].to_numpy(),
                              df[value_col].to_numpy(dtype=float)))
    return np.vstack(rows) if rows else None


def smooth(arr, window=21):
    if arr is None or len(arr) < window:
        return arr
    return pd.Series(arr).rolling(window, min_periods=1, center=True).median().to_numpy()


def panel_dynamic(ax, per_seed, df_key, col_for, grid, title):
    x = grid * ITER_PER_EP
    markevery = max(1, len(x) // N_MARKERS)
    for trait in OCEAN:
        s = stack_on_grid(per_seed, df_key, col_for(trait), grid)
        if s is None:
            continue
        m  = smooth(s.mean(axis=0))
        sd = smooth(s.std(axis=0))
        c  = OCEAN_COLORS[trait]
        ax.plot(x, m, color=c, linewidth=1.4,
                marker=OCEAN_MARKERS[trait], markersize=6,
                markevery=markevery, markerfacecolor=c,
                markeredgecolor=c, label=OCEAN_LABELS[trait])
        ax.fill_between(x, m - sd, m + sd, color=c, alpha=0.10, linewidth=0)
    ax.axhline(0.0, color="grey", linewidth=0.5, linestyle="--")
    ax.set_xlabel(r"CFR iteration  $t$")
    ax.set_ylabel("Trait value")
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(title, fontsize=12)
    style_ax(ax)


def panel_static(ax, stance, grid, title):
    x = grid * ITER_PER_EP
    markevery = max(1, len(x) // N_MARKERS)
    for trait in OCEAN:
        v = stance[trait]
        c = OCEAN_COLORS[trait]
        ax.plot(x, np.full_like(x, v, dtype=float),
                color=c, linewidth=1.4,
                marker=OCEAN_MARKERS[trait], markersize=6,
                markevery=markevery, markerfacecolor=c,
                markeredgecolor=c, label=OCEAN_LABELS[trait])
    ax.axhline(0.0, color="grey", linewidth=0.5, linestyle="--")
    ax.set_xlabel(r"CFR iteration  $t$")
    ax.set_ylabel("Trait value")
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(title, fontsize=12)
    style_ax(ax)


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    per_seed = {s: load_seed(d) for s, d in seeds.items()}

    max_eps = []
    for d in per_seed.values():
        for key in ("alice", "carol"):
            df = d.get(key)
            if df is not None and "episode" in df.columns and len(df):
                max_eps.append(int(df["episode"].max()))
    n_eps = min(max_eps) if max_eps else 0
    grid  = np.arange(1, n_eps + 1)

    print(f"Loaded {len(per_seed)} seeds: {n_eps} episodes.")

    fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.6),
                             sharex=True, sharey=True)
    fig.suptitle("Per-agent OCEAN personality "
                 f"(mean $\\pm$ std across {len(per_seed)} seeds, "
                 f"{grid[-1] * ITER_PER_EP} CFR iterations)",
                 fontsize=14, fontweight="bold")

    panel_dynamic(axes[0, 0], per_seed, "alice", lambda t: t,          grid, "Alice (CFR)")
    panel_static (axes[0, 1], BOB_HELP_STANCE,                         grid, "Bob (static)")
    panel_dynamic(axes[1, 0], per_seed, "carol", lambda t: f"carol_{t}", grid, "Carol (CFR)")
    panel_static (axes[1, 1], DAVE_HELP_STANCE,                        grid, "Dave (static)")

    handles = [
        Line2D([0], [0], color=OCEAN_COLORS[t], linewidth=1.4,
                   marker=OCEAN_MARKERS[t], markersize=7,
                   markerfacecolor=OCEAN_COLORS[t],
                   markeredgecolor=OCEAN_COLORS[t],
                   label=OCEAN_LABELS[t])
        for t in OCEAN
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5,
               frameon=False, fontsize=11, columnspacing=2.4,
               handlelength=2.0, bbox_to_anchor=(0.5, -0.01))

    plt.tight_layout(rect=(0, 0.04, 1, 1))
    out = OUT / "agent_personality_plot_overtime.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
