#!/usr/bin/env python3
"""Adaptive reciprocity dynamics across colleagues (closed-loop check).

Reads results/seed_<n>/adapted_reciprocity.csv and produces:

  fig4_adaptive_reciprocity.png   1x2 panel.
    (0) Adapted reciprocity over training for each colleague (Bob, Carol,
        Dave). Innate baselines drawn as dotted reference lines, the soft
        adaptation cap (0.85, defined in BehavioralMemory.java:158)
        as a horizontal dashed line.
    (1) Carol's *latent* adapted reciprocity vs her *empirical* observed
        reciprocity ratio. A consistency check: Alice's internal estimate
        should track what Carol is actually doing.
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

ADAPTATION_CAP = 0.85

COLLEAGUE_COLOR = {"bob":   "#1f77b4",
                   "carol": "#d62728",
                   "dave":  "#2ca02c"}
COLLEAGUE_MARKER = {"bob": "s", "carol": "o", "dave": "^"}
COLLEAGUE_LABEL = {"bob": "Bob", "carol": "Carol", "dave": "Dave"}


def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(alpha=0.25)


def collect_seeds():
    out = {}
    for d in sorted(RESULTS.glob("seed_*")):
        try:
            s = int(d.name.split("_")[1])
        except (IndexError, ValueError):
            continue
        out[s] = d
    return out


def load_recip(seed_dir):
    p = seed_dir / "adapted_reciprocity.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df["episode"] = pd.to_numeric(df["episode"], errors="coerce")
    df = df.dropna(subset=["episode"]).astype({"episode": int})
    return df.sort_values("episode")


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


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    dfs = [load_recip(d) for d in seeds.values()]
    n_eps = min(int(df["episode"].max()) for df in dfs if df is not None)
    grid = np.arange(0, n_eps + 1)
    print(f"Loaded {len(dfs)} seeds, common grid 0..{n_eps}")

    fig, axes = plt.subplots(1, 2, figsize=(14.0, 5.6))
    ITER_PER_EP = 30  # see plot_paper_figures.py
    x = grid * ITER_PER_EP
    fig.suptitle("Rule-based adaptive reciprocity across colleagues "
                 r"(non-CFR mechanism — see $\mathit{adaptReciprocity}$ in BehavioralMemory.java)"
                 "\n"
                 f"mean $\\pm$ std across {len(dfs)} seeds, "
                 f"{x[-1]} CFR iterations",
                 fontsize=12, fontweight="bold")

    # --- Left: 3 colleagues' adapted reciprocity ---
    ax = axes[0]
    for k in ("bob", "carol", "dave"):
        adapted = stack(dfs, f"{k}_adapted", grid)
        innate  = stack(dfs, f"{k}_innate",  grid)
        if adapted is None:
            continue
        m  = smooth(adapted.mean(axis=0))
        sd = smooth(adapted.std(axis=0))
        c  = COLLEAGUE_COLOR[k]
        ax.plot(x, m, color=c, linewidth=1.4,
                marker=COLLEAGUE_MARKER[k], markersize=6,
                markevery=max(1, len(x) // 11),
                markerfacecolor=c, markeredgecolor=c,
                label=f"{COLLEAGUE_LABEL[k]} adapted")
        ax.fill_between(x, m - sd, m + sd, color=c, alpha=0.10, linewidth=0)
        if innate is not None:
            innate_value = float(innate.mean(axis=0)[0])
            ax.axhline(innate_value, color=c, linewidth=1.0,
                       linestyle=":",
                       label=f"{COLLEAGUE_LABEL[k]} innate ({innate_value:.2f})")

    ax.axhline(ADAPTATION_CAP, color="grey", linewidth=1.0,
               linestyle="--",
               label=f"adaptation cap ({ADAPTATION_CAP:.2f})")
    ax.set_xlabel(r"CFR iteration  $t$")
    ax.set_ylabel("Reciprocity ratio")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title("Adapted reciprocity per colleague",
                 fontsize=12)
    style_ax(ax)
    ax.legend(loc="lower right", fontsize=9, frameon=False, ncol=2,
              columnspacing=1.6, handlelength=2.0)

    # --- Right: Carol adapted vs observed (consistency check) ---
    ax = axes[1]
    for col, color, label in (("carol_adapted",        "#16A085", "Adapted (latent)"),
                              ("carol_observed_ratio", "#7F8C8D", "Observed (empirical)")):
        s = stack(dfs, col, grid)
        if s is None:
            continue
        m  = smooth(s.mean(axis=0))
        sd = smooth(s.std(axis=0))
        marker = "o" if "adapted" in col else "s"
        ax.plot(x, m, color=color, linewidth=1.4,
                marker=marker, markersize=6,
                markevery=max(1, len(x) // 11),
                markerfacecolor=color, markeredgecolor=color,
                label=label)
        ax.fill_between(x, m - sd, m + sd, color=color, alpha=0.10, linewidth=0)

    final_adapted = stack(dfs, "carol_adapted", grid)
    final_observed = stack(dfs, "carol_observed_ratio", grid)
    if final_adapted is not None and final_observed is not None:
        a_end = final_adapted[:, -1].mean()
        a_std = final_adapted[:, -1].std()
        o_end = final_observed[:, -1].mean()
        o_std = final_observed[:, -1].std()
        ax.text(0.98, 0.05,
                f"Carol final ratios:\n"
                f"   Adapted  = {a_end:.2f} $\\pm$ {a_std:.2f}\n"
                f"   Observed = {o_end:.2f} $\\pm$ {o_std:.2f}",
                transform=ax.transAxes,
                fontsize=9, va="bottom", ha="right",
                bbox=dict(boxstyle="round,pad=0.35",
                          facecolor="white", edgecolor="grey", alpha=0.92))

    ax.set_xlabel(r"CFR iteration  $t$")
    ax.set_ylabel("Reciprocity ratio")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title("Carol: adapted vs observed",
                 fontsize=12)
    style_ax(ax)
    ax.legend(loc="upper left", fontsize=9, frameon=False, handlelength=2.0)

    plt.tight_layout()
    out_dir = RESULTS / "reciprocity"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "fig4_adaptive_reciprocity.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
