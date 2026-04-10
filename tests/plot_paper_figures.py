"""
Generate all paper figures from the 10-seed CFR and static baseline runs.

Outputs to results/:
  fig_personality_mood.png        — personality + mood evolution (2 rows)
  fig_regrets_per_person.png      — cumulative regrets per colleague
  fig_reward_comparison.png       — CFR vs Static baseline reward
  fig_convergence_zoom.png        — full + zoom personality view
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

OCEAN_COLORS = {
    "openness":          ("#4C78A8", "Openness"),
    "conscientiousness": ("#54A24B", "Conscientiousness"),
    "extraversion":      ("#F58518", "Extraversion"),
    "agreeableness":     ("#E45756", "Agreeableness"),
    "neuroticism":       ("#9467BD", "Neuroticism"),
}

MOOD_COLORS = {
    "stress":         ("#B07AA1", "Stress"),
    "satisfaction":   ("#59A14F", "Satisfaction"),
    "social_energy":  ("#EDC948", "Social Energy"),
}

BOB_COLORS = {
    "help_bob":    "#4C78A8",
    "decline_bob": "#E45756",
    "delay_bob":   "#54A24B",
}
CAROL_COLORS = {
    "help_carol":    "#4C78A8",
    "decline_carol": "#E45756",
    "teach_carol":   "#54A24B",
}
DAVE_COLORS = {
    "help_dave":    "#4C78A8",
    "decline_dave": "#E45756",
    "suggest_dave": "#54A24B",
}

N_SEEDS = 10
RESULTS_DIR = "results"
OUT_DIR = "results"


def load_seeds(base_dir):
    """Load personality and regret CSVs from seed_0..seed_(N-1)."""
    pers_list, reg_list = [], []
    for s in range(N_SEEDS):
        p = os.path.join(base_dir, f"seed_{s}", "personality_evolution.csv")
        r = os.path.join(base_dir, f"seed_{s}", "cfr_regrets.csv")
        if os.path.exists(p):
            pers_list.append(pd.read_csv(p))
        if os.path.exists(r):
            reg_list.append(pd.read_csv(r))
    return pers_list, reg_list


def style(ax, ylabel=None, ylim=None):
    ax.set_xlabel("Episode", fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)
    if ylim:
        ax.set_ylim(ylim)
    ax.grid(alpha=0.25, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)


# ============================================================
# FIGURE 1: Personality + Mood Evolution (2x2 grid)
# ============================================================
def fig_personality_mood(pers_list):
    fig, axes = plt.subplots(2, 2, figsize=(13, 7))
    fig.suptitle(
        f"Personality and Mood Evolution — mean ± std across {len(pers_list)} seeds",
        fontsize=12, fontweight="bold", y=1.00
    )

    ep = pers_list[0]["episode"].values

    # (a) Personality full range
    ax = axes[0, 0]
    ax.set_title("(a) OCEAN Personality", fontsize=11, fontweight="bold")
    for trait, (color, label) in OCEAN_COLORS.items():
        stacked = np.array([p[trait].values for p in pers_list])
        mean, std = stacked.mean(0), stacked.std(0)
        ax.plot(ep, mean, label=label, color=color, linewidth=2)
        ax.fill_between(ep, mean - std, mean + std, color=color, alpha=0.2)
    ax.legend(fontsize=8, loc="upper right", framealpha=0.85)
    style(ax, ylabel="Trait Value", ylim=(0.0, 1.0))

    # (b) Mood full range
    ax = axes[0, 1]
    ax.set_title("(b) Mood Evolution", fontsize=11, fontweight="bold")
    for mood, (color, label) in MOOD_COLORS.items():
        if mood not in pers_list[0].columns:
            continue
        stacked = np.array([p[mood].values for p in pers_list])
        mean, std = stacked.mean(0), stacked.std(0)
        ax.plot(ep, mean, label=label, color=color, linewidth=2)
        ax.fill_between(ep, mean - std, mean + std, color=color, alpha=0.2)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.legend(fontsize=8, loc="center right", framealpha=0.85)
    style(ax, ylabel="Mood Value", ylim=(-1.0, 1.1))

    # (c) Personality zoom
    ZOOM = 30
    ax = axes[1, 0]
    ax.set_title(f"(c) Personality Zoom (episodes 0-{ZOOM})", fontsize=11, fontweight="bold")
    for trait, (color, label) in OCEAN_COLORS.items():
        stacked = np.array([p[trait].values[:ZOOM + 1] for p in pers_list])
        mean, std = stacked.mean(0), stacked.std(0)
        ep_z = ep[:ZOOM + 1]
        ax.plot(ep_z, mean, label=label, color=color, linewidth=2, marker="o", markersize=3)
        ax.fill_between(ep_z, mean - std, mean + std, color=color, alpha=0.2)
    style(ax, ylabel="Trait Value", ylim=(0.0, 1.0))

    # (d) Mood zoom
    ax = axes[1, 1]
    ax.set_title(f"(d) Mood Zoom (episodes 0-{ZOOM})", fontsize=11, fontweight="bold")
    for mood, (color, label) in MOOD_COLORS.items():
        if mood not in pers_list[0].columns:
            continue
        stacked = np.array([p[mood].values[:ZOOM + 1] for p in pers_list])
        mean, std = stacked.mean(0), stacked.std(0)
        ep_z = ep[:ZOOM + 1]
        ax.plot(ep_z, mean, label=label, color=color, linewidth=2, marker="o", markersize=3)
        ax.fill_between(ep_z, mean - std, mean + std, color=color, alpha=0.2)
    ax.axhline(0, color="black", linewidth=0.6)
    style(ax, ylabel="Mood Value", ylim=(-1.0, 1.1))

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "fig_personality_mood.png")
    plt.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close()


# ============================================================
# FIGURE 2: Regrets per Colleague
# ============================================================
def fig_regrets(reg_list):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle(
        f"Cumulative Regrets per Information Set — mean ± std across {len(reg_list)} seeds",
        fontsize=12, fontweight="bold", y=1.03
    )

    ep = reg_list[0]["episode"].values

    for idx, (person, colors, title) in enumerate([
        ("bob",   BOB_COLORS,   "(a) Bob (Moderate Reciprocity)"),
        ("carol", CAROL_COLORS, "(b) Carol (Exploitative)"),
        ("dave",  DAVE_COLORS,  "(c) Dave (Highly Reciprocal)"),
    ]):
        ax = axes[idx]
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.axhline(0, color="black", linewidth=0.6)
        for action, color in colors.items():
            if action not in reg_list[0].columns:
                continue
            stacked = np.array([r[action].values for r in reg_list])
            mean, std = stacked.mean(0), stacked.std(0)
            label = action.replace(f"_{person}", "").capitalize()
            ax.plot(ep, mean, label=label, color=color, linewidth=2)
            ax.fill_between(ep, mean - std, mean + std, color=color, alpha=0.2)
        ax.legend(fontsize=9, loc="upper left", framealpha=0.85)
        style(ax, ylabel="Cumulative Regret")

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "fig_regrets_per_person.png")
    plt.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close()


# ============================================================
# FIGURE 3: Reward Comparison CFR vs Static
# ============================================================
def fig_reward_comparison(cfr_list, static_list):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.suptitle(
        f"Reward Comparison: CFR Learning vs Static Baseline (n={len(cfr_list)} seeds each)",
        fontsize=12, fontweight="bold", y=1.02
    )

    ep = cfr_list[0]["episode"].values

    # (a) Per-episode reward with bands
    ax = axes[0]
    ax.set_title("(a) Per-Episode Reward", fontsize=11, fontweight="bold")
    cfr_stack = np.array([c["total_reward"].values for c in cfr_list])
    stat_stack = np.array([s["total_reward"].values for s in static_list])
    cfr_mean, cfr_std = cfr_stack.mean(0), cfr_stack.std(0)
    stat_mean, stat_std = stat_stack.mean(0), stat_stack.std(0)

    ax.plot(ep, cfr_mean, label="CFR Learning (ours)", color="#4C78A8", linewidth=2)
    ax.fill_between(ep, cfr_mean - cfr_std, cfr_mean + cfr_std, color="#4C78A8", alpha=0.2)
    ax.plot(ep, stat_mean, label="Static Baseline", color="#E45756",
            linewidth=2, linestyle="--")
    ax.fill_between(ep, stat_mean - stat_std, stat_mean + stat_std, color="#E45756", alpha=0.2)
    ax.legend(fontsize=10, loc="lower right", framealpha=0.85)
    style(ax, ylabel="Episode Reward")

    # (b) Cumulative average reward
    ax = axes[1]
    ax.set_title("(b) Cumulative Average Reward", fontsize=11, fontweight="bold")
    cfr_cum = np.cumsum(cfr_stack, axis=1) / (np.arange(cfr_stack.shape[1]) + 1)
    stat_cum = np.cumsum(stat_stack, axis=1) / (np.arange(stat_stack.shape[1]) + 1)
    cfr_cm, cfr_cs = cfr_cum.mean(0), cfr_cum.std(0)
    stat_cm, stat_cs = stat_cum.mean(0), stat_cum.std(0)

    ax.plot(ep, cfr_cm, label="CFR Learning (ours)", color="#4C78A8", linewidth=2)
    ax.fill_between(ep, cfr_cm - cfr_cs, cfr_cm + cfr_cs, color="#4C78A8", alpha=0.2)
    ax.plot(ep, stat_cm, label="Static Baseline", color="#E45756",
            linewidth=2, linestyle="--")
    ax.fill_between(ep, stat_cm - stat_cs, stat_cm + stat_cs, color="#E45756", alpha=0.2)
    ax.legend(fontsize=10, loc="lower right", framealpha=0.85)
    style(ax, ylabel="Cumulative Avg Reward")

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "fig_reward_comparison.png")
    plt.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close()

    # Print summary stats
    last_50_cfr = cfr_stack[:, -50:].mean(axis=1)
    last_50_stat = stat_stack[:, -50:].mean(axis=1)
    print(f"\n=== Reward Comparison (last 50 episodes) ===")
    print(f"  CFR:    {last_50_cfr.mean():.3f} ± {last_50_cfr.std():.3f}")
    print(f"  Static: {last_50_stat.mean():.3f} ± {last_50_stat.std():.3f}")
    improvement = (last_50_cfr.mean() - last_50_stat.mean()) / last_50_stat.mean() * 100
    print(f"  Improvement: {improvement:+.1f}%")


# ============================================================
# MAIN
# ============================================================
def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("Loading CFR runs...")
    cfr_pers, cfr_reg = load_seeds(RESULTS_DIR)
    print(f"  Loaded {len(cfr_pers)} CFR seeds")

    print("Loading static baseline runs...")
    static_pers, _ = load_seeds(os.path.join(RESULTS_DIR, "static"))
    print(f"  Loaded {len(static_pers)} static seeds")

    if not cfr_pers:
        print("ERROR: No CFR data found")
        return

    print("\nGenerating figures...")
    fig_personality_mood(cfr_pers)
    fig_regrets(cfr_reg)

    if static_pers:
        fig_reward_comparison(cfr_pers, static_pers)
    else:
        print("  Skipping reward comparison (no static baseline data)")

    # Print final personality summary
    print("\n=== Final CFR Personality (10 seeds, episode 300) ===")
    arr = np.array([[p.iloc[-1][t] for t in ["openness","conscientiousness",
                    "extraversion","agreeableness","neuroticism"]] for p in cfr_pers])
    for i, n in enumerate(["O","C","E","A","N"]):
        print(f"  {n}: {arr[:,i].mean():.4f} ± {arr[:,i].std():.4f}")


if __name__ == "__main__":
    main()
