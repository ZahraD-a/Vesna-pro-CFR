#!/bin/bash
# Run the CFR personality learning experiment with 10 different seeds (0-9)
# Saves per-seed CSV outputs under results/seed_N/ (CFR) or results/static/seed_N/ (baseline)
#
# Usage (from project root):
#   bash tests/run_10_seeds.sh           # CFR learning mode (default)
#   bash tests/run_10_seeds.sh static    # Static baseline (no learning)
#
# Requirements:
#   - vesna.jcm must have a "seed: <N>" line (any non-negative integer)
#   - vesna.jcm must have a "cfr_learning:" line
#   - gradle-8.5 installed at ./gradle-8.5/bin/gradle

set -e

GRADLE=./gradle-8.5/bin/gradle
JCM_FILE=vesna.jcm

MODE="${1:-cfr}"

if [ "$MODE" = "static" ]; then
    RESULTS_DIR=results/static
    CFR_VALUE=false
    echo "Mode: STATIC BASELINE (cfr_learning: false)"
elif [ "$MODE" = "cfr" ]; then
    RESULTS_DIR=results
    CFR_VALUE=true
    echo "Mode: CFR LEARNING (cfr_learning: true)"
else
    echo "ERROR: Unknown mode '$MODE'. Use 'cfr' or 'static'."
    exit 1
fi

# Verify gradle
if [ ! -x "$GRADLE" ]; then
    echo "ERROR: Gradle not found at $GRADLE"
    exit 1
fi

# Verify JCM has a seed line
if ! grep -q "seed:" "$JCM_FILE"; then
    echo "ERROR: $JCM_FILE has no 'seed:' line to replace."
    exit 1
fi

# Set cfr_learning value in JCM
sed -i.bak "s/cfr_learning: *[a-z]\+/cfr_learning: $CFR_VALUE/" "$JCM_FILE"
rm -f "$JCM_FILE.bak"

mkdir -p "$RESULTS_DIR"

echo "=========================================="
echo "Running 10-seed experiment ($MODE mode)"
echo "=========================================="

for SEED in 0 1 2 3 4 5 6 7 8 9; do
    echo ""
    echo "--- Seed $SEED ($MODE) ---"

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

# Reset to seed 0 + cfr mode in JCM
sed -i.bak "s/seed: *[0-9]\+/seed:       0/" "$JCM_FILE"
sed -i.bak "s/cfr_learning: *[a-z]\+/cfr_learning: true/" "$JCM_FILE"
rm -f "$JCM_FILE.bak"

echo ""
echo "=========================================="
echo "All 10 seeds complete ($MODE mode). Results in $RESULTS_DIR/"
echo "=========================================="
ls -la "$RESULTS_DIR/" 2>/dev/null | grep seed_
