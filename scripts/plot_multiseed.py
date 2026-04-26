#!/usr/bin/env python3
"""Mastio-style multi-seed publication figures for the EUMAS paper.

Reads results/seed_<n>/* directories produced by tests/run_10_seeds.sh
and produces three figures saved into results/:

  figA_regret_reversal.png   Alice's CFR regrets vs Carol (3 actions),
                              mean +/- std across seeds.
  figB_OCEAN_coevolution.png 2x5 grid: every OCEAN trait for Alice (top
                              row) and Carol (bottom row), mean +/- std
                              across seeds. This is the core figure for
                              showing how personality co-evolves under
                              CFR-driven adaptation.
  figC_reciprocity.png       Carol agreeableness alongside her adapted
                              reciprocity ratio, mean +/- std.

All bands are computed on a common episode grid using linear
interpolation, then a short rolling median is applied for readability.
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

OCEAN = ["openness", "conscientiousness", "extraversion",
         "agreeableness", "neuroticism"]
OCEAN_LABELS = {
    "openness":          "Openness",
    "conscientiousness": "Conscientiousness",
    "extraversion":      "Extraversion",
    "agreeableness":     "Agreeableness",
    "neuroticism":       "Neuroticism",
}
OCEAN_COLORS = {
    "openness":          "#8E44AD",
    "conscientiousness": "#16A085",
    "extraversion":      "#F39C12",
    "agreeableness":     "#2980B9",
    "neuroticism":       "#C0392B",
}


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
    files = {
        "alice":     "personality_evolution.csv",
        "carol":     "carol_personality_evolution.csv",
        "alice_reg": "cfr_regrets.csv",
        "recip":     "adapted_reciprocity.csv",
    }
    out = {}
    for k, f in files.items():
        p = seed_dir / f
        if p.exists():
            df = pd.read_csv(p)
            if "episode" in df.columns:
                df["episode"] = pd.to_numeric(df["episode"],
                                              errors="coerce")
                df = df.dropna(subset=["episode"]).astype({"episode": int})
                df = df.sort_values("episode")
            out[k] = df
    return out


def stack_on_grid(per_seed, df_key, value_col, grid):
    rows = []
    for dfs in per_seed.values():
        df = dfs.get(df_key)
        if df is None or value_col not in df.columns:
            continue
        rows.append(np.interp(grid,
                              df["episode"].to_numpy(),
                              df[value_col].to_numpy(dtype=float)))
    if not rows:
        return None
    return np.vstack(rows)


def smooth(arr, window=21):
    if arr is None or len(arr) < window:
        return arr
    s = pd.Series(arr).rolling(window, min_periods=1, center=True).median()
    return s.to_numpy()


def plot_band(ax, x, mean, std, color, label, smooth_window=21):
    m = smooth(mean, smooth_window)
    s = smooth(std,  smooth_window)
    ax.plot(x, m, color=color, linewidth=2.0, label=label)
    ax.fill_between(x, m - s, m + s, color=color, alpha=0.20)


# ---------------------------------------------------------------------------
# Figure A: regret reversal (Alice vs Carol)
# ---------------------------------------------------------------------------

def fig_regret_reversal(per_seed, grid):
    targets = [("help_alice",    "help",    "#16A085"),
               ("decline_alice", "decline", "#C0392B"),
               ("teach_alice",   "teach",   "#2980B9")]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), sharey=True)
    fig.suptitle("Alice CFR regret vs Carol "
                 f"(mean $\\pm$ std across {len(per_seed)} seeds)",
                 fontsize=13, fontweight="bold")

    for ax, (col, label, color) in zip(axes, targets):
        stack = stack_on_grid(per_seed, "alice_reg", col, grid)
        if stack is None:
            ax.set_axis_off()
            continue
        plot_band(ax, grid, stack.mean(axis=0), stack.std(axis=0),
                  color, label)
        ax.axhline(0.0, color="grey", linewidth=0.7, linestyle="--")
        ax.set_xlabel("Episode")
        ax.set_title(f"{label}_alice", fontsize=11)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Cumulative regret")
    plt.tight_layout()
    out = RESULTS / "figA_regret_reversal.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure B: OCEAN co-evolution -- one panel per agent, all 5 traits overlaid
# ---------------------------------------------------------------------------

def _plot_all_ocean(ax, per_seed, df_key, col_for_trait, grid, title):
    for trait in OCEAN:
        col = col_for_trait(trait)
        stack = stack_on_grid(per_seed, df_key, col, grid)
        if stack is None:
            continue
        m  = smooth(stack.mean(axis=0))
        sd = smooth(stack.std(axis=0))
        c  = OCEAN_COLORS[trait]
        ax.plot(grid, m, color=c, linewidth=2.2, label=OCEAN_LABELS[trait])
        ax.fill_between(grid, m - sd, m + sd, color=c, alpha=0.12)
    ax.axhline(0.0, color="grey", linewidth=0.7, linestyle="--")
    ax.set_xlabel("Episode")
    ax.set_ylabel("Trait value")
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=9, framealpha=0.85, ncol=1)


def fig_ocean_coevolution(per_seed, grid):
    fig, axes = plt.subplots(1, 2, figsize=(14.0, 5.4),
                             sharex=True, sharey=True)
    fig.suptitle("OCEAN personality co-evolution under CFR "
                 f"(mean $\\pm$ std across {len(per_seed)} seeds)",
                 fontsize=14, fontweight="bold")

    _plot_all_ocean(axes[0], per_seed, "alice",
                    lambda t: t, grid, "Alice OCEAN")
    _plot_all_ocean(axes[1], per_seed, "carol",
                    lambda t: f"carol_{t}", grid, "Carol OCEAN")

    plt.tight_layout()
    out = RESULTS / "figB_OCEAN_coevolution.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure C: Carol agreeableness next to her adapted reciprocity ratio
# ---------------------------------------------------------------------------

def fig_reciprocity(per_seed, grid):
    """Carol's OCEAN dynamics with her reciprocity ratio overlaid.

    Left panel: all 5 of Carol's OCEAN traits + her adapted reciprocity
                ratio on a twin y-axis. The reader sees the temporal
                correlation: as Carol's reciprocity ratio rises, her
                Agreeableness flips from negative to positive.
    Right panel: Carol's adapted vs observed reciprocity ratios.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14.0, 5.0))
    fig.suptitle("Carol's reciprocity-driven personality change "
                 f"(mean $\\pm$ std across {len(per_seed)} seeds)",
                 fontsize=13, fontweight="bold")

    ax = axes[0]
    for trait in OCEAN:
        stack = stack_on_grid(per_seed, "carol", f"carol_{trait}", grid)
        if stack is None:
            continue
        m  = smooth(stack.mean(axis=0))
        sd = smooth(stack.std(axis=0))
        c  = OCEAN_COLORS[trait]
        ax.plot(grid, m, color=c, linewidth=2.0, label=OCEAN_LABELS[trait])
        ax.fill_between(grid, m - sd, m + sd, color=c, alpha=0.12)
    ax.axhline(0.0, color="grey", linewidth=0.7, linestyle="--")
    ax.set_xlabel("Episode")
    ax.set_ylabel("Carol trait value")
    ax.set_ylim(-1.05, 1.05)
    ax.set_title("Carol OCEAN with reciprocity overlay")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower left", fontsize=9, framealpha=0.85)

    ax2 = ax.twinx()
    rec = stack_on_grid(per_seed, "recip", "carol_adapted", grid)
    if rec is not None:
        m = smooth(rec.mean(axis=0))
        ax2.plot(grid, m, color="black", linewidth=2.4,
                 linestyle="--", label="Adapted reciprocity")
    ax2.set_ylabel("Adapted reciprocity ratio", color="black")
    ax2.set_ylim(-0.05, 1.10)
    ax2.legend(loc="lower right", fontsize=9, framealpha=0.85)

    ax = axes[1]
    for col, color, label in (("carol_adapted",        "#16A085", "Adapted"),
                              ("carol_observed_ratio", "#7F8C8D", "Observed")):
        stack = stack_on_grid(per_seed, "recip", col, grid)
        if stack is None:
            continue
        plot_band(ax, grid, stack.mean(axis=0), stack.std(axis=0),
                  color, label)
    ax.set_xlabel("Episode")
    ax.set_ylabel("Reciprocity ratio")
    ax.set_title("Carol adapted vs observed reciprocity")
    ax.set_ylim(-0.05, 1.10)
    ax.legend(loc="best")
    ax.grid(alpha=0.3)

    plt.tight_layout()
    out = RESULTS / "figC_reciprocity.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Endpoint summary table
# ---------------------------------------------------------------------------

def endpoint_summary(per_seed):
    rows = []
    for seed, dfs in per_seed.items():
        row = {"seed": seed}
        if "alice" in dfs:
            for t in OCEAN:
                if t in dfs["alice"].columns:
                    row[f"alice_{t}_final"] = float(dfs["alice"][t].iloc[-1])
        if "carol" in dfs:
            for t in OCEAN:
                col = f"carol_{t}"
                if col in dfs["carol"].columns:
                    row[f"carol_{t}_final"] = float(dfs["carol"][col].iloc[-1])
        if "alice_reg" in dfs and "decline_alice" in dfs["alice_reg"].columns:
            row["phase_transition_episode"] = int(
                np.argmax(dfs["alice_reg"]["decline_alice"].to_numpy()))
        if "recip" in dfs and "carol_adapted" in dfs["recip"].columns:
            row["carol_recip_final"] = float(
                dfs["recip"]["carol_adapted"].iloc[-1])
        rows.append(row)
    df = pd.DataFrame(rows)
    print("\n=== Endpoint statistics across seeds (mean +/- std) ===")
    summary = df.drop(columns=["seed"]).agg(["mean", "std"]).round(3)
    print(summary.to_string())
    return df


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write(
            "No results/seed_* directories found. "
            "Run tests/run_10_seeds.sh first.\n")
        return 1

    per_seed = {s: load_seed(d) for s, d in seeds.items()}

    max_eps = []
    for dfs in per_seed.values():
        for k in ("alice", "alice_reg", "carol", "recip"):
            df = dfs.get(k)
            if df is not None and "episode" in df.columns and len(df):
                max_eps.append(int(df["episode"].max()))
    n_eps = min(max_eps) if max_eps else 0
    grid = np.arange(0, n_eps + 1)
    print(f"Loaded {len(per_seed)} seeds, common grid 0..{n_eps}")

    fig_regret_reversal(per_seed, grid)
    fig_ocean_coevolution(per_seed, grid)
    fig_reciprocity(per_seed, grid)
    endpoint_summary(per_seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
