"""
Plot detailed convergence view (first 20 episodes) for all 10 seeds.
Shows how fast the personality converges before stabilising.
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

RESULTS_DIR = "results"
OUT_FILE = "results/fig_convergence_zoom.png"
N_SEEDS = 10
ZOOM_EPISODES = 30  # first N episodes

# Load all seeds
all_data = []
for s in range(N_SEEDS):
    path = os.path.join(RESULTS_DIR, f"seed_{s}", "personality_evolution.csv")
    if not os.path.exists(path):
        continue
    all_data.append(pd.read_csv(path))

if not all_data:
    print("No data found")
    exit(1)

fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
fig.suptitle(
    f"Personality Convergence — {len(all_data)} seeds "
    f"(10 interactions per colleague per episode)",
    fontsize=12, fontweight="bold", y=1.02
)

# LEFT: Full 0-300 episode range
ax = axes[0]
ax.set_title("(a) Full Training (Episodes 0-300)", fontsize=11, fontweight="bold")
for trait, (color, label) in OCEAN_COLORS.items():
    stacked = np.array([df[trait].values for df in all_data])
    mean = stacked.mean(axis=0)
    std = stacked.std(axis=0)
    ep = all_data[0]["episode"].values
    ax.plot(ep, mean, label=label, color=color, linewidth=2)
    ax.fill_between(ep, mean - std, mean + std, color=color, alpha=0.2)
ax.axvline(ZOOM_EPISODES, color="red", linestyle=":", linewidth=1.5,
           label=f"Zoom region (<= {ZOOM_EPISODES})")
ax.set_xlabel("Episode", fontsize=11)
ax.set_ylabel("Trait Value", fontsize=11)
ax.set_ylim(0, 1)
ax.legend(fontsize=8, loc="center right", framealpha=0.85)
ax.grid(alpha=0.3, linestyle="--")

# RIGHT: Zoomed into first 30 episodes
ax = axes[1]
ax.set_title(f"(b) Zoom: Episodes 0-{ZOOM_EPISODES} (convergence region)",
             fontsize=11, fontweight="bold")
for trait, (color, label) in OCEAN_COLORS.items():
    stacked = np.array([df[trait].values[:ZOOM_EPISODES + 1] for df in all_data])
    mean = stacked.mean(axis=0)
    std = stacked.std(axis=0)
    ep = all_data[0]["episode"].values[:ZOOM_EPISODES + 1]
    ax.plot(ep, mean, label=label, color=color, linewidth=2,
            marker="o", markersize=4)
    ax.fill_between(ep, mean - std, mean + std, color=color, alpha=0.2)
ax.set_xlabel("Episode", fontsize=11)
ax.set_ylabel("Trait Value", fontsize=11)
ax.set_ylim(0, 1)
ax.legend(fontsize=8, loc="center right", framealpha=0.85)
ax.grid(alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig(OUT_FILE, dpi=200, bbox_inches="tight")
print(f"Saved: {OUT_FILE}")
plt.close()

# Also print how fast convergence happens
print("\n=== Convergence Speed Analysis ===")
final = all_data[0].iloc[-1]
for trait in OCEAN_COLORS:
    final_val = final[trait]
    for ep_idx in range(len(all_data[0])):
        val = all_data[0].iloc[ep_idx][trait]
        if abs(val - final_val) < 0.01:
            print(f"  {trait:22s}: within 0.01 of final by episode {ep_idx}")
            break
