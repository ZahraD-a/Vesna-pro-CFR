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
OUT_OCEAN  = RESULTS / "ocean"
OUT_REGRET = RESULTS / "regret"
OUT_OCEAN.mkdir(parents=True, exist_ok=True)
OUT_REGRET.mkdir(parents=True, exist_ok=True)

# CFR iterations per episode in our experiment loop. record_outcome is
# fired ~30 times per episode by workplace_cfr_learning.asl, which is
# what populates cfr_trace.csv / carol_cfr_trace.csv. We use this ratio
# to project the per-episode personality CSVs onto a per-iteration
# x-axis so all paper figures share the Leduc-style "CFR iteration t"
# convention (Zinkevich et al., 2008).
ITER_PER_EP = 30

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
# One marker shape per trait, Leduc-style sparse markers along each curve.
OCEAN_MARKERS = {
    "openness":          "^",   # triangle up
    "conscientiousness": "o",   # circle
    "extraversion":      "s",   # square
    "agreeableness":     "D",   # diamond
    "neuroticism":       "v",   # triangle down
}
# Number of markers placed along each curve (Leduc figures use ~10–11).
N_MARKERS = 11


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
        "alice":       "personality_evolution.csv",
        "carol":       "carol_personality_evolution.csv",
        "alice_reg":   "cfr_regrets.csv",
        "carol_reg":   "carol_cfr_regrets.csv",
        "alice_trace": "cfr_trace.csv",
        "carol_trace": "carol_cfr_trace.csv",
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
            if "iteration" in df.columns:
                df["iteration"] = pd.to_numeric(df["iteration"],
                                                errors="coerce")
                df = df.dropna(subset=["iteration"]).astype({"iteration": int})
                df = df.sort_values("iteration")
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
    # X axis is CFR iteration t = episode * ITER_PER_EP. Leduc-style
    # styling: thin line, sparse filled markers (one shape per trait),
    # faint cross-seed std band.
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


def _ocean_panel_static(ax, stance, grid, title, subtitle):
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


def fig_4agent_personality(per_seed, grid):
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.6),
                             sharex=True, sharey=True)
    fig.suptitle("Per-agent OCEAN personality "
                 f"(mean $\\pm$ std across {len(per_seed)} seeds, "
                 f"{grid[-1] * ITER_PER_EP} CFR iterations)",
                 fontsize=14, fontweight="bold")

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

    # Shared legend at the bottom (Leduc-style), one entry per OCEAN trait.
    handles = []
    for trait in OCEAN:
        handles.append(plt.Line2D(
            [0], [0], color=OCEAN_COLORS[trait], linewidth=1.4,
            marker=OCEAN_MARKERS[trait], markersize=7,
            markerfacecolor=OCEAN_COLORS[trait],
            markeredgecolor=OCEAN_COLORS[trait],
            label=OCEAN_LABELS[trait]))
    fig.legend(handles=handles, loc="lower center", ncol=5,
               frameon=False, fontsize=11, columnspacing=2.4,
               handlelength=2.0, bbox_to_anchor=(0.5, -0.01))

    plt.tight_layout(rect=(0, 0.04, 1, 1))
    out = OUT_OCEAN / "fig1_personality_4agents.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# FIGURE 2 -- Per-agent, per-context cumulative CFR regret
# ---------------------------------------------------------------------------

def _trace_t_grid(per_seed, trace_key, target_points=2000):
    """Build a per-trace iteration grid clipped to the shortest trace
    across seeds. Avoids np.interp's edge-extrapolation artefact when
    Alice (60 000 iter) and Carol (20 000 iter) traces have different
    lengths in the same experiment."""
    max_iters = []
    for d in per_seed.values():
        df = d.get(trace_key)
        if df is not None and "iteration" in df.columns and len(df):
            max_iters.append(int(df["iteration"].max()))
    if not max_iters:
        return None
    n = min(max_iters)
    step = max(1, n // target_points)
    return np.arange(1, n + 1, step)


def _stack_regret_per_action(per_seed, trace_key, action_cols, t_grid):
    """For each action in `action_cols`, return an array of shape
    (n_seeds, len(t_grid)) of cumulative regret values, interpolated onto
    the iteration grid. Returns dict {action: stacked_array}.

    The caller is responsible for passing a t_grid clipped to the
    actual range of `trace_key` — we no longer fall back to
    extrapolation past the last logged iteration."""
    out = {a: [] for a in action_cols}
    for d in per_seed.values():
        df = d.get(trace_key)
        if df is None:
            continue
        t = df["iteration"].to_numpy(dtype=float)
        for a in action_cols:
            if a not in df.columns:
                continue
            r = df[a].to_numpy(dtype=float)
            # Clip the grid to this trace's actual range so np.interp
            # never extends a flat tail past the last logged iteration.
            mask = t_grid <= t.max()
            row = np.full_like(t_grid, np.nan, dtype=float)
            row[mask] = np.interp(t_grid[mask], t, r)
            out[a].append(row)
    return {a: np.vstack(rows) for a, rows in out.items() if rows}


def fig_convergence_behavior(per_seed):
    """Per-agent, per-context cumulative CFR regret over iterations.

    Each panel uses its own iteration grid built from the trace it
    reads:
      - Alice panels: alice_trace iterations (~60 000 = 30 per episode)
      - Carol panel:  carol_trace iterations (~20 000 = 10 per episode)
    No interpolation past the last logged iteration — Carol's curve
    stops at her real iteration count, no flat extrapolation tail.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.0))
    fig.suptitle("Per-agent CFR cumulative regret "
                 f"(mean $\\pm$ std across {len(per_seed)} seeds)",
                 fontsize=13, fontweight="bold")

    ACTION_COLOR = {
        # cooperative actions in green, declining in red, third in orange
        "help": "#27AE60", "decline": "#C0392B", "third": "#E67E22",
    }
    # Leduc-style: one marker per action role (consistent across panels).
    ACTION_MARKER = {"help": "^", "decline": "o", "third": "s"}

    alice_grid = _trace_t_grid(per_seed, "alice_trace")
    carol_grid = _trace_t_grid(per_seed, "carol_trace")

    # (panel_title, csv_key, t_grid, [(col, role, label), ...])
    PANELS = [
        ("Alice vs Bob   (self-CFR)",
         "alice_trace", alice_grid,
         [("help_bob",     "help",    "help"),
          ("decline_bob",  "decline", "decline"),
          ("delay_bob",    "third",   "delay")]),
        ("Alice vs Carol  (self-CFR)",
         "alice_trace", alice_grid,
         [("help_alice",    "help",    "help"),
          ("decline_alice", "decline", "decline"),
          ("teach_alice",   "third",   "teach")]),
        ("Alice vs Dave   (self-CFR)",
         "alice_trace", alice_grid,
         [("help_dave",     "help",    "help"),
          ("decline_dave",  "decline", "decline"),
          ("suggest_dave",  "third",   "suggest")]),
        ("Carol vs Alice  (observational CFR)",
         "carol_trace", carol_grid,
         [("carol_help_regret",        "help",    "help"),
          ("carol_decline_regret",     "decline", "decline"),
          ("carol_reciprocate_regret", "third",   "reciprocate")]),
    ]

    for ax, (title, key, panel_grid, actions) in zip(axes.flat, PANELS):
        if panel_grid is None:
            continue
        markevery = max(1, len(panel_grid) // N_MARKERS)
        cols = [a[0] for a in actions]
        stacks = _stack_regret_per_action(per_seed, key, cols, panel_grid)
        for col, role, label in actions:
            s = stacks.get(col)
            if s is None:
                continue
            color  = ACTION_COLOR[role]
            marker = ACTION_MARKER[role]
            m  = smooth(np.nanmean(s, axis=0))
            sd = smooth(np.nanstd(s, axis=0))
            ax.plot(panel_grid, m, color=color, linewidth=1.4,
                    marker=marker, markersize=6, markevery=markevery,
                    markerfacecolor=color, markeredgecolor=color,
                    label=label)
            ax.fill_between(panel_grid, m - sd, m + sd,
                            color=color, alpha=0.10, linewidth=0)
        ax.axhline(0.0, color="grey", linewidth=0.5, linestyle="--")
        ax.set_xlabel(rf"CFR iteration  $t$  (max {panel_grid[-1]})")
        ax.set_ylabel("Cumulative regret  $R_t(a)$")
        ax.set_title(title, fontsize=12)
        style_ax(ax)
        ax.legend(loc="best", fontsize=9, frameon=False, handlelength=2.0)

    plt.tight_layout()
    out = OUT_REGRET / "fig2_regret_per_agent.png"
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

    # Per-trace iteration grids are built inside fig_convergence_behavior
    # so Alice (max ~60 000) and Carol (max ~20 000) each plot against
    # their own range — no flat-tail extrapolation past the shorter trace.
    max_alice = max(int(d["alice_trace"]["iteration"].max())
                    for d in per_seed.values()
                    if d.get("alice_trace") is not None
                    and "iteration" in d["alice_trace"].columns)
    max_carol = max(int(d["carol_trace"]["iteration"].max())
                    for d in per_seed.values()
                    if d.get("carol_trace") is not None
                    and "iteration" in d["carol_trace"].columns)
    print(f"Loaded {len(per_seed)} seeds: {n_eps} episodes, "
          f"Alice trace max iter {max_alice}, Carol trace max iter {max_carol}.")

    fig_4agent_personality(per_seed, grid)
    fig_convergence_behavior(per_seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
