#!/usr/bin/env python3
"""Per-agent, per-context cumulative CFR regret over iterations.

Reads results/seed_<n>/cfr_trace.csv (Alice) and
results/seed_<n>/carol_cfr_trace.csv (Carol).

Produces:
    results/regret/regret_per_agent.png
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
    for key, fname in [("alice_trace", "cfr_trace.csv"),
                       ("carol_trace", "carol_cfr_trace.csv")]:
        p = seed_dir / fname
        if p.exists():
            df = pd.read_csv(p)
            df["iteration"] = pd.to_numeric(df["iteration"], errors="coerce")
            df = df.dropna(subset=["iteration"]).astype({"iteration": int})
            out[key] = df.sort_values("iteration")
    return out


def smooth(arr, window=21):
    if arr is None or len(arr) < window:
        return arr
    return pd.Series(arr).rolling(window, min_periods=1, center=True).median().to_numpy()


def build_t_grid(per_seed, trace_key, target_points=2000):
    max_iters = []
    for d in per_seed.values():
        df = d.get(trace_key)
        if df is not None and "iteration" in df.columns and len(df):
            max_iters.append(int(df["iteration"].max()))
    if not max_iters:
        return None
    n    = min(max_iters)
    step = max(1, n // target_points)
    return np.arange(1, n + 1, step)


def stack_regret(per_seed, trace_key, action_cols, t_grid):
    out = {a: [] for a in action_cols}
    for d in per_seed.values():
        df = d.get(trace_key)
        if df is None:
            continue
        t = df["iteration"].to_numpy(dtype=float)
        for a in action_cols:
            if a not in df.columns:
                continue
            r    = df[a].to_numpy(dtype=float)
            mask = t_grid <= t.max()
            row  = np.full_like(t_grid, np.nan, dtype=float)
            row[mask] = np.interp(t_grid[mask], t, r)
            out[a].append(row)
    return {a: np.vstack(rows) for a, rows in out.items() if rows}


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    per_seed   = {s: load_seed(d) for s, d in seeds.items()}
    alice_grid = build_t_grid(per_seed, "alice_trace")
    carol_grid = build_t_grid(per_seed, "carol_trace")

    print(f"Loaded {len(per_seed)} seeds. "
          f"Alice max iter: {alice_grid[-1] if alice_grid is not None else 'N/A'}, "
          f"Carol max iter: {carol_grid[-1] if carol_grid is not None else 'N/A'}.")

    # Carol vs Alice has its own dedicated plot in carol_vs_alice_cfr.py
    PANELS = [
        ("Alice vs Bob   (self-CFR)",
         "alice_trace", alice_grid,
         [("alice_help_bob",     "help",    "alice_help_bob"),
          ("alice_decline_bob",  "decline", "alice_decline_bob"),
          ("alice_delay_bob",    "third",   "alice_delay_bob")]),

        ("Alice vs Carol  (self-CFR)",
         "alice_trace", alice_grid,
         [("alice_help_carol",    "help",    "alice_help_carol"),
          ("alice_decline_carol", "decline", "alice_decline_carol"),
          ("alice_teach_carol",   "third",   "alice_teach_carol")]),

        ("Alice vs Dave   (self-CFR)",
         "alice_trace", alice_grid,
         [("alice_help_dave",     "help",    "alice_help_dave"),
          ("alice_decline_dave",  "decline", "alice_decline_dave"),
          ("alice_suggest_dave",  "third",   "alice_suggest_dave")]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18.0, 5.5))
    fig.suptitle("Alice self-CFR cumulative regret "
                 f"(mean $\\pm$ std across {len(per_seed)} seeds)",
                 fontsize=13, fontweight="bold")

    for ax, (title, key, panel_grid, actions) in zip(axes.flat, PANELS):
        if panel_grid is None:
            continue
        markevery = max(1, len(panel_grid) // N_MARKERS)
        cols   = [a[0] for a in actions]
        stacks = stack_regret(per_seed, key, cols, panel_grid)
        for col, role, label in actions:
            s = stacks.get(col)
            if s is None:
                continue
            color  = ACTION_COLOR[role]
            marker = ACTION_MARKER[role]
            m  = smooth(np.nanmean(s, axis=0))
            sd = smooth(np.nanstd(s,  axis=0))
            ax.plot(panel_grid, m, color=color, linewidth=1.4,
                    marker=marker, markersize=6, markevery=markevery,
                    markerfacecolor=color, markeredgecolor=color,
                    label=label)
            ax.fill_between(panel_grid, m - sd, m + sd,
                            color=color, alpha=0.10, linewidth=0)
        ax.axhline(0.0, color="grey", linewidth=0.5, linestyle="--")
        ax.set_xlim(0, panel_grid[-1])
        ax.set_xlabel(rf"CFR iteration  $t$  (max {panel_grid[-1]})")
        ax.set_ylabel("Cumulative regret  $R_t(a)$")
        ax.set_title(title, fontsize=12)
        style_ax(ax)
        ax.legend(loc="best", fontsize=9, frameon=False, handlelength=2.0)

    plt.tight_layout()
    out = OUT / "regret_per_agent.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
