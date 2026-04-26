#!/usr/bin/env python3
"""Two clean Leduc-style publication figures for the EUMAS paper.

Reads results/seed_<n>/*.csv (10 seeds x 2000 episodes) and produces:

  fig1_personality_4agents.png   2x2 grid of OCEAN per agent.
                                   - Alice and Carol: dynamic mean +/- std
                                     trajectories of all 5 OCEAN traits.
                                   - Bob and Dave: static "cooperative
                                     stance" derived from their help-action
                                     profile in HelpScenarioConfig (they do
                                     not learn, so their values are flat
                                     reference lines).

  fig2_convergence_behavior.png  Leduc-style 1x2 paired panel.
                                   - Left: log10 average per-info-set regret
                                     vs log10 episode, one curve per
                                     decision context (Alice-vs-Bob,
                                     -vs-Carol, -vs-Dave, Carol-vs-Alice).
                                   - Right: regret-matching probability of
                                     selecting decline at each context, mean
                                     +/- std across seeds.
                                   Same color per context across both panels.

The colour rule from the Leduc paper is enforced: one semantic dimension
per colour, and the colour stays locked across paired panels.
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
    "openness": "O", "conscientiousness": "C", "extraversion": "E",
    "agreeableness": "A", "neuroticism": "N",
}
OCEAN_COLORS = {
    "openness":          "#7D3C98",   # purple
    "conscientiousness": "#27AE60",   # green
    "extraversion":      "#E67E22",   # orange
    "agreeableness":     "#1F3A93",   # navy
    "neuroticism":       "#B22222",   # firebrick
}


def style_ax(ax):
    """Modern academic style: drop top/right spines, soft grid."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(alpha=0.25)

# Static "cooperative stance" for Bob and Dave -- the OCEAN profile
# attached to their help_X action in HelpScenarioConfig.java.
BOB_HELP_STANCE  = {"openness": -0.2, "conscientiousness":  0.4,
                    "extraversion":  0.0, "agreeableness":   0.6,
                    "neuroticism":  -0.4}
DAVE_HELP_STANCE = {"openness":  0.4, "conscientiousness":  0.0,
                    "extraversion":  0.2, "agreeableness":   0.0,
                    "neuroticism":  -0.8}

# Leduc-style colour-per-context (locked across paired panels).
CONTEXT_COLOR  = {"Alice vs Bob":   "#1f77b4",
                  "Alice vs Carol": "#d62728",
                  "Alice vs Dave":  "#2ca02c",
                  "Carol vs Alice": "#9467bd"}
CONTEXT_MARKER = {"Alice vs Bob":   "s",
                  "Alice vs Carol": "o",
                  "Alice vs Dave":  "^",
                  "Carol vs Alice": "D"}
CONTEXT_ACTIONS = {
    "Alice vs Bob":   ("help_bob",   "decline_bob",   "delay_bob"),
    "Alice vs Carol": ("help_alice", "decline_alice", "teach_alice"),
    "Alice vs Dave":  ("help_dave",  "decline_dave",  "suggest_dave"),
    "Carol vs Alice": ("carol_help_regret",
                       "carol_decline_regret",
                       "carol_reciprocate_regret"),
}
CONTEXT_DECLINE = {"Alice vs Bob":   "decline_bob",
                   "Alice vs Carol": "decline_alice",
                   "Alice vs Dave":  "decline_dave",
                   "Carol vs Alice": "carol_decline_regret"}
CONTEXT_CSV = {"Alice vs Bob":   "alice_reg",
               "Alice vs Carol": "alice_reg",
               "Alice vs Dave":  "alice_reg",
               "Carol vs Alice": "carol_reg"}


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
        "carol_reg": "carol_cfr_regrets.csv",
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
    for d in per_seed.values():
        df = d.get(df_key)
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
    return pd.Series(arr).rolling(window, min_periods=1,
                                  center=True).median().to_numpy()


# ---------------------------------------------------------------------------
# FIGURE 1 -- 4-agent personality
# ---------------------------------------------------------------------------

def _ocean_panel_dynamic(ax, per_seed, df_key, col_for, grid, title):
    for trait in OCEAN:
        s = stack_on_grid(per_seed, df_key, col_for(trait), grid)
        if s is None:
            continue
        m  = smooth(s.mean(axis=0))
        sd = smooth(s.std(axis=0))
        c  = OCEAN_COLORS[trait]
        ax.plot(grid, m, color=c, linewidth=2.0, label=OCEAN_LABELS[trait])
        ax.fill_between(grid, m - sd, m + sd, color=c, alpha=0.18)
    ax.axhline(0.0, color="grey", linewidth=0.7, linestyle="--")
    ax.set_xlabel("Episode")
    ax.set_ylabel("Trait value")
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(title, fontsize=12, fontweight="bold")
    style_ax(ax)
    ax.legend(loc="lower right", fontsize=9, frameon=False, ncol=5,
              columnspacing=0.9, handlelength=1.2)


def _ocean_panel_static(ax, stance, grid, title, subtitle):
    for trait in OCEAN:
        v = stance[trait]
        c = OCEAN_COLORS[trait]
        ax.plot(grid, np.full_like(grid, v, dtype=float),
                color=c, linewidth=2.4, label=OCEAN_LABELS[trait])
    ax.axhline(0.0, color="grey", linewidth=0.7, linestyle="--")
    ax.set_xlabel("Episode")
    ax.set_ylabel("Trait value")
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.text(0.02, 0.96, subtitle, transform=ax.transAxes,
            fontsize=9, va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.3",
                      facecolor="white", edgecolor="grey", alpha=0.85))
    style_ax(ax)
    ax.legend(loc="lower right", fontsize=9, frameon=False, ncol=5,
              columnspacing=0.9, handlelength=1.2)


def fig_4agent_personality(per_seed, grid):
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.6),
                             sharex=True, sharey=True)
    fig.suptitle("Per-agent OCEAN personality "
                 f"(mean $\\pm$ std across {len(per_seed)} seeds, "
                 f"{grid[-1]} episodes)",
                 fontsize=14, fontweight="bold")
    fig.text(0.5, 0.005,
             "Carol initialised at A=$-$0.4, N=0, O=+0.2, C=$-$0.2, E=+0.2 "
             "(moderately exploitative starting profile). "
             "Alice's late-episode A and E recovery (ep $\\sim$1500+) "
             "reflects closed-loop adaptation to Carol's rising reciprocity. "
             "Bob and Dave are static partners: their flat lines show the "
             "OCEAN profile of their cooperative (help_*) action; their "
             "reliability and reciprocity values drive reward dynamics in "
             "their contexts but their personality is not learned.",
             ha="center", fontsize=9, style="italic", wrap=True)

    _ocean_panel_dynamic(axes[0, 0], per_seed, "alice",
                         lambda t: t, grid,
                         "Alice (CFR learner)")
    _ocean_panel_static (axes[0, 1], BOB_HELP_STANCE, grid,
                         "Bob (static partner)",
                         "reliability=0.6\nreciprocity=0.4")
    _ocean_panel_dynamic(axes[1, 0], per_seed, "carol",
                         lambda t: f"carol_{t}", grid,
                         "Carol (CFR + adaptive reciprocity)")
    _ocean_panel_static (axes[1, 1], DAVE_HELP_STANCE, grid,
                         "Dave (static partner)",
                         "reliability=0.8\nreciprocity=0.9")

    plt.tight_layout()
    out = RESULTS / "fig1_personality_4agents.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# FIGURE 2 -- Leduc-style: log-log avg regret + decline probability
# ---------------------------------------------------------------------------

def regret_matching_prob(R_actions):
    """Return regret-matching probabilities for one row of regrets.

    R_actions: array of shape (n_actions,). Returns probabilities where
    sigma(a) = max(R(a), 0) / sum_b max(R(b), 0). Uniform if all <= 0.
    """
    pos = np.maximum(R_actions, 0.0)
    total = pos.sum()
    if total <= 0:
        return np.ones_like(R_actions) / len(R_actions)
    return pos / total


def avg_regret_curve(per_seed, csv_key, action_cols, grid):
    """Average per-info-set regret max_a max(R_a, 0) / t across seeds."""
    rows = []
    for d in per_seed.values():
        df = d.get(csv_key)
        if df is None:
            continue
        cols = [c for c in action_cols if c in df.columns]
        if not cols:
            continue
        R = df[cols].to_numpy(dtype=float)
        worst = np.maximum(R, 0.0).max(axis=1)
        eps = df["episode"].to_numpy(dtype=float)
        eps_safe = np.maximum(eps, 1.0)
        avg = worst / eps_safe
        rows.append(np.interp(grid, eps, avg))
    if not rows:
        return None
    return np.vstack(rows)


def decline_prob_curve(per_seed, csv_key, action_cols, decline_col, grid):
    rows = []
    for d in per_seed.values():
        df = d.get(csv_key)
        if df is None or decline_col not in df.columns:
            continue
        cols = [c for c in action_cols if c in df.columns]
        if not cols:
            continue
        R = df[cols].to_numpy(dtype=float)
        probs = np.array([regret_matching_prob(r) for r in R])
        decline_idx = cols.index(decline_col)
        p_decline = probs[:, decline_idx]
        eps = df["episode"].to_numpy(dtype=float)
        rows.append(np.interp(grid, eps, p_decline))
    if not rows:
        return None
    return np.vstack(rows)


def fig_convergence_behavior(per_seed, grid):
    fig, axes = plt.subplots(1, 2, figsize=(14.0, 6.0))
    fig.suptitle("No-regret stationarity and behavioural outcome per decision context "
                 f"(mean $\\pm$ std across {len(per_seed)} seeds)",
                 fontsize=13, fontweight="bold")
    fig.text(0.5, 0.005,
             "Contested context (Alice $\\leftrightarrow$ Carol, red) shows "
             "a clear V-shape: regret rises during Carol's exploitation phase "
             "then descends as Alice and Carol's adaptive reciprocity reach a "
             "stable mutual best-response. Uncontested contexts (Bob, Dave, "
             "Carol-internal) settle to constant low regret early. The "
             "convergence target is no-regret stationarity in personality "
             "space -- a stable mutual best-response between two adaptive "
             "agents under non-stationary reciprocity dynamics -- which is "
             "distinct from the Nash equilibrium target of canonical CFR "
             "(Zinkevich et al., 2008) since neither stationarity nor "
             "zero-sum payoffs hold in our setting.",
             ha="center", fontsize=9, style="italic", wrap=True)

    # --- Left: log-log average regret ---
    ax = axes[0]
    for ctx, color in CONTEXT_COLOR.items():
        s = avg_regret_curve(per_seed,
                             CONTEXT_CSV[ctx],
                             CONTEXT_ACTIONS[ctx],
                             grid)
        if s is None:
            continue
        m  = smooth(s.mean(axis=0))
        sd = smooth(s.std(axis=0))
        valid = m > 1e-6
        ax.plot(grid[valid], m[valid], color=color, linewidth=2.0,
                marker=CONTEXT_MARKER[ctx], markersize=4,
                markevery=max(1, len(grid) // 33), label=ctx)
        ax.fill_between(grid[valid],
                        np.maximum(m[valid] - sd[valid], 1e-6),
                        m[valid] + sd[valid],
                        color=color, alpha=0.15)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Episode (log scale)")
    ax.set_ylabel("Average per-info-set regret  $\\bar R(t)/t$")
    ax.set_title("Convergence:  $\\bar R(t)/t \\to 0$",
                 fontsize=12, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(alpha=0.25, which="both")
    ax.legend(loc="lower left", fontsize=9, frameon=False)

    # --- Right: decline probability over training ---
    ax = axes[1]
    carol_start_end = None
    for ctx, color in CONTEXT_COLOR.items():
        s = decline_prob_curve(per_seed,
                               CONTEXT_CSV[ctx],
                               CONTEXT_ACTIONS[ctx],
                               CONTEXT_DECLINE[ctx],
                               grid)
        if s is None:
            continue
        m  = smooth(s.mean(axis=0))
        sd = smooth(s.std(axis=0))
        ax.plot(grid, m, color=color, linewidth=2.0,
                marker=CONTEXT_MARKER[ctx], markersize=4,
                markevery=max(1, len(grid) // 33), label=ctx)
        ax.fill_between(grid, m - sd, m + sd, color=color, alpha=0.18)
        if ctx == "Alice vs Carol":
            carol_start_end = (m[0], m[-1])
    ax.axhline(1.0/3.0, color="grey", linewidth=0.7, linestyle="--",
               label="uniform 1/3")

    peaks = []
    for d in per_seed.values():
        df = d.get("alice_reg")
        if df is not None and "decline_alice" in df.columns:
            peaks.append(int(df.loc[df["decline_alice"].idxmax(), "episode"]))
    if peaks:
        phase_ep = int(np.mean(peaks))
        ax.axvline(phase_ep, color="#7F1D1D", linewidth=1.2,
                   linestyle=":", alpha=0.85)
        ax.text(phase_ep + 30, 0.92,
                f"phase transition\n(ep $\\approx${phase_ep})",
                fontsize=9, color="#7F1D1D", va="top", ha="left")

    if carol_start_end is not None:
        s0, s1 = carol_start_end
        ax.text(0.98, 0.05,
                f"Alice vs Carol  P(decline):\n"
                f"   start = {s0:.2f}\n"
                f"   end   = {s1:.2f}",
                transform=ax.transAxes,
                fontsize=9, va="bottom", ha="right",
                bbox=dict(boxstyle="round,pad=0.35",
                          facecolor="white", edgecolor="grey",
                          alpha=0.92))

    ax.set_xlabel("Episode")
    ax.set_ylabel(r"$P(\mathit{decline} \mid \mathrm{context})$")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title("Behavioural outcome:  P(decline)",
                 fontsize=12, fontweight="bold")
    style_ax(ax)
    ax.legend(loc="upper left", fontsize=9, frameon=False)

    plt.tight_layout()
    out = RESULTS / "fig2_convergence_behavior.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    per_seed = {s: load_seed(d) for s, d in seeds.items()}

    max_eps = []
    for d in per_seed.values():
        for k in ("alice", "alice_reg", "carol", "carol_reg"):
            df = d.get(k)
            if df is not None and "episode" in df.columns and len(df):
                max_eps.append(int(df["episode"].max()))
    n_eps = min(max_eps) if max_eps else 0
    grid = np.arange(1, n_eps + 1)
    print(f"Loaded {len(per_seed)} seeds, common grid 1..{n_eps}")

    fig_4agent_personality(per_seed, grid)
    fig_convergence_behavior(per_seed, grid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
