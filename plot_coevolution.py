#!/usr/bin/env python3
"""
Plot Alice & Carol Co-evolution: Personality Learning with CFR

Generates a 6-panel figure showing:
(a) Alice's personality (OCEAN)
(b) Carol's personality (OCEAN)
(c) Carol's reciprocity adaptation
(d) Alice's regrets (help_carol, decline_carol)
(e) Carol's CFR regrets (help, decline, reciprocate)
(f) Key trait comparison (Alice vs Carol Agreeableness)
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_csv(path):
    """Load a CSV, force numeric, deduplicate, sort."""
    df = pd.read_csv(path)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['episode'])
    df = df.drop_duplicates(subset=['episode'], keep='first')
    df = df.sort_values('episode')
    return df

def load_data():
    """Load all CSV files."""
    data = {}
    
    if Path("personality_evolution.csv").exists():
        data['alice_personality'] = load_csv("personality_evolution.csv")
        print(f"  Alice personality ({len(data['alice_personality'])} episodes)")
    
    if Path("carol_personality_evolution.csv").exists():
        data['carol_personality'] = load_csv("carol_personality_evolution.csv")
        print(f"  Carol personality ({len(data['carol_personality'])} episodes)")
    
    if Path("adapted_reciprocity.csv").exists():
        data['carol_reciprocity'] = load_csv("adapted_reciprocity.csv")
        print(f"  Carol reciprocity ({len(data['carol_reciprocity'])} episodes)")
    
    if Path("cfr_regrets.csv").exists():
        data['alice_regrets'] = load_csv("cfr_regrets.csv")
        print(f"  Alice regrets ({len(data['alice_regrets'])} episodes)")
    
    if Path("carol_cfr_regrets.csv").exists():
        data['carol_regrets'] = load_csv("carol_cfr_regrets.csv")
        print(f"  Carol CFR regrets ({len(data['carol_regrets'])} episodes)")
    
    return data

def plot_coevolution(data):
    """Create 6-panel coevolution plot."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle("Alice & Carol Co-evolution: Personality Learning with CFR\n(5000 episodes, both agents learning)", 
                 fontsize=14, fontweight='bold')
    
    # ===== PANEL A: Alice's Personality =====
    ax = axes[0, 0]
    if 'alice_personality' in data:
        df = data['alice_personality']
        episodes = df['episode']
        traits = ['carol_openness', 'carol_conscientiousness', 'carol_extraversion', 
                  'carol_agreeableness', 'carol_neuroticism']
        
        # Try alternate column names
        alt_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for trait, color in zip(alt_traits, colors):
            if trait in df.columns:
                ax.plot(episodes, df[trait], label=trait.capitalize(), color=color, linewidth=1.5, marker='o', markersize=2)
        
        ax.set_xlabel('Episode')
        ax.set_ylabel('Trait Value')
        ax.set_title('(a) Alice\'s Personality (OCEAN)', fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
    
    # ===== PANEL B: Carol's Personality =====
    ax = axes[0, 1]
    if 'carol_personality' in data:
        df = data['carol_personality']
        episodes = df['episode']
        traits = ['carol_openness', 'carol_conscientiousness', 'carol_extraversion', 
                  'carol_agreeableness', 'carol_neuroticism']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for trait, color in zip(traits, colors):
            if trait in df.columns:
                ax.plot(episodes, df[trait], label=trait.replace('carol_', '').capitalize(), 
                       color=color, linewidth=1.5, marker='o', markersize=2)
        
        ax.set_xlabel('Episode')
        ax.set_ylabel('Trait Value')
        ax.set_title('(b) Carol\'s Personality (OCEAN)\n[Learning from Exploiter (A=0.3) → Reformed]', fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
    
    # ===== PANEL C: Carol's Reciprocity Adaptation =====
    ax = axes[0, 2]
    if 'carol_reciprocity' in data:
        df = data['carol_reciprocity']
        episodes = df['episode']
        ax.plot(episodes, df['carol_adapted'], label='Carol adapted reciprocity', 
               color='red', linewidth=2, marker='o', markersize=2)
        ax.axhline(y=0.85, color='gray', linestyle='--', label='Cap (0.85)', alpha=0.7)
        ax.axhline(y=0.10, color='lightblue', linestyle='--', label='Innate (0.10)', alpha=0.7)
        
        ax.set_xlabel('Episode')
        ax.set_ylabel('Reciprocity Probability')
        ax.set_title('(c) Carol\'s Reciprocity Adaptation\n[Proportional Learning, base=0.012]', fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
    
    # ===== PANEL D: Alice's Regrets (Carol interaction) =====
    ax = axes[1, 0]
    if 'alice_regrets' in data:
        df = data['alice_regrets']
        episodes = df['episode']
        
        # Find help_carol and decline_carol columns
        help_col = [c for c in df.columns if 'help' in c and 'carol' in c]
        decline_col = [c for c in df.columns if 'decline' in c and 'carol' in c]
        
        if help_col:
            ax.plot(episodes, df[help_col[0]], label='help_carol', color='blue', linewidth=1.5, marker='o', markersize=2)
        if decline_col:
            ax.plot(episodes, df[decline_col[0]], label='decline_carol', color='red', linewidth=1.5, marker='o', markersize=2)
        
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
        ax.set_xlabel('Episode')
        ax.set_ylabel('Cumulative Regret')
        ax.set_title('(d) Alice\'s Regrets (Carol interaction)\n[Reversal when decline crosses above help]', fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # ===== PANEL E: Carol's CFR Regrets =====
    ax = axes[1, 1]
    if 'carol_regrets' in data:
        df = data['carol_regrets']
        episodes = df['episode']
        
        help_col = 'carol_help_regret' if 'carol_help_regret' in df.columns else None
        decline_col = 'carol_decline_regret' if 'carol_decline_regret' in df.columns else None
        reciprocate_col = 'carol_reciprocate_regret' if 'carol_reciprocate_regret' in df.columns else None
        
        if help_col and help_col in df.columns:
            ax.plot(episodes, df[help_col], label='help regret', color='green', linewidth=1.5, marker='o', markersize=2)
        if decline_col and decline_col in df.columns:
            ax.plot(episodes, df[decline_col], label='decline regret', color='orange', linewidth=1.5, marker='o', markersize=2)
        if reciprocate_col and reciprocate_col in df.columns:
            ax.plot(episodes, df[reciprocate_col], label='reciprocate regret', color='purple', linewidth=1.5, marker='o', markersize=2)
        
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
        ax.set_xlabel('Episode')
        ax.set_ylabel('Cumulative Regret')
        ax.set_title('(e) Carol\'s CFR Regrets\n[Drives personality evolution]', fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # ===== PANEL F: Key Trait Comparison (Agreeableness) =====
    ax = axes[1, 2]
    if 'alice_personality' in data and 'carol_personality' in data:
        alice_df = data['alice_personality']
        carol_df = data['carol_personality']
        
        alice_episodes = alice_df['episode']
        carol_episodes = carol_df['episode']
        
        # Find agreeableness columns
        alice_agree_col = 'agreeableness' if 'agreeableness' in alice_df.columns else None
        carol_agree_col = 'carol_agreeableness' if 'carol_agreeableness' in carol_df.columns else None
        
        if alice_agree_col and alice_agree_col in alice_df.columns:
            ax.plot(alice_episodes, alice_df[alice_agree_col], label='Alice Agreeableness', 
                   color='blue', linewidth=2, marker='o', markersize=2)
        
        if carol_agree_col and carol_agree_col in carol_df.columns:
            ax.plot(carol_episodes, carol_df[carol_agree_col], label='Carol Agreeableness', 
                   color='red', linewidth=2, marker='o', markersize=2)
        
        ax.axhline(y=0.3, color='red', linestyle=':', alpha=0.5, label='Carol initial (0.3 exploiter)')
        ax.set_xlabel('Episode')
        ax.set_ylabel('Agreeableness')
        ax.set_title('(f) Agreeableness Comparison\n[Carol reforms from exploiter (0.3) → cooperative]', fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
    
    plt.tight_layout()
    plt.savefig('results/coevolution_alice_carol.png', dpi=150, bbox_inches='tight')
    print("\n  Saved: results/coevolution_alice_carol.png")
    plt.close()

def main():
    print("=" * 60)
    print("Alice & Carol Co-evolution Plotter")
    print("=" * 60)
    
    # Load data
    data = load_data()
    
    if not data:
        print("❌ No CSV files found. Please run the simulation first.")
        return
    
    print("\nGenerating plots...")
    plot_coevolution(data)
    print("\n  Done! Open results/coevolution_alice_carol.png to view the results.")

if __name__ == '__main__':
    main()
