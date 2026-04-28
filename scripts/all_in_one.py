#!/usr/bin/env python3
"""All-in-one figure: 4-agent OCEAN + mood in one layout.

Layout (5 panels):
  Row 1: Alice (CFR)  |  Bob (static)
  Row 2: Carol (CFR)  |  Dave (static)
  Row 3: Mood (full width) — satisfaction, social energy, stress

Produces:
    results/ocean/all_in_one.png
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D

ROOT    = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT     = RESULTS / "ocean"
OUT.mkdir(parents=True, exist_ok=True)

ITER_PER_EP = 30
N_MARKERS   = 11

OCEAN        = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
OCEAN_LABELS = {"openness": "O", "conscientiousness": "C", "extraversion": "E",
                "agreeableness": "A", "neuroticism": "N"}
OCEAN_COLORS = {
    "openness":          "#7D3C98",
    "conscientiousness": "#27AE60",
    "extraversion":      "#E67E22",
    "agreeableness":     "#1F3A93",
    "neuroticism":       "#B22222",
}
OCEAN_MARKERS = {
    "openness": "^", "conscientiousness": "o", "extraversion": "s",
    "agreeableness": "D", "neuroticism": "v",
}

MOOD_TRAITS  = ["stress", "satisfaction", "social_energy"]
MOOD_LABELS  = {"stress": "Stress (unused)", "satisfaction": "Satisfaction",
                "social_energy": "Social Energy"}
MOOD_COLORS  = {"stress": "#E74C3C", "satisfaction": "#2ECC71", "social_energy": "#3498DB"}
MOOD_MARKERS = {"stress": "x", "satisfaction": "+", "social_energy": "*"}

BOB_HELP_STANCE  = {"openness": -0.2, "conscientiousness": 0.4,
                    "extraversion": 0.0, "agreeableness": 0.6, "neuroticism": -0.4}
DAVE_HELP_STANCE = {"openness": 0.4, "conscientiousness": 0.01,
                    "extraversion": 0.2, "agreeableness": 0.0, "neuroticism": -0.8}


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


def stack_on_grid(per_seed, df_key, col, grid):
    rows = []
    for d in per_seed.values():
        df = d.get(df_key)
        if df is None or col not in df.columns:
            continue
        rows.append(np.interp(grid, df["episode"].to_numpy(),
                               df[col].to_numpy(dtype=float)))
    return np.vstack(rows) if rows else None


def smooth(arr, window=21):
    if arr is None or len(arr) < window:
        return arr
    return pd.Series(arr).rolling(window, min_periods=1, center=True).median().to_numpy()


def draw_dynamic(ax, per_seed, df_key, col_for, x, grid, title):
    markevery = max(1, len(x) // N_MARKERS)
    for trait in OCEAN:
        s = stack_on_grid(per_seed, df_key, col_for(trait), grid)
        if s is None:
            continue
        m  = smooth(s.mean(axis=0))
        sd = smooth(s.std(axis=0))
        c  = OCEAN_COLORS[trait]
        ax.plot(x, m, color=c, linewidth=1.4,
                marker=OCEAN_MARKERS[trait], markersize=5,
                markevery=markevery, markerfacecolor=c,
                markeredgecolor=c, label=OCEAN_LABELS[trait])
        ax.fill_between(x, m - sd, m + sd, color=c, alpha=0.10, linewidth=0)
    ax.axhline(0.0, color="grey", linewidth=0.5, linestyle="--")
    ax.set_xlim(0, x[-1])
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(title, fontsize=11)
    ax.set_ylabel("Trait value")
    ax.set_xlabel(r"CFR iteration  $t$")
    style_ax(ax)


def draw_static(ax, stance, x, title):
    markevery = max(1, len(x) // N_MARKERS)
    for trait in OCEAN:
        v = stance[trait]
        c = OCEAN_COLORS[trait]
        ax.plot(x, np.full_like(x, v, dtype=float),
                color=c, linewidth=1.4,
                marker=OCEAN_MARKERS[trait], markersize=5,
                markevery=markevery, markerfacecolor=c,
                markeredgecolor=c, label=OCEAN_LABELS[trait])
    ax.axhline(0.0, color="grey", linewidth=0.5, linestyle="--")
    ax.set_xlim(0, x[-1])
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(title, fontsize=11)
    ax.set_ylabel("Trait value")
    ax.set_xlabel(r"CFR iteration  $t$")
    style_ax(ax)


def draw_mood(ax, per_seed, x, grid):
    markevery = max(1, len(x) // N_MARKERS)
    for trait in MOOD_TRAITS:
        rows = []
        for d in per_seed.values():
            df = d.get("alice")
            if df is None or trait not in df.columns:
                continue
            rows.append(np.interp(grid, df["episode"].to_numpy(),
                                   df[trait].to_numpy(dtype=float)))
        if not rows:
            continue
        s  = np.vstack(rows)
        m  = s.mean(axis=0)
        sd = s.std(axis=0)
        c  = MOOD_COLORS[trait]
        mk = MOOD_MARKERS[trait]
        lw = 0.8 if trait != "stress" else 1.0
        ax.plot(x, m, color=c, linewidth=lw,
                marker=mk, markersize=5, markevery=markevery,
                markerfacecolor=c, markeredgecolor=c,
                label=MOOD_LABELS[trait])
        ax.fill_between(x, m - sd, m + sd, color=c, alpha=0.12, linewidth=0)
    ax.axhline(0.0, color="grey", linewidth=0.5, linestyle="--")
    ax.set_xlim(0, x[-1])
    ax.set_ylim(-1.05, 1.05)
    ax.set_ylabel("Trait value")
    ax.set_xlabel(r"CFR iteration  $t$")
    ax.set_title("Alice mood — updated after every plan execution, reset each episode",
                 fontsize=11)
    ax.legend(loc="lower right", fontsize=9, frameon=False,
              ncol=3, handlelength=1.5)
    style_ax(ax)


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    per_seed = {s: load_seed(d) for s, d in seeds.items()}

    max_eps = max(int(df["episode"].max())
                  for d in per_seed.values()
                  for df in d.values())
    grid = np.arange(1, max_eps + 1)
    x    = grid * ITER_PER_EP

    print(f"Loaded {len(per_seed)} seeds: {max_eps} episodes.")

    fig = plt.figure(figsize=(14, 16))
    fig.suptitle("Per-agent OCEAN personality and Alice mood\n"
                 f"(mean ± std across {len(per_seed)} seeds, "
                 f"{max_eps * ITER_PER_EP} CFR iterations)",
                 fontsize=13, fontweight="bold")

    gs = gridspec.GridSpec(3, 2, figure=fig,
                           height_ratios=[1, 1, 0.85],
                           hspace=0.45, wspace=0.30)

    ax_alice = fig.add_subplot(gs[0, 0])
    ax_bob   = fig.add_subplot(gs[0, 1])
    ax_carol = fig.add_subplot(gs[1, 0])
    ax_dave  = fig.add_subplot(gs[1, 1])
    ax_mood  = fig.add_subplot(gs[2, :])

    draw_dynamic(ax_alice, per_seed, "alice", lambda t: t,          x, grid, "Alice (CFR)")
    draw_static (ax_bob,   BOB_HELP_STANCE,                         x,       "Bob (static)")
    draw_dynamic(ax_carol, per_seed, "carol", lambda t: f"carol_{t}", x, grid, "Carol (CFR)")
    draw_static (ax_dave,  DAVE_HELP_STANCE,                        x,       "Dave (static)")
    draw_mood   (ax_mood,  per_seed,                                x, grid)

    # Shared OCEAN legend below the 2x2 panels, above the mood panel
    handles = [Line2D([0], [0], color=OCEAN_COLORS[t], linewidth=1.4,
                      marker=OCEAN_MARKERS[t], markersize=7,
                      markerfacecolor=OCEAN_COLORS[t],
                      markeredgecolor=OCEAN_COLORS[t],
                      label=OCEAN_LABELS[t])
               for t in OCEAN]
    fig.legend(handles=handles,
               loc="lower center",
               bbox_to_anchor=(0.5, 0.335),
               ncol=5, frameon=False, fontsize=10,
               columnspacing=2.0, handlelength=1.8)

    out = OUT / "all_in_one.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
