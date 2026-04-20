"""
Log mean (across 10 seeds) to TensorBoard — one clean run.

Groups logged:
  Personality/   — O, C, E, A, N
  Regrets/Bob/   — help, decline, delay
  Regrets/Carol/ — help, decline, teach
  Regrets/Dave/  — help, decline, suggest
  Adaptation/    — carol_reciprocity, carol_regret_growth_rate, bob_reciprocity, dave_reciprocity
  Reward/        — episode reward

Usage (from project root):
    python tests/log_tensorboard_mean.py
Then open: tensorboard --logdir tests/runs/mean_run
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path

try:
    from torch.utils.tensorboard import SummaryWriter
except ImportError:
    from tensorboardX import SummaryWriter

RESULTS_DIR = "results"
LOG_DIR     = "tests/runs/mean_run"
N_SEEDS     = 10

OCEAN  = ["openness","conscientiousness","extraversion","agreeableness","neuroticism"]
REGRETS = {
    "Bob":   ["help_bob",   "decline_bob",   "delay_bob"],
    "Carol": ["help_carol", "decline_carol", "teach_carol"],
    "Dave":  ["help_dave",  "decline_dave",  "suggest_dave"],
}
ADAPT_COLS = ["carol_adapted","bob_adapted","dave_adapted"]


def load_seeds():
    pers, regs, adapts = [], [], []
    for s in range(N_SEEDS):
        base = os.path.join(RESULTS_DIR, f"seed_{s}")
        p = os.path.join(base, "personality_evolution.csv")
        r = os.path.join(base, "cfr_regrets.csv")
        a = os.path.join(base, "adapted_reciprocity.csv")
        if os.path.exists(p):
            pers.append(pd.read_csv(p))
            regs.append(pd.read_csv(r))
            if os.path.exists(a):
                adapts.append(pd.read_csv(a))
    print(f"Loaded {len(pers)} seeds  (adapt: {len(adapts)})")
    return pers, regs, adapts


def mean_std(dfs, col):
    arr = np.array([df[col].values for df in dfs])
    return arr.mean(0), arr.std(0)


def main():
    pers, regs, adapts = load_seeds()

    ep_p = pers[0]["episode"].values   # 0..300
    ep_r = regs[0]["episode"].values   # 1..300

    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    writer = SummaryWriter(LOG_DIR)
    print(f"Writing to {LOG_DIR} ...")

    # ── Personality ───────────────────────────────────────────────────────
    for trait in OCEAN:
        mean, std = mean_std(pers, trait)
        for i, ep in enumerate(ep_p):
            writer.add_scalar(f"Personality/{trait}", float(mean[i]), int(ep))
            writer.add_scalar(f"Personality/{trait}_std", float(std[i]),  int(ep))

    # ── Reward ───────────────────────────────────────────────────────────
    mean_r, std_r = mean_std(pers, "total_reward")
    for i, ep in enumerate(ep_p):
        writer.add_scalar("Reward/episode_reward",     float(mean_r[i]), int(ep))
        writer.add_scalar("Reward/episode_reward_std", float(std_r[i]),  int(ep))

    # ── Regrets per colleague ─────────────────────────────────────────────
    for person, actions in REGRETS.items():
        for action in actions:
            if action not in regs[0].columns:
                continue
            short = action.split("_")[0].capitalize()   # Help / Decline / Delay
            mean, std = mean_std(regs, action)
            for i, ep in enumerate(ep_r):
                writer.add_scalar(f"Regrets/{person}/{short}",
                                  float(mean[i]), int(ep))
                writer.add_scalar(f"Regrets/{person}/{short}_std",
                                  float(std[i]),  int(ep))

    # ── Carol adaptation ──────────────────────────────────────────────────
    if adapts:
        ep_a = adapts[0]["episode"].values    # 1..300

        for col in ADAPT_COLS:
            person = col.split("_")[0].capitalize()
            mean, std = mean_std(adapts, col)
            for i, ep in enumerate(ep_a):
                writer.add_scalar(f"Adaptation/{person}_reciprocity",
                                  float(mean[i]), int(ep))
                writer.add_scalar(f"Adaptation/{person}_reciprocity_std",
                                  float(std[i]),  int(ep))

        # Carol regret gap growth rate (smoothed)
        window = 20
        gap_stack = np.array([
            r["decline_carol"].values - r["help_carol"].values
            for r in regs
        ])
        rate_stack = np.diff(gap_stack, axis=1)   # (n_seeds, 299)
        rate_mean  = rate_stack.mean(0)
        # smooth
        kernel     = np.ones(window) / window
        smoothed   = np.convolve(rate_mean, kernel, mode="valid")
        ep_rate    = ep_r[window:]
        for i, ep in enumerate(ep_rate):
            writer.add_scalar("Adaptation/Carol_regret_gap_growth_rate",
                              float(smoothed[i]), int(ep))

    # ── Custom layout so TensorBoard shows nice grouped charts ───────────
    layout = {
        "Alice Personality": {
            "All OCEAN Traits": ["Multiline", [f"Personality/{t}" for t in OCEAN]],
        },
        "Bob Regrets": {
            "All Actions": ["Multiline",
                ["Regrets/Bob/Help","Regrets/Bob/Decline","Regrets/Bob/Delay"]],
        },
        "Carol Regrets": {
            "All Actions": ["Multiline",
                ["Regrets/Carol/Help","Regrets/Carol/Decline","Regrets/Carol/Teach"]],
        },
        "Dave Regrets": {
            "All Actions": ["Multiline",
                ["Regrets/Dave/Help","Regrets/Dave/Decline","Regrets/Dave/Suggest"]],
        },
        "Carol Adaptation": {
            "Reciprocity vs Baseline": ["Multiline",
                ["Adaptation/Carol_reciprocity"]],
            "Regret Gap Growth Rate": ["Multiline",
                ["Adaptation/Carol_regret_gap_growth_rate"]],
        },
        "All Colleague Reciprocity": {
            "Bob / Carol / Dave": ["Multiline",
                ["Adaptation/Carol_reciprocity",
                 "Adaptation/Bob_reciprocity",
                 "Adaptation/Dave_reciprocity"]],
        },
    }
    writer.add_custom_scalars(layout)
    writer.close()
    print("Done. Run:")
    print(f"  tensorboard --logdir {LOG_DIR} --port 6008")


if __name__ == "__main__":
    main()
