#!/bin/bash
# Sensitivity sweep over the reciprocity-shaping coefficient ALPHA in
# record_outcome.java. For each ALPHA value, we run SEEDS_PER_VALUE seeds
# of the 1000-episode CFR experiment and save outputs to
# results/alpha_<value>/seed_<n>/.
#
# Usage (from project root):
#   bash scripts/run_alpha_sweep.sh
#
# After it finishes, run:
#   python3 scripts/plot_alpha_sweep.py
# to produce the sensitivity figure.

set -e

GRADLE=./gradle-8.5/bin/gradle
JCM_FILE=vesna.jcm
ALPHAS=(0.4 0.6 1.0 1.5)
SEEDS_PER_VALUE=5

if [ ! -x "$GRADLE" ]; then
    echo "ERROR: Gradle wrapper not found at $GRADLE"
    exit 1
fi

# Always run with cfr_learning: true.
sed -i.bak "s/cfr_learning: *[a-z]\+/cfr_learning: true/" "$JCM_FILE"
rm -f "$JCM_FILE.bak"

echo "==========================================================="
echo "Alpha sweep: alphas=${ALPHAS[*]}, seeds_per_value=$SEEDS_PER_VALUE"
echo "==========================================================="

for ALPHA in "${ALPHAS[@]}"; do
    SAFE=$(echo "$ALPHA" | tr '.' '_')
    OUT_BASE="results/alpha_${SAFE}"
    mkdir -p "$OUT_BASE"

    for SEED in $(seq 0 $((SEEDS_PER_VALUE - 1))); do
        echo
        echo "--- alpha=$ALPHA  seed=$SEED ---"

        sed -i.bak "s/seed: *[0-9]\+/seed:       $SEED/" "$JCM_FILE"
        rm -f "$JCM_FILE.bak"

        rm -f personality_evolution.csv carol_personality_evolution.csv \
              cfr_regrets.csv carol_cfr_regrets.csv \
              adapted_reciprocity.csv personality.json

        # Pass alpha to the JVM as a system property; build.gradle forwards
        # -Palpha=... via systemProperty 'alpha', and record_outcome reads it.
        "$GRADLE" -Palpha="$ALPHA" run --quiet 2>&1 | tail -3

        SEED_DIR="$OUT_BASE/seed_$SEED"
        mkdir -p "$SEED_DIR"
        for f in personality_evolution.csv carol_personality_evolution.csv \
                 cfr_regrets.csv carol_cfr_regrets.csv \
                 adapted_reciprocity.csv personality.json; do
            [ -f "$f" ] && cp "$f" "$SEED_DIR/"
        done
        echo "  saved -> $SEED_DIR/"
    done
done

# Restore JCM to seed 0 for subsequent ad-hoc runs.
sed -i.bak "s/seed: *[0-9]\+/seed:       0/" "$JCM_FILE"
rm -f "$JCM_FILE.bak"

echo
echo "==========================================================="
echo "Alpha sweep complete. Outputs under results/alpha_*/"
echo "Next: python3 scripts/plot_alpha_sweep.py"
echo "==========================================================="
