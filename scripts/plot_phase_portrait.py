#!/usr/bin/env python3
"""Phase portrait of the Alice-Carol Agreeableness co-evolution.

This is the headline figure for the co-evolutionary equilibrium claim:
each axis is one agent's Agreeableness, the trajectory is episode-coloured
so that the reader sees the *path* through joint trait space, not just
two separate time series.

Layout: 1x2 panels.
    (0) Joint phase portrait. Faint per-seed traces in light grey, the
        cross-seed mean trajectory as a thick episode-coloured line. A
        navy circle marks the non-cooperative start (Carol's exploitative
        initial type, A = -0.4) and a red star marks the cooperative
        endpoint reached after ~1500 episodes.
    (1) Endpoint distribution. Per-seed start positions vs the pooled
        last-100-episode endpoints, with centroids and an explicit +/- std
        callout.

Convention: Carol's Agreeableness on the x-axis (the "leading" variable
adapting through reciprocity), Alice's Agreeableness on the y-axis (the
responder).
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


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


def load_pair(seed_dir):
    a = pd.read_csv(seed_dir / "personality_evolution.csv")
    c = pd.read_csv(seed_dir / "carol_personality_evolution.csv")
    a["episode"] = pd.to_numeric(a["episode"], errors="coerce")
    c["episode"] = pd.to_numeric(c["episode"], errors="coerce")
    a = a.dropna(subset=["episode"]).astype({"episode": int}).sort_values("episode")
    c = c.dropna(subset=["episode"]).astype({"episode": int}).sort_values("episode")
    return a, c


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

    per_seed_alice, per_seed_carol = {}, {}
    n_eps = None
    for s, d in seeds.items():
        a, c = load_pair(d)
        per_seed_alice[s] = a
        per_seed_carol[s] = c
        local = min(int(a["episode"].max()), int(c["episode"].max()))
        n_eps = local if n_eps is None else min(n_eps, local)
    grid = np.arange(0, n_eps + 1)

    alice_A, carol_A = [], []
    for s in seeds:
        a = per_seed_alice[s]
        c = per_seed_carol[s]
        alice_A.append(np.interp(grid,
                                 a["episode"].to_numpy(),
                                 a["agreeableness"].to_numpy(dtype=float)))
        carol_A.append(np.interp(grid,
                                 c["episode"].to_numpy(),
                                 c["carol_agreeableness"].to_numpy(dtype=float)))
    alice_A = np.vstack(alice_A)
    carol_A = np.vstack(carol_A)

    mean_alice = smooth(alice_A.mean(axis=0))
    mean_carol = smooth(carol_A.mean(axis=0))

    end_alice_mean = mean_alice[-1]
    end_carol_mean = mean_carol[-1]
    end_alice_std = alice_A[:, -1].std()
    end_carol_std = carol_A[:, -1].std()
    start_alice = mean_alice[0]
    start_carol = mean_carol[0]

    fig, axes = plt.subplots(1, 2, figsize=(14.0, 6.6),
                             gridspec_kw={"width_ratios": [1.4, 1.0]})
    fig.suptitle("Co-evolutionary equilibrium in personality space "
                 f"(Carol Agreeableness  vs  Alice Agreeableness, "
                 f"{len(seeds)} seeds, {n_eps} episodes)",
                 fontsize=13, fontweight="bold")
    fig.text(0.5, 0.005,
             "Joint trajectories start in the non-cooperative lower-left "
             f"quadrant (Carol A={start_carol:+.2f}, Alice A={start_alice:+.2f}) "
             f"and converge to a cooperative upper-right cluster "
             f"(Carol A={end_carol_mean:+.2f}$\\pm${end_carol_std:.2f}, "
             f"Alice A={end_alice_mean:+.2f}$\\pm${end_alice_std:.2f}). "
             "The episode-coloured progression shows that mutual "
             "best-response in personality space emerges from the closed "
             "loop of regret-matching personality projection and adaptive "
             "reciprocity, despite no explicit coordination signal between "
             "the two agents.",
             ha="center", fontsize=9, style="italic", wrap=True)

    # --- Left panel: joint trajectory in (Carol A, Alice A) space ---
    ax = axes[0]
    for i in range(alice_A.shape[0]):
        ax.plot(carol_A[i], alice_A[i],
                color="grey", linewidth=0.6, alpha=0.30)

    pts = np.array([mean_carol, mean_alice]).T.reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    norm = Normalize(vmin=0, vmax=n_eps)
    lc = LineCollection(segs, cmap="viridis", norm=norm, linewidth=3.2)
    lc.set_array(grid[:-1])
    ax.add_collection(lc)

    ax.scatter([start_carol], [start_alice],
               color="#1F3A93", s=140, marker="o", zorder=6,
               edgecolor="black", linewidth=1.2,
               label=f"start  (ep 0):  Carol A={start_carol:+.2f}, "
                     f"Alice A={start_alice:+.2f}")
    ax.scatter([end_carol_mean], [end_alice_mean],
               color="#B22222", s=200, marker="*", zorder=6,
               edgecolor="black", linewidth=1.2,
               label=f"end  (ep {n_eps}):  Carol A={end_carol_mean:+.2f},"
                     f" Alice A={end_alice_mean:+.2f}")

    ax.axhline(0.0, color="grey", linewidth=0.6, linestyle="--")
    ax.axvline(0.0, color="grey", linewidth=0.6, linestyle="--")
    ax.set_xlabel("Carol Agreeableness")
    ax.set_ylabel("Alice Agreeableness")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_title("Joint trajectory in trait space",
                 fontsize=12, fontweight="bold")
    style_ax(ax)
    ax.legend(loc="lower right", fontsize=9, frameon=False)

    cbar = fig.colorbar(ScalarMappable(norm=norm, cmap="viridis"),
                        ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("Episode")
    cbar.outline.set_visible(False)

    # --- Right panel: endpoint distribution ---
    ax = axes[1]
    tail_eps = max(1, n_eps - 100)
    tail_mask = grid >= tail_eps
    end_alice = alice_A[:, tail_mask].ravel()
    end_carol = carol_A[:, tail_mask].ravel()
    ax.scatter(end_carol, end_alice, color="#B22222",
               s=10, alpha=0.20,
               label=f"endpoints (last 100 ep, all seeds)")
    ax.scatter(carol_A[:, 0], alice_A[:, 0], color="#1F3A93",
               s=46, marker="o", edgecolor="black", linewidth=0.6,
               label="seeds at ep 0")
    ax.scatter([end_carol_mean], [end_alice_mean],
               color="#B22222", s=200, marker="*", zorder=5,
               edgecolor="black", linewidth=1.2)

    ax.text(0.98, 0.05,
            f"endpoint centroid:\n"
            f"   Carol A = {end_carol_mean:+.2f} $\\pm$ {end_carol_std:.2f}\n"
            f"   Alice A = {end_alice_mean:+.2f} $\\pm$ {end_alice_std:.2f}",
            transform=ax.transAxes,
            fontsize=9, va="bottom", ha="right",
            bbox=dict(boxstyle="round,pad=0.4",
                      facecolor="white", edgecolor="grey", alpha=0.92))

    ax.axhline(0.0, color="grey", linewidth=0.6, linestyle="--")
    ax.axvline(0.0, color="grey", linewidth=0.6, linestyle="--")
    ax.set_xlabel("Carol Agreeableness")
    ax.set_ylabel("Alice Agreeableness")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_title("Endpoint distribution (last 100 episodes)",
                 fontsize=12, fontweight="bold")
    style_ax(ax)
    ax.legend(loc="upper left", fontsize=9, frameon=False)

    plt.tight_layout()
    out = RESULTS / "fig3_phase_portrait.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)

    print(f"\nStart  mean: Carol A = {start_carol:+.3f}, "
          f"Alice A = {start_alice:+.3f}")
    print(f"End    mean: Carol A = {end_carol_mean:+.3f}, "
          f"Alice A = {end_alice_mean:+.3f}")
    print(f"End    std : Carol A = {end_carol_std:.3f}, "
          f"Alice A = {end_alice_std:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
