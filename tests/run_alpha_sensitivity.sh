#!/bin/bash
# Alpha sensitivity check for reward shaping coefficient
# Tests alpha in {0.4, 0.6, 0.8} with 3 seeds each
#
# Usage (from project root):
#   bash tests/run_alpha_sensitivity.sh

set -e
GRADLE=./gradle-8.5/bin/gradle
JCM_FILE=vesna.jcm
RESULTS_DIR=results/alpha_sensitivity

mkdir -p "$RESULTS_DIR"

# Ensure cfr_learning: true
sed -i.bak "s/cfr_learning: *[a-z]\+/cfr_learning: true/" "$JCM_FILE"
rm -f "$JCM_FILE.bak"

for ALPHA in 0.4 0.6 0.8; do
    for SEED in 0 1 2; do
        echo ""
        echo "--- alpha=$ALPHA, seed=$SEED ---"

        sed -i.bak "s/seed: *[0-9]\+/seed:       $SEED/" "$JCM_FILE"
        rm -f "$JCM_FILE.bak"

        rm -f personality_evolution.csv cfr_regrets.csv personality.json

        "$GRADLE" run --quiet -Palpha=$ALPHA 2>&1 | tail -3

        OUT_DIR="$RESULTS_DIR/alpha_${ALPHA}/seed_$SEED"
        mkdir -p "$OUT_DIR"
        cp personality_evolution.csv "$OUT_DIR/"
        cp cfr_regrets.csv "$OUT_DIR/"
        echo "  saved to $OUT_DIR/"
    done
done

sed -i.bak "s/seed: *[0-9]\+/seed:       0/" "$JCM_FILE"
rm -f "$JCM_FILE.bak"

echo ""
echo "Alpha sensitivity check complete. Results in $RESULTS_DIR/"
