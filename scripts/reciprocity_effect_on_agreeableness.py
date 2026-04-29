#!/usr/bin/env python3
"""Reciprocity effect on agreeableness convergence.

Two-panel figure sharing the same x-axis:
  Top:    Alice vs Carol agreeableness — the trust reversal crossing
  Bottom: Carol's adapted reciprocity rising in response to Alice's behaviour,
          with the exploitative flag (phi) deactivation marked

The shared vertical line on both panels makes the causal link crystal clear:
Carol's rising reciprocity and her agreeableness crossing Alice both happen
in the same early window, driven by the same regret signal.

Produces:
    results/ocean/reciprocity_effect_on_agreeableness.png
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

ROOT    = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT     = RESULTS / "ocean"
OUT.mkdir(parents=True, exist_ok=True)

ITER_PER_EP   = 30
ALICE_COLOR   = "#1F3A93"   # navy
CAROL_COLOR   = "#B22222"   # firebrick
RECIP_COLOR   = "#E67E22"   # orange
INNATE_COLOR  = "#95A5A6"   # grey


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
    for key, fname in [
        ("alice",   "personality_evolution.csv"),
        ("carol",   "carol_personality_evolution.csv"),
        ("recip",   "adapted_reciprocity.csv"),
    ]:
        p = seed_dir / fname
        if p.exists():
            df = pd.read_csv(p)
            df["episode"] = pd.to_numeric(df["episode"], errors="coerce")
            df = df.dropna(subset=["episode"]).astype({"episode": int})
            out[key] = df.sort_values("episode")
    return out


def smooth(arr, window=21):
    if arr is None or len(arr) < window:
        return arr
    return pd.Series(arr).rolling(window, min_periods=1, center=True).median().to_numpy()


def find_crossing(alice_a, carol_a, grid):
    diff = carol_a - alice_a
    for i in range(1, len(diff)):
        if diff[i - 1] < 0 and diff[i] >= 0:
            return grid[i]
    return None


def find_phi_deactivation(phi, grid):
    """First episode where phi drops from 1 to 0."""
    for i in range(1, len(phi)):
        if phi[i - 1] == 1 and phi[i] == 0:
            return grid[i]
    return None


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    per_seed = {s: load_seed(d) for s, d in seeds.items()}

    max_eps = max(
        int(d["alice"]["episode"].max())
        for d in per_seed.values() if "alice" in d
    )
    grid = np.arange(0, max_eps + 1)
    x    = grid * ITER_PER_EP

    alice_rows, carol_rows, recip_rows = [], [], []
    crossings, phi_deacts = [], []

    for d in per_seed.values():
        if not all(k in d for k in ("alice", "carol", "recip")):
            continue

        alice_a = np.interp(grid, d["alice"]["episode"].to_numpy(),
                            d["alice"]["agreeableness"].to_numpy(dtype=float))
        carol_a = np.interp(grid, d["carol"]["episode"].to_numpy(),
                            d["carol"]["carol_agreeableness"].to_numpy(dtype=float))
        recip   = np.interp(grid, d["recip"]["episode"].to_numpy(),
                            d["recip"]["carol_adapted"].to_numpy(dtype=float))
        phi     = np.interp(grid, d["recip"]["episode"].to_numpy(),
                            d["recip"]["carol_phi"].to_numpy(dtype=float))

        alice_rows.append(alice_a)
        carol_rows.append(carol_a)
        recip_rows.append(recip)

        ep = find_crossing(alice_a, carol_a, grid)
        if ep is not None:
            crossings.append(ep)

        ep2 = find_phi_deactivation(np.round(phi).astype(int), grid)
        if ep2 is not None:
            phi_deacts.append(ep2)

    alice_mean = smooth(np.vstack(alice_rows).mean(axis=0))
    alice_std  = smooth(np.vstack(alice_rows).std(axis=0))
    carol_mean = smooth(np.vstack(carol_rows).mean(axis=0))
    carol_std  = smooth(np.vstack(carol_rows).std(axis=0))
    recip_mean = smooth(np.vstack(recip_rows).mean(axis=0))
    recip_std  = smooth(np.vstack(recip_rows).std(axis=0))

    crossing_ep = int(np.mean(crossings)) if crossings else None
    crossing_t  = crossing_ep * ITER_PER_EP if crossing_ep else None
    phi_ep      = int(np.mean(phi_deacts)) if phi_deacts else None
    phi_t       = phi_ep * ITER_PER_EP if phi_ep else None

    print(f"Loaded {len(alice_rows)} seeds.")
    if crossing_ep:
        print(f"Agreeableness crossing: ep {crossing_ep} ± {int(np.std(crossings))} (t={crossing_t})")
    if phi_ep:
        print(f"Phi deactivation:       ep {phi_ep} ± {int(np.std(phi_deacts))} (t={phi_t})")

    fig = plt.figure(figsize=(12, 9))
    fig.suptitle(
        "Reciprocity behaviour drives the social trust reversal\n"
        f"(mean ± std across {len(alice_rows)} seeds)",
        fontsize=13, fontweight="bold"
    )

    gs = gridspec.GridSpec(2, 1, figure=fig,
                           height_ratios=[1.2, 1],
                           hspace=0.12)
    ax_top = fig.add_subplot(gs[0])
    ax_bot = fig.add_subplot(gs[1], sharex=ax_top)

    # ── Top panel: agreeableness ──────────────────────────────────────────
    if crossing_t:
        ax_top.axvspan(0, crossing_t, alpha=0.06, color="red")
        ax_top.axvspan(crossing_t, x[-1], alpha=0.06, color="green")

    ax_top.plot(x, alice_mean, color=ALICE_COLOR, linewidth=2.0,
                label="Alice agreeableness")
    ax_top.fill_between(x, alice_mean - alice_std, alice_mean + alice_std,
                        color=ALICE_COLOR, alpha=0.12, linewidth=0)

    ax_top.plot(x, carol_mean, color=CAROL_COLOR, linewidth=2.0,
                label="Carol agreeableness")
    ax_top.fill_between(x, carol_mean - carol_std, carol_mean + carol_std,
                        color=CAROL_COLOR, alpha=0.12, linewidth=0)

    ax_top.axhline(0.0, color="grey", linewidth=0.7, linestyle="--", alpha=0.5)

    if crossing_t:
        cross_val = float(np.interp(crossing_ep, grid, alice_mean))
        ax_top.axvline(crossing_t, color="black", linewidth=1.2,
                       linestyle="--", alpha=0.6)
        ax_top.scatter([crossing_t], [cross_val], color="black", s=100,
                       zorder=6, marker="*")
        ax_top.annotate(
            f"Agreeableness crossing\nt ≈ {crossing_t:,}  (ep {crossing_ep})",
            xy=(crossing_t, cross_val),
            xytext=(crossing_t + x[-1] * 0.05, cross_val - 0.15),
            fontsize=8.5, color="black",
            arrowprops=dict(arrowstyle="->", color="black", lw=1.0)
        )

    ax_top.scatter([0], [0.0],  color=ALICE_COLOR, s=60, zorder=5)
    ax_top.scatter([0], [-0.4], color=CAROL_COLOR, s=60, zorder=5)
    ax_top.set_ylabel("Agreeableness  $A_t$", fontsize=10)
    ax_top.set_ylim(-0.60, 0.55)
    ax_top.set_xlim(0, x[-1])
    ax_top.legend(loc="lower right", fontsize=9, frameon=False)
    ax_top.set_title("Alice vs Carol agreeableness — trust reversal crossing",
                     fontsize=10)
    style_ax(ax_top)
    plt.setp(ax_top.get_xticklabels(), visible=False)

    # ── Bottom panel: Carol reciprocity ───────────────────────────────────
    if crossing_t:
        ax_bot.axvspan(0, crossing_t, alpha=0.06, color="red")
        ax_bot.axvspan(crossing_t, x[-1], alpha=0.06, color="green")

    ax_bot.plot(x, recip_mean, color=RECIP_COLOR, linewidth=2.2,
                label="Carol adapted reciprocity")
    ax_bot.fill_between(x, recip_mean - recip_std, recip_mean + recip_std,
                        color=RECIP_COLOR, alpha=0.15, linewidth=0)

    # Innate floor only
    ax_bot.axhline(0.10, color="#777777", linewidth=1.4, linestyle=":", zorder=1)
    ax_bot.text(x[-1] * 0.995, 0.10 + 0.025, "Innate floor  0.10",
                ha="right", va="bottom", fontsize=9.5, color="#555555",
                fontweight="bold")

    # Shared agreeableness crossing line in bottom panel too
    if crossing_t:
        ax_bot.axvline(crossing_t, color="black", linewidth=1.2,
                       linestyle="--", alpha=0.6)
        ax_bot.text(crossing_t + x[-1] * 0.008, 0.88,
                    "Agreeableness\ncrossing",
                    fontsize=9, color="black", va="top")

    # Final reciprocity value on the right
    final_recip = recip_mean[-1]
    ax_bot.text(x[-1] * 0.995, final_recip + 0.025,
                f"Final: {final_recip:.2f}",
                ha="right", va="bottom", fontsize=9.5, color=RECIP_COLOR,
                fontweight="bold")

    ax_bot.set_ylabel("Carol adapted reciprocity", fontsize=10)
    ax_bot.set_xlabel(r"CFR iteration  $t$", fontsize=10)
    ax_bot.set_ylim(0.0, 1.0)
    ax_bot.set_xlim(0, x[-1])
    ax_bot.set_title(
        "Carol adapted reciprocity — rises as Alice sets boundaries",
        fontsize=10
    )

    style_ax(ax_bot)

    # Caption-style legend below both panels
    from matplotlib.lines import Line2D
    leg_handles = [
        Line2D([0], [0], color=RECIP_COLOR, linewidth=2.2,
               label="Carol adapted reciprocity"),
        Line2D([0], [0], color="#777777", linewidth=1.4, linestyle=":",
               label="Innate floor (0.10)"),
        Line2D([0], [0], color="black", linewidth=1.2, linestyle="--",
               label="Agreeableness crossing"),
    ]
    fig.legend(handles=leg_handles,
               loc="lower center",
               ncol=3,
               fontsize=9.5,
               frameon=False,
               bbox_to_anchor=(0.5, -0.03),
               handlelength=2.0,
               columnspacing=2.5)

    plt.tight_layout(rect=(0, 0.05, 1, 1))
    out = OUT / "reciprocity_effect_on_agreeableness.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
