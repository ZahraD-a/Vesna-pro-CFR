"""
CFR Regret Visualization - Simple Matplotlib Version
Run this directly: python analyze_cfr_simple.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def load_data():
    """Load CFR regret and personality evolution data."""
    # Check parent directory
    parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    regrets_path = os.path.join(parent_path, "cfr_regrets.csv")
    personality_path = os.path.join(parent_path, "personality_evolution.csv")

    if not os.path.exists(regrets_path):
        print(f"ERROR: {regrets_path} not found!")
        print("Run the CFR simulation first to generate data files.")
        return None, None

    if not os.path.exists(personality_path):
        print(f"ERROR: {personality_path} not found!")
        print("Run the CFR simulation first to generate data files.")
        return None, None

    regrets_df = pd.read_csv(regrets_path)

    # Handle both old and new CSV formats
    personality_df = pd.read_csv(personality_path)

    # If 'curious' column is missing, add it with default value 0.5
    if 'curious' not in personality_df.columns:
        personality_df['curious'] = 0.5

    return regrets_df, personality_df

def compute_implied_strategy(row):
    """Compute implied strategy probabilities from regrets using regret matching."""
    regrets = [
        max(0, row["try_new_shop"]),
        max(0, row["go_regular_shop"]),
        max(0, row["make_at_home"])
    ]
    total = sum(regrets)

    if total < 0.001:
        return [1.0/3, 1.0/3, 1.0/3]

    return [regrets[0]/total, regrets[1]/total, regrets[2]/total]

def main():
    regrets_df, personality_df = load_data()

    if regrets_df is None or personality_df is None:
        return

    print(f"Loaded {len(regrets_df)} episodes of regret data")
    print(f"Loaded {len(personality_df)} episodes of personality data")

    # Strategy info
    strategies = ["Try New Shop", "Regular Shop", "Make at Home"]
    colors = ["#EF553B", "#00CC96", "#636EFA"]
    regret_keys = ["try_new_shop", "go_regular_shop", "make_at_home"]

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("CFR Counterfactual Regret Minimization Analysis", fontsize=16, fontweight='bold')

    # Plot 1: Cumulative Regrets
    ax1 = axes[0, 0]
    for i, (key, label, color) in enumerate(zip(regret_keys, strategies, colors)):
        ax1.plot(regrets_df["episode"], regrets_df[key], label=label, color=color, linewidth=2)
    ax1.set_xlabel("Episode")
    ax1.set_ylabel("Cumulative Regret")
    ax1.set_title("Cumulative Regrets Over Time")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Implied Strategy Probabilities
    ax2 = axes[0, 1]
    implied_probs = [compute_implied_strategy(row) for _, row in regrets_df.iterrows()]
    implied_probs = np.array(implied_probs) * 100  # Convert to percentage

    # Final implied strategy for bar chart
    final_implied = compute_implied_strategy(regrets_df.iloc[-1])

    for i, (label, color) in enumerate(zip(strategies, colors)):
        ax2.plot(regrets_df["episode"], implied_probs[:, i], label=label, color=color, linewidth=2)
    ax2.axhline(y=95, color='gray', linestyle='--', alpha=0.5, label='Expected Optimal')
    ax2.set_xlabel("Episode")
    ax2.set_ylabel("Probability (%)")
    ax2.set_title("Implied Strategy (Regret Matching)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Personality Evolution
    ax3 = axes[1, 0]
    # Check which traits are available
    traits = ["cautious", "bold"]
    trait_colors = ["#636EFA", "#EF553B"]
    trait_labels = ["Cautious", "Bold"]

    # Add curious if it varies (not constant 0.5)
    if 'curious' in personality_df.columns and personality_df['curious'].std() > 0.001:
        traits.append("curious")
        trait_colors.append("#00CC96")
        trait_labels.append("Curious")

    for trait, label, color in zip(traits, trait_labels, trait_colors):
        ax3.plot(personality_df["episode"], personality_df[trait], label=label, color=color, linewidth=2)

    ax3.set_xlabel("Episode")
    ax3.set_ylabel("Trait Value")
    ax3.set_title("Personality Evolution")
    ax3.set_ylim(0, 1)
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Final Strategy Distribution (Bar Chart)
    ax4 = axes[1, 1]
    final_probs = np.array(final_implied) * 100

    bars = ax4.bar(strategies, final_probs, color=colors, alpha=0.8, edgecolor='black')
    ax4.set_ylabel("Probability (%)")
    ax4.set_title("Final Implied Strategy")
    ax4.set_ylim(0, 100)

    # Add value labels on bars
    for bar, val in zip(bars, final_probs):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')

    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    # Save and show
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cfr_analysis.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nChart saved to: {output_path}")

    # Print summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)

    final_regrets = regrets_df.iloc[-1]
    print("\nFinal Cumulative Regrets:")
    for key, label in zip(regret_keys, strategies):
        print(f"  {label:20s}: {final_regrets[key]:.2f}")

    final_personality = personality_df.iloc[-1]
    print("\nFinal Personality:")
    print(f"  Cautious:  {final_personality['cautious']:.4f}")
    print(f"  Bold:      {final_personality['bold']:.4f}")
    if 'curious' in final_personality:
        print(f"  Curious:   {final_personality['curious']:.4f}")

    # Personality change
    first_personality = personality_df.iloc[0]
    print("\nPersonality Change:")
    print(f"  Cautious Δ: {final_personality['cautious'] - first_personality['cautious']:+.4f}")
    print(f"  Bold Δ:     {final_personality['bold'] - first_personality['bold']:+.4f}")
    if 'curious' in final_personality and 'curious' in first_personality:
        print(f"  Curious Δ:  {final_personality['curious'] - first_personality['curious']:+.4f}")

    print("\nImplied Strategy (Final):")
    for label, prob in zip(strategies, np.array(final_implied) * 100):
        print(f"  {label:20s}: {prob:.1f}%")

    print("="*60)

    plt.show()

if __name__ == "__main__":
    main()
