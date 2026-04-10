"""
VesnaPro CFR Personality Learning — Results Visualization
Generates the paper figures from personality_evolution.csv and cfr_regrets.csv

Usage:
    python tests/analyze_results.py
    python tests/analyze_results.py --base . --static-base ./static_run
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse

OCEAN_COLORS = {
    "openness":          ("#4C78A8", "Openness (O)"),
    "conscientiousness": ("#54A24B", "Conscientiousness (C)"),
    "extraversion":      ("#F58518", "Extraversion (E)"),
    "agreeableness":     ("#E45756", "Agreeableness (A)"),
    "neuroticism":       ("#9467BD", "Neuroticism (N)"),
}

BOB_COLORS   = {
    "help_bob":    "#4C78A8",
    "decline_bob": "#E45756",
    "delay_bob":   "#54A24B"
}
CAROL_COLORS = {
    "help_carol":    "#4C78A8",
    "decline_carol": "#E45756",
    "teach_carol":   "#54A24B"
}
DAVE_COLORS  = {
    "help_dave":     "#4C78A8",
    "decline_dave":  "#E45756",
    "suggest_dave":  "#54A24B"
}

def load_data(base_dir):
    p = os.path.join(base_dir, "personality_evolution.csv")
    r = os.path.join(base_dir, "cfr_regrets.csv")
    if not os.path.exists(p) or not os.path.exists(r):
        raise FileNotFoundError(
            f"CSV files not found in {base_dir}. "
            "Run 'gradle run' first."
        )
    return pd.read_csv(p), pd.read_csv(r)

def apply_style(ax, ylabel=None, ylim=None):
    ax.set_xlabel("Episodes", fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)
    if ylim:
        ax.set_ylim(ylim)
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)

def plot_main(pers_df, reg_df, out_path):
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.suptitle(
        "Personality Evolution and Cumulative Regrets — VesnaPro CFR",
        fontsize=11, fontweight="bold", y=1.02
    )

    ep_pers = pers_df["episode"].values
    ep_reg = reg_df["episode"].values

    # (a) OCEAN personality
    ax = axes[0]
    ax.set_title("(a) Alice's Personality", fontsize=10, fontweight="bold")
    for trait, (color, label) in OCEAN_COLORS.items():
        ax.plot(ep_pers, pers_df[trait].values, label=label,
                color=color, linewidth=2,
                marker="s", markevery=30, markersize=4)
    ax.legend(fontsize=7.5, loc="upper right", framealpha=0.7)
    apply_style(ax, ylabel="Trait Value", ylim=(0.0, 1.0))

    # (b)(c)(d) regrets per information set
    for idx, (person, colors, title) in enumerate([
        ("bob",   BOB_COLORS,   "(b) Bob (Senior)"),
        ("carol", CAROL_COLORS, "(c) Carol (Exploitative)"),
        ("dave",  DAVE_COLORS,  "(d) Dave (Reciprocal)"),
    ]):
        ax = axes[idx + 1]
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.axhline(0, color="black", linewidth=0.6)
        for action, color in colors.items():
            if action not in reg_df.columns:
                continue
            label = action.replace(f"_{person}", "").capitalize()
            ax.plot(ep_reg, reg_df[action].values, label=label,
                    color=color, linewidth=2,
                    marker="s", markevery=30, markersize=4)
        ax.legend(fontsize=8, loc="upper left", framealpha=0.7)
        apply_style(ax, ylabel="Cumulative Regret")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close()

def plot_reward_comparison(cfr_df, static_df, out_path):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.set_title("Reward Comparison: CFR-RM vs Static Personality",
                 fontsize=11, fontweight="bold")

    ep = cfr_df["episode"].values
    cfr_avg  = np.cumsum(cfr_df["total_reward"].values) / (np.arange(len(cfr_df)) + 1)
    stat_avg = np.cumsum(static_df["total_reward"].values) / (np.arange(len(static_df)) + 1)

    ax.plot(ep, cfr_avg,  label="CFR-RM (ours)",
            color="#4C78A8", linewidth=2,
            marker="s", markevery=30, markersize=4)
    ax.plot(ep, stat_avg, label="Static baseline",
            color="#888888", linewidth=2, linestyle="--",
            marker="^", markevery=30, markersize=4)

    ax.legend(fontsize=9, loc="lower right", framealpha=0.8)
    apply_style(ax, ylabel="Cumulative Average Reward")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close()

def print_summary(pers_df, reg_df):
    final_p = pers_df.iloc[-1]
    final_r = reg_df.iloc[-1]
    print("\n" + "="*60)
    print(f"FINAL PERSONALITY (episode {int(final_p['episode'])}):")
    for t in ["openness","conscientiousness","extraversion",
               "agreeableness","neuroticism"]:
        print(f"  {t:22s}: {final_p[t]:.4f}")
    print("\nFINAL CUMULATIVE REGRETS:")
    for a in ["help_bob","decline_bob","delay_bob",
              "help_carol","decline_carol","teach_carol",
              "help_dave","decline_dave","suggest_dave"]:
        if a in final_r:
            print(f"  {a:22s}: {final_r[a]:+.3f}")
    print("="*60)

def load_multi_seed(results_dir, n_seeds=10):
    """Load CSVs from results/seed_0 .. seed_(n-1) and return aligned arrays."""
    pers_list, reg_list = [], []
    for s in range(n_seeds):
        seed_dir = os.path.join(results_dir, f"seed_{s}")
        try:
            p, r = load_data(seed_dir)
            pers_list.append(p)
            reg_list.append(r)
        except FileNotFoundError:
            print(f"  Skipping seed_{s} (not found)")
    return pers_list, reg_list

def plot_multi_seed(pers_list, reg_list, out_path):
    """Plot mean±std across seeds."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.suptitle(
        f"VesnaPro CFR — Mean ± Std across {len(pers_list)} seeds",
        fontsize=11, fontweight="bold", y=1.02
    )

    # (a) OCEAN with bands
    ax = axes[0]
    ax.set_title(f"(a) Alice's Personality (n={len(pers_list)})",
                 fontsize=10, fontweight="bold")
    ep = pers_list[0]["episode"].values
    for trait, (color, label) in OCEAN_COLORS.items():
        stacked = np.array([p[trait].values for p in pers_list])
        mean, std = stacked.mean(0), stacked.std(0)
        ax.plot(ep, mean, label=label, color=color, linewidth=2)
        ax.fill_between(ep, mean - std, mean + std, color=color, alpha=0.2)
    ax.legend(fontsize=7.5, loc="upper right", framealpha=0.7)
    apply_style(ax, ylabel="Trait Value", ylim=(0.0, 1.0))

    # (b)(c)(d) regrets with bands
    for idx, (person, colors, title) in enumerate([
        ("bob",   BOB_COLORS,   "(b) Bob (Senior)"),
        ("carol", CAROL_COLORS, "(c) Carol (Exploitative)"),
        ("dave",  DAVE_COLORS,  "(d) Dave (Reciprocal)"),
    ]):
        ax = axes[idx + 1]
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.axhline(0, color="black", linewidth=0.6)
        ep_r = reg_list[0]["episode"].values
        for action, color in colors.items():
            if action not in reg_list[0].columns:
                continue
            stacked = np.array([r[action].values for r in reg_list])
            mean, std = stacked.mean(0), stacked.std(0)
            label = action.replace(f"_{person}", "").capitalize()
            ax.plot(ep_r, mean, label=label, color=color, linewidth=2)
            ax.fill_between(ep_r, mean - std, mean + std, color=color, alpha=0.2)
        ax.legend(fontsize=8, loc="upper left", framealpha=0.7)
        apply_style(ax, ylabel="Cumulative Regret")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=".",
                        help="Directory containing CSV files from CFR run")
    parser.add_argument("--static-base", default=None,
                        help="Directory containing CSV files from static run")
    parser.add_argument("--out-dir", default="tests",
                        help="Output directory for figures")
    parser.add_argument("--multi-seed", default=None,
                        help="Directory with per-seed subdirs (e.g. 'results') to plot mean±std")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    if args.multi_seed:
        pers_list, reg_list = load_multi_seed(args.multi_seed)
        if not pers_list:
            print(f"ERROR: No seed directories found in {args.multi_seed}")
            return
        out_multi = os.path.join(args.out_dir, "fig_personality_regrets_bands.png")
        plot_multi_seed(pers_list, reg_list, out_multi)
        print_summary(pers_list[0], reg_list[0])
        return

    try:
        pers_df, reg_df = load_data(args.base)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return

    # Align episodes
    ep_max = min(pers_df["episode"].max(), reg_df["episode"].max())
    pers_df = pers_df[pers_df["episode"] <= ep_max].reset_index(drop=True)
    reg_df  = reg_df[reg_df["episode"]  <= ep_max].reset_index(drop=True)

    out1 = os.path.join(args.out_dir, "fig_personality_regrets.png")
    plot_main(pers_df, reg_df, out1)

    if args.static_base:
        try:
            static_pers, _ = load_data(args.static_base)
            out2 = os.path.join(args.out_dir, "fig_reward_comparison.png")
            plot_reward_comparison(pers_df, static_pers, out2)
        except FileNotFoundError as e:
            print(f"WARNING: {e}")

    print_summary(pers_df, reg_df)

if __name__ == "__main__":
    main()
