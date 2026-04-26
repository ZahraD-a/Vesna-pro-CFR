#!/usr/bin/env python3
"""Per-agent CFR regret dynamics, mean +/- std across seeds.

Inspired by the per-game grid layout used in
"Asynchronous Predictive Counterfactual Regret Minimization+"
(Meng et al. 2025), where each panel contains all curves needed to
compare action-level dynamics within one decision context.

Layout: 2x2 grid.
    (0,0) Alice vs Bob       help_bob,    decline_bob,    delay_bob
    (0,1) Alice vs Carol     help_alice,  decline_alice,  teach_alice
    (1,0) Alice vs Dave      help_dave,   decline_dave,   suggest_dave
    (1,1) Carol vs Alice     carol_help_regret,
                              carol_decline_regret,
                              carol_reciprocate_regret

Each panel shows mean (line) +/- std (band) across all available seeds.
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

ACTION_COLORS = {
    "help":        "#16A085",
    "decline":     "#C0392B",
    "teach":       "#2980B9",
    "delay":       "#8E44AD",
    "suggest":     "#F39C12",
    "reciprocate": "#1ABC9C",
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


def load_csv(seed_dir, name):
    p = seed_dir / name
    if not p.exists():
        return None
    df = pd.read_csv(p)
    if "episode" in df.columns:
        df["episode"] = pd.to_numeric(df["episode"], errors="coerce")
        df = df.dropna(subset=["episode"]).astype({"episode": int})
        df = df.sort_values("episode")
    return df


def stack(per_seed_dfs, col, grid):
    rows = []
    for df in per_seed_dfs:
        if df is None or col not in df.columns:
            continue
        rows.append(np.interp(grid,
                              df["episode"].to_numpy(),
                              df[col].to_numpy(dtype=float)))
    if not rows:
        return None
    return np.vstack(rows)


def smooth(arr, window=21):
    if arr is None or len(arr) < window:
        return arr
    return pd.Series(arr).rolling(window, min_periods=1,
                                  center=True).median().to_numpy()


def panel(ax, per_seed, csv_key, columns, title, ylabel,
          color_for, label_for, grid):
    dfs = [d.get(csv_key) for d in per_seed.values()]
    for col in columns:
        s = stack(dfs, col, grid)
        if s is None:
            continue
        m = smooth(s.mean(axis=0))
        sd = smooth(s.std(axis=0))
        c = color_for(col)
        ax.plot(grid, m, color=c, linewidth=2.0, label=label_for(col))
        ax.fill_between(grid, m - sd, m + sd, color=c, alpha=0.18)
    ax.axhline(0.0, color="grey", linewidth=0.7, linestyle="--")
    ax.set_xlabel("Episode")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=9, framealpha=0.85)


def alice_color(col):
    head = col.split("_")[0]
    return ACTION_COLORS.get(head, "#34495E")


def alice_label(col):
    return col


def carol_color(col):
    if "help" in col:        return ACTION_COLORS["help"]
    if "decline" in col:     return ACTION_COLORS["decline"]
    if "reciprocate" in col: return ACTION_COLORS["reciprocate"]
    return "#34495E"


def carol_label(col):
    return col.replace("carol_", "").replace("_regret", "")


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    per_seed = {s: {"alice": load_csv(d, "cfr_regrets.csv"),
                    "carol": load_csv(d, "carol_cfr_regrets.csv")}
                for s, d in seeds.items()}

    max_eps = []
    for d in per_seed.values():
        for v in d.values():
            if v is not None and "episode" in v.columns and len(v):
                max_eps.append(int(v["episode"].max()))
    n_eps = min(max_eps) if max_eps else 0
    grid = np.arange(0, n_eps + 1)
    print(f"Loaded {len(per_seed)} seeds, common grid 0..{n_eps}")

    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.0), sharex=True)
    fig.suptitle("CFR cumulative regret per agent and decision context "
                 f"(mean $\\pm$ std across {len(per_seed)} seeds)",
                 fontsize=14, fontweight="bold")

    panel(axes[0, 0], per_seed, "alice",
          ["help_bob", "decline_bob", "delay_bob"],
          "Alice vs Bob", "Cumulative regret",
          alice_color, alice_label, grid)
    panel(axes[0, 1], per_seed, "alice",
          ["help_alice", "decline_alice", "teach_alice"],
          "Alice vs Carol", "Cumulative regret",
          alice_color, alice_label, grid)
    panel(axes[1, 0], per_seed, "alice",
          ["help_dave", "decline_dave", "suggest_dave"],
          "Alice vs Dave", "Cumulative regret",
          alice_color, alice_label, grid)
    panel(axes[1, 1], per_seed, "carol",
          ["carol_help_regret",
           "carol_decline_regret",
           "carol_reciprocate_regret"],
          "Carol vs Alice", "Cumulative regret",
          carol_color, carol_label, grid)

    plt.tight_layout()
    out = RESULTS / "figF_cfr_per_agent.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
