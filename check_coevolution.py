#!/usr/bin/env python3
"""
Quick check of coevolution experiment results.
Verifies that Carol's personality is actually evolving through CFR.
"""
import csv
import os
from pathlib import Path

def check_personality_evolution():
    """Check if personality_evolution.csv shows Carol's personality changing."""
    csv_path = Path("personality_evolution.csv")

    if not csv_path.exists():
        print("❌ personality_evolution.csv not found")
        return False

    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("❌ No data in personality_evolution.csv")
        return False

    print(f"✓ Found {len(rows)} rows in personality_evolution.csv")

    # Check if we have data beyond episode 0
    episodes = set(row['episode'] for row in rows)
    print(f"✓ Episodes: {sorted(set(int(e) for e in episodes if e.isdigit()), key=int)}")

    # Check first and last rows
    first = rows[0]
    last = rows[-1]

    print(f"\nFirst episode {first['episode']} traits:")
    for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
        if trait in first:
            print(f"  {trait}: {first[trait]}")

    print(f"\nLast episode {last['episode']} traits:")
    for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
        if trait in last:
            print(f"  {trait}: {last[trait]}")

    # Check if traits changed
    if first['agreeableness'] != last['agreeableness']:
        change = float(last['agreeableness']) - float(first['agreeableness'])
        print(f"\n✓ Agreeableness changed by {change:+.4f} (CFR learning detected)")
        return True
    else:
        print(f"\n❌ No change in agreeableness (possible issue with CFR)")
        return False

def check_cfr_regrets():
    """Check if cfr_regrets.csv shows regret accumulation."""
    csv_path = Path("cfr_regrets.csv")

    if not csv_path.exists():
        print("\n❌ cfr_regrets.csv not found")
        return False

    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("\n❌ No data in cfr_regrets.csv")
        return False

    print(f"\n✓ Found {len(rows)} rows in cfr_regrets.csv")

    # Show first row
    first = rows[0]
    print(f"\nFirst row (episode {first.get('episode', '?')}):")
    for key in sorted(first.keys())[:5]:  # Show first 5 columns
        print(f"  {key}: {first[key]}")

    return True

if __name__ == "__main__":
    print("Checking coevolution experiment...")
    print("=" * 50)

    personality_ok = check_personality_evolution()
    regrets_ok = check_cfr_regrets()

    print("\n" + "=" * 50)
    if personality_ok and regrets_ok:
        print("✓ Coevolution experiment appears to be working!")
    else:
        print("⚠ Some issues detected - check logs")
