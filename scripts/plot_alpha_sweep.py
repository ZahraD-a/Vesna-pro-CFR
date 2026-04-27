#!/usr/bin/env python3
"""Sensitivity figures for the reciprocity-shaping coefficient alpha.

Reads results/alpha/alpha_<v>/seed_<n>/* directories produced by
scripts/run_alpha_sweep.sh and produces two complementary figures:

  figD_alpha_sensitivity.png     CFR-level outcomes vs alpha
                                  (phase-transition episode +
                                  Carol's adapted reciprocity).
  figE_OCEAN_alpha_sensitivity.png  Final OCEAN traits vs alpha
                                     for each of the five dimensions
                                     and each agent (2 rows x 5 cols).

For every metric we plot mean +/- std over the SEEDS_PER_VALUE seeds
that ran for each alpha.
"""

from __future__ import annotations
import re
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
ALPHA_RESULTS = RESULTS / "alpha"
OUT = ALPHA_RESULTS
OUT.mkdir(parents=True, exist_ok=True)

ALPHA_DIR_RE = re.compile(r"^alpha_(\d+(?:_\d+)?)$")

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


def collect_alpha_runs():
    found = {}
    for child in sorted(ALPHA_RESULTS.iterdir()):
        if not child.is_dir():
            continue
        m = ALPHA_DIR_RE.match(child.name)
        if not m:
            continue
        alpha = float(m.group(1).replace("_", "."))
        seeds = sorted(child.glob("seed_*"))
        if seeds:
            found[alpha] = seeds
    return found


def load_seed(seed_dir):
    paths = {
        "alice":   seed_dir / "personality_evolution.csv",
        "carol":   seed_dir / "carol_personality_evolution.csv",
        "regrets": seed_dir / "cfr_regrets.csv",
        "recip":   seed_dir / "adapted_reciprocity.csv",
    }
    out = {}
    for k, p in paths.items():
        if p.exists():
            out[k] = pd.read_csv(p)
    return out


def metrics_for_seed(d):
    metrics = {}
    if "regrets" in d and "decline_alice" in d["regrets"].columns:
        decl = d["regrets"]["decline_alice"].to_numpy()
        metrics["peak_episode"] = int(np.argmax(decl))
    if "alice" in d:
        for t in OCEAN:
            if t in d["alice"].columns:
                metrics[f"alice_{t}_final"] = float(d["alice"][t].iloc[-1])
    if "carol" in d:
        for t in OCEAN:
            col = f"carol_{t}"
            if col in d["carol"].columns:
                metrics[f"carol_{t}_final"] = float(d["carol"][col].iloc[-1])
    if "recip" in d and "carol_adapted" in d["recip"].columns:
        metrics["carol_recip_final"] = float(d["recip"]["carol_adapted"].iloc[-1])
    return metrics


def errorbar_panel(ax, df, alphas, col, color, ylabel, title,
                   y_lo=None, y_hi=None):
    if col not in df.columns:
        ax.set_axis_off()
        return
    agg = df.groupby("alpha")[col].agg(["mean", "std"]).reindex(alphas)
    x = np.array(alphas, dtype=float)
    m = agg["mean"].to_numpy()
    s = agg["std"].to_numpy()
    ax.errorbar(x, m, yerr=s, fmt="o-", color=color, capsize=4,
                linewidth=2.0, markersize=7)
    ax.fill_between(x, m - s, m + s, color=color, alpha=0.18)
    ax.set_xlabel(r"$\alpha$ (reciprocity shaping)")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11, fontweight="bold")
    if y_lo is not None and y_hi is not None:
        ax.set_ylim(y_lo, y_hi)
    ax.grid(alpha=0.3)


def fig_outcomes(df, alphas, n_seeds):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.4))
    fig.suptitle(r"Sensitivity of CFR outcomes to the shaping coefficient $\alpha$ "
                 f"(mean $\\pm$ std over {n_seeds} seeds per $\\alpha$)",
                 fontsize=12, fontweight="bold")
    errorbar_panel(axes[0], df, alphas, "peak_episode", "#7F1D1D",
                   "Episode", "Phase-transition episode\n(decline-regret peak)")
    errorbar_panel(axes[1], df, alphas, "carol_recip_final", "#16A085",
                   "Reciprocity", "Carol final adapted reciprocity",
                   y_lo=-0.05, y_hi=1.10)
    plt.tight_layout()
    out = OUT / "figD_alpha_sensitivity.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)


def fig_ocean_sensitivity(df, alphas, n_seeds):
    fig, axes = plt.subplots(2, 5, figsize=(18.0, 7.0),
                             sharex=True, sharey=True)
    fig.suptitle(r"Sensitivity of final OCEAN traits to $\alpha$ "
                 f"(mean $\\pm$ std over {n_seeds} seeds per $\\alpha$)",
                 fontsize=14, fontweight="bold")
    for j, trait in enumerate(OCEAN):
        color = OCEAN_COLORS[trait]
        # Alice top row
        ax = axes[0, j]
        errorbar_panel(ax, df, alphas, f"alice_{trait}_final", color,
                       "Trait value", OCEAN_LABELS[trait],
                       y_lo=-1.05, y_hi=1.05)
        ax.axhline(0.0, color="grey", linewidth=0.6, linestyle="--")
        if j == 0:
            ax.set_ylabel("Alice final trait", fontsize=11, fontweight="bold")
        else:
            ax.set_ylabel("")
        # Carol bottom row
        ax = axes[1, j]
        errorbar_panel(ax, df, alphas, f"carol_{trait}_final", color,
                       "Trait value", "",
                       y_lo=-1.05, y_hi=1.05)
        ax.axhline(0.0, color="grey", linewidth=0.6, linestyle="--")
        if j == 0:
            ax.set_ylabel("Carol final trait", fontsize=11, fontweight="bold")
        else:
            ax.set_ylabel("")
    plt.tight_layout()
    out = OUT / "figE_OCEAN_alpha_sensitivity.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)


def main():
    runs = collect_alpha_runs()
    if not runs:
        sys.stderr.write(
            "No results/alpha/alpha_*/seed_*/ directories found.\n"
            "Run scripts/run_alpha_sweep.sh first.\n")
        return 1

    alphas = sorted(runs)
    print(f"alpha values: {alphas}")

    rows = []
    for alpha in alphas:
        for seed_dir in runs[alpha]:
            d = load_seed(seed_dir)
            m = metrics_for_seed(d)
            m["alpha"] = alpha
            m["seed"] = int(seed_dir.name.split("_")[1])
            rows.append(m)

    df = pd.DataFrame(rows)
    n_seeds = int(df.groupby("alpha").size().min())

    fig_outcomes(df, alphas, n_seeds)
    fig_ocean_sensitivity(df, alphas, n_seeds)

    print("\n=== Sensitivity summary (final OCEAN per agent + outcomes) ===")
    keep = [c for c in df.columns
            if c.endswith("_final") or c == "peak_episode"]
    print(df.groupby("alpha")[keep].agg(["mean", "std"]).round(3).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
