#!/usr/bin/env python3
"""Alice vs Carol agreeableness convergence plot.

Shows Alice's and Carol's agreeableness on the same axis so the crossing
point — the social-trust-reversal moment where Carol transitions from
exploitative to cooperative — is visible.

Also marks the mean crossing episode across seeds with a vertical line.

Reads results/seed_<n>/personality_evolution.csv (Alice)
      results/seed_<n>/carol_personality_evolution.csv (Carol)

Produces:
    results/ocean/convergence_agreeableness.png
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT    = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT     = RESULTS / "ocean"
OUT.mkdir(parents=True, exist_ok=True)

ITER_PER_EP = 30

ALICE_COLOR = "#1F3A93"   # navy
CAROL_COLOR = "#B22222"   # firebrick


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


def load_agreeableness(seed_dir):
    alice_path = seed_dir / "personality_evolution.csv"
    carol_path = seed_dir / "carol_personality_evolution.csv"
    result = {}
    if alice_path.exists():
        df = pd.read_csv(alice_path)
        df["episode"] = pd.to_numeric(df["episode"], errors="coerce")
        df = df.dropna(subset=["episode"]).astype({"episode": int})
        result["alice"] = df.sort_values("episode")
    if carol_path.exists():
        df = pd.read_csv(carol_path)
        df["episode"] = pd.to_numeric(df["episode"], errors="coerce")
        df = df.dropna(subset=["episode"]).astype({"episode": int})
        result["carol"] = df.sort_values("episode")
    return result


def find_crossing_episode(alice_a, carol_a, episodes):
    """Find the first episode where Carol's agreeableness exceeds Alice's."""
    diff = carol_a - alice_a
    for i in range(1, len(diff)):
        if diff[i - 1] < 0 and diff[i] >= 0:
            return episodes[i]
    return None


def smooth(arr, window=21):
    if arr is None or len(arr) < window:
        return arr
    return pd.Series(arr).rolling(window, min_periods=1, center=True).median().to_numpy()


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    per_seed = {s: load_agreeableness(d) for s, d in seeds.items()}

    max_eps = max(
        int(d["alice"]["episode"].max())
        for d in per_seed.values()
        if "alice" in d
    )
    grid = np.arange(0, max_eps + 1)
    x    = grid * ITER_PER_EP

    alice_rows = []
    carol_rows = []
    crossings  = []

    for d in per_seed.values():
        if "alice" not in d or "carol" not in d:
            continue
        alice_a = np.interp(grid,
                            d["alice"]["episode"].to_numpy(),
                            d["alice"]["agreeableness"].to_numpy(dtype=float))
        carol_a = np.interp(grid,
                            d["carol"]["episode"].to_numpy(),
                            d["carol"]["carol_agreeableness"].to_numpy(dtype=float))
        alice_rows.append(alice_a)
        carol_rows.append(carol_a)

        ep = find_crossing_episode(alice_a, carol_a, grid)
        if ep is not None:
            crossings.append(ep)

    alice_arr = np.vstack(alice_rows)
    carol_arr = np.vstack(carol_rows)

    alice_mean = smooth(alice_arr.mean(axis=0))
    alice_std  = smooth(alice_arr.std(axis=0))
    carol_mean = smooth(carol_arr.mean(axis=0))
    carol_std  = smooth(carol_arr.std(axis=0))

    mean_crossing_ep  = int(np.mean(crossings))  if crossings else None
    std_crossing_ep   = int(np.std(crossings))   if crossings else None
    mean_crossing_t   = mean_crossing_ep * ITER_PER_EP if mean_crossing_ep else None

    print(f"Loaded {len(alice_rows)} seeds.")
    if crossings:
        print(f"Crossing episodes: mean={mean_crossing_ep} ± {std_crossing_ep} "
              f"(t = {mean_crossing_t})")
    else:
        print("No crossing detected.")

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(x, alice_mean, color=ALICE_COLOR, linewidth=2.0,
            label="Alice agreeableness")
    ax.fill_between(x, alice_mean - alice_std, alice_mean + alice_std,
                    color=ALICE_COLOR, alpha=0.15, linewidth=0)

    ax.plot(x, carol_mean, color=CAROL_COLOR, linewidth=2.0,
            label="Carol agreeableness")
    ax.fill_between(x, carol_mean - carol_std, carol_mean + carol_std,
                    color=CAROL_COLOR, alpha=0.15, linewidth=0)

    # Mark starting points
    ax.scatter([0], [0.0],  color=ALICE_COLOR, s=80, zorder=5)
    ax.scatter([0], [-0.4], color=CAROL_COLOR, s=80, zorder=5)
    ax.annotate("Alice starts: 0.0",  xy=(0, 0.0),
                xytext=(x[-1] * 0.04, 0.06),
                fontsize=9, color=ALICE_COLOR)
    ax.annotate("Carol starts: -0.4", xy=(0, -0.4),
                xytext=(x[-1] * 0.04, -0.46),
                fontsize=9, color=CAROL_COLOR)

    # Mark crossing
    if mean_crossing_t is not None:
        crossing_alice = float(np.interp(mean_crossing_ep, grid, alice_mean))
        ax.axvline(mean_crossing_t, color="grey", linewidth=1.2,
                   linestyle="--", alpha=0.7)
        ax.scatter([mean_crossing_t], [crossing_alice],
                   color="black", s=100, zorder=6, marker="*")
        ax.annotate(
            f"Crossing\n$t \\approx {mean_crossing_t:,}$\n(ep {mean_crossing_ep} ± {std_crossing_ep})",
            xy=(mean_crossing_t, crossing_alice),
            xytext=(mean_crossing_t + x[-1] * 0.04, crossing_alice - 0.18),
            fontsize=9, color="black",
            arrowprops=dict(arrowstyle="->", color="black", lw=1.0)
        )

    # Mark final values
    ax.annotate(f"Alice final: {alice_mean[-1]:+.2f}",
                xy=(x[-1], alice_mean[-1]),
                xytext=(x[-1] - x[-1] * 0.18, alice_mean[-1] + 0.06),
                fontsize=9, color=ALICE_COLOR)
    ax.annotate(f"Carol final: {carol_mean[-1]:+.2f}",
                xy=(x[-1], carol_mean[-1]),
                xytext=(x[-1] - x[-1] * 0.18, carol_mean[-1] - 0.08),
                fontsize=9, color=CAROL_COLOR)

    ax.axhline(0.0, color="grey", linewidth=0.8, linestyle="--", alpha=0.5)

    ax.set_xlim(0, x[-1])
    ax.set_ylim(-0.65, 0.55)
    ax.set_xlabel(r"CFR iteration  $t$", fontsize=11)
    ax.set_ylabel("Agreeableness  $A_t$", fontsize=11)
    ax.set_title(
        "Social trust reversal: Alice and Carol agreeableness over time\n"
        f"(mean ± std across {len(alice_rows)} seeds, "
        f"{max_eps * ITER_PER_EP} CFR iterations)",
        fontsize=12, fontweight="bold"
    )

    region_before = mpatches.Patch(color="grey", alpha=0.15,
                                    label="Carol exploitative (A < Alice A)")
    region_after  = mpatches.Patch(color="green", alpha=0.10,
                                    label="Carol cooperative (A > Alice A)")
    if mean_crossing_t is not None:
        ax.axvspan(0, mean_crossing_t, alpha=0.05, color="red")
        ax.axvspan(mean_crossing_t, x[-1], alpha=0.05, color="green")

    handles, labels = ax.get_legend_handles_labels()
    handles += [region_before, region_after]
    ax.legend(handles=handles, loc="lower right", fontsize=9, frameon=False)

    style_ax(ax)
    plt.tight_layout()

    out = OUT / "convergence_agreeableness.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
