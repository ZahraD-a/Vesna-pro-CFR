#!/bin/bash
# Run the CFR personality learning experiment with 10 different seeds (0-9)
# Saves per-seed CSV outputs under results/seed_N/
#
# Usage (from project root):
#   bash tests/run_10_seeds.sh
#
# Requirements:
#   - vesna.jcm must have a "seed: <N>" line (any non-negative integer)
#   - gradle-8.5 installed at ./gradle-8.5/bin/gradle

set -e

GRADLE=./gradle-8.5/bin/gradle
JCM_FILE=vesna.jcm
RESULTS_DIR=results

# Verify gradle
if [ ! -x "$GRADLE" ]; then
    echo "ERROR: Gradle not found at $GRADLE"
    exit 1
fi

# Verify JCM has a seed line
if ! grep -q "seed:" "$JCM_FILE"; then
    echo "ERROR: $JCM_FILE has no 'seed:' line to replace."
    echo "Add 'seed: 0' to the agent block before running this script."
    exit 1
fi

mkdir -p "$RESULTS_DIR"

echo "=========================================="
echo "Running 10-seed CFR experiment"
echo "=========================================="

for SEED in 0 1 2 3 4 5 6 7 8 9; do
    echo ""
    echo "--- Seed $SEED ---"

    # Update JCM with this seed (portable sed)
    sed -i.bak "s/seed: *[0-9]\+/seed:       $SEED/" "$JCM_FILE"
    rm -f "$JCM_FILE.bak"

    # Clean previous single-run artifacts so we start fresh
    rm -f personality_evolution.csv cfr_regrets.csv personality.json

    # Run gradle (quiet mode, errors still shown)
    "$GRADLE" run --quiet 2>&1 | tail -5

    # Save outputs to per-seed directory
    SEED_DIR="$RESULTS_DIR/seed_$SEED"
    mkdir -p "$SEED_DIR"

    if [ -f personality_evolution.csv ]; then
        cp personality_evolution.csv "$SEED_DIR/"
        cp cfr_regrets.csv "$SEED_DIR/"
        if [ -f personality.json ]; then
            cp personality.json "$SEED_DIR/"
        fi
        echo "  Saved to $SEED_DIR/"
    else
        echo "  ERROR: No CSV files generated for seed $SEED"
    fi
done

# Reset seed to 0 in JCM
sed -i.bak "s/seed: *[0-9]\+/seed:       0/" "$JCM_FILE"
rm -f "$JCM_FILE.bak"

echo ""
echo "=========================================="
echo "All 10 seeds complete. Results in $RESULTS_DIR/"
echo "=========================================="
ls -la "$RESULTS_DIR/"
