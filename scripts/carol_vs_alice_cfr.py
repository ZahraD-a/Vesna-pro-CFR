#!/usr/bin/env python3
"""Carol vs Alice observational CFR cumulative regret over iterations.

Carol fires her CFR only during her own 10 interactions per episode:
  10 interactions × 2000 episodes = 20,000 CFR iterations.

This is by design — Carol observes Alice's actions toward her only,
not Alice's interactions with Bob or Dave.

Reads results/seed_<n>/carol_cfr_trace.csv

Produces:
    results/regret/carol_vs_alice_cfr.png
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT    = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT     = RESULTS / "regret"
OUT.mkdir(parents=True, exist_ok=True)

N_MARKERS = 11

ACTION_COLOR  = {"help": "#27AE60", "decline": "#C0392B", "third": "#E67E22"}
ACTION_MARKER = {"help": "^",       "decline": "o",       "third": "s"}

ACTIONS = [
    ("carol_help_alice_regret",        "help",    "carol_help_alice"),
    ("carol_decline_alice_regret",     "decline", "carol_decline_alice"),
    ("carol_reciprocate_alice_regret", "third",   "carol_reciprocate_alice"),
]


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
    p = seed_dir / "carol_cfr_trace.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df["iteration"] = pd.to_numeric(df["iteration"], errors="coerce")
    df = df.dropna(subset=["iteration"]).astype({"iteration": int})
    return df.sort_values("iteration")


def smooth(arr, window=21):
    if arr is None or len(arr) < window:
        return arr
    return pd.Series(arr).rolling(window, min_periods=1, center=True).median().to_numpy()


def build_t_grid(traces, target_points=2000):
    max_iters = [int(df["iteration"].max()) for df in traces.values() if df is not None]
    if not max_iters:
        return None
    n    = min(max_iters)
    step = max(1, n // target_points)
    return np.arange(1, n + 1, step)


def stack_regret(traces, col, t_grid):
    rows = []
    for df in traces.values():
        if df is None or col not in df.columns:
            continue
        t    = df["iteration"].to_numpy(dtype=float)
        r    = df[col].to_numpy(dtype=float)
        mask = t_grid <= t.max()
        row  = np.full_like(t_grid, np.nan, dtype=float)
        row[mask] = np.interp(t_grid[mask], t, r)
        rows.append(row)
    return np.vstack(rows) if rows else None


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    traces = {s: load_seed(d) for s, d in seeds.items()}
    t_grid = build_t_grid(traces)
    if t_grid is None:
        sys.stderr.write("No carol_cfr_trace.csv found in any seed.\n")
        return 1

    print(f"Loaded {len(seeds)} seeds. Carol max iter: {t_grid[-1]}.")

    fig, ax = plt.subplots(figsize=(8.0, 5.5))
    fig.suptitle("Carol vs Alice CFR cumulative regret\n"
                 f"(mean $\\pm$ std across {len(seeds)} seeds, "
                 f"{t_grid[-1]} CFR iterations)",
                 fontsize=13, fontweight="bold")

    markevery = max(1, len(t_grid) // N_MARKERS)
    for col, role, label in ACTIONS:
        s = stack_regret(traces, col, t_grid)
        if s is None:
            continue
        color  = ACTION_COLOR[role]
        marker = ACTION_MARKER[role]
        m  = smooth(np.nanmean(s, axis=0))
        sd = smooth(np.nanstd(s,  axis=0))
        ax.plot(t_grid, m, color=color, linewidth=1.4,
                marker=marker, markersize=6, markevery=markevery,
                markerfacecolor=color, markeredgecolor=color,
                label=label)
        ax.fill_between(t_grid, m - sd, m + sd,
                        color=color, alpha=0.10, linewidth=0)

    ax.axhline(0.0, color="grey", linewidth=0.5, linestyle="--")
    ax.set_xlabel(rf"CFR iteration  $t$  (max {t_grid[-1]})")
    ax.set_ylabel("Cumulative regret  $R_t(a)$")
    ax.set_title("Carol vs Alice  (CFR)", fontsize=12)
    ax.legend(loc="best", fontsize=10, frameon=False, handlelength=2.0)
    style_ax(ax)

    plt.tight_layout()
    out = OUT / "carol_vs_alice_cfr.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
