#!/usr/bin/env python3
"""Convert the CSV logs produced by a training run into TensorBoard event files.

Reads the five CSV files written by PolicyLogger and the two reciprocity
trackers at the project root, and writes a TensorBoard run tree under
``runs/vesna/`` containing three logical runs:

    alice     -- Alice's OCEAN, mood, total reward, and per-colleague regrets
    carol     -- Carol's OCEAN, action regrets, reciprocity statistics
    coupling  -- key signals on a shared scale for side-by-side visualisation

Usage (from project root):
    python3 scripts/log_to_tensorboard.py
    tensorboard --logdir runs/vesna
"""

import csv
import os
import sys
from pathlib import Path

try:
    from torch.utils.tensorboard import SummaryWriter
except ImportError:
    try:
        from tensorboardX import SummaryWriter
    except ImportError:
        sys.stderr.write(
            "Requires torch or tensorboardX. "
            "Install with: pip install tensorboard torch\n")
        sys.exit(1)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_ROOT / "runs" / "vesna"

OCEAN_TRAITS = [
    "openness", "conscientiousness", "extraversion",
    "agreeableness", "neuroticism",
]


def read_csv(path):
    if not path.exists():
        print(f"warning: {path} not found, skipping")
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    w_alice    = SummaryWriter(str(RUNS_DIR / "alice"))
    w_carol    = SummaryWriter(str(RUNS_DIR / "carol"))
    w_coupling = SummaryWriter(str(RUNS_DIR / "coupling"))

    # --- Alice: personality + mood + reward ----------------------------------
    alice_rows = read_csv(PROJECT_ROOT / "personality_evolution.csv")
    for row in alice_rows:
        ep = to_float(row.get("episode"))
        if ep is None:
            continue
        ep = int(ep)
        for trait in OCEAN_TRAITS:
            v = to_float(row.get(trait))
            if v is not None:
                w_alice.add_scalar(f"OCEAN/{trait.capitalize()}", v, ep)
        for m in ("stress", "satisfaction", "social_energy"):
            v = to_float(row.get(m))
            if v is not None:
                w_alice.add_scalar(f"Mood/{m.capitalize()}", v, ep)
        r = to_float(row.get("total_reward"))
        if r is not None:
            w_alice.add_scalar("Learning/Total_Reward", r, ep)

    # --- Alice's regrets, grouped per colleague ------------------------------
    alice_reg_rows = read_csv(PROJECT_ROOT / "cfr_regrets.csv")
    alice_reg_by_ep = {}
    for row in alice_reg_rows:
        ep = to_float(row.get("episode"))
        if ep is None:
            continue
        ep = int(ep)
        alice_reg_by_ep[ep] = row
        for a in ("help_bob", "decline_bob", "delay_bob"):
            v = to_float(row.get(a))
            if v is not None:
                w_alice.add_scalar(f"Regret_vs_Bob/{a}", v, ep)
        for a in ("help_alice", "decline_alice", "teach_alice"):
            v = to_float(row.get(a))
            if v is not None:
                w_alice.add_scalar(f"Regret_vs_Carol/{a}", v, ep)
        for a in ("help_dave", "decline_dave", "suggest_dave"):
            v = to_float(row.get(a))
            if v is not None:
                w_alice.add_scalar(f"Regret_vs_Dave/{a}", v, ep)

    # --- Carol: personality + regrets ---------------------------------------
    carol_rows = read_csv(PROJECT_ROOT / "carol_personality_evolution.csv")
    carol_by_ep = {}
    for row in carol_rows:
        ep = to_float(row.get("episode"))
        if ep is None:
            continue
        ep = int(ep)
        carol_by_ep[ep] = row
        for trait in OCEAN_TRAITS:
            v = to_float(row.get(f"carol_{trait}"))
            if v is not None:
                w_carol.add_scalar(f"OCEAN/{trait.capitalize()}", v, ep)

    carol_reg_rows = read_csv(PROJECT_ROOT / "carol_cfr_regrets.csv")
    for row in carol_reg_rows:
        ep = to_float(row.get("episode"))
        if ep is None:
            continue
        ep = int(ep)
        for col, short in (
            ("carol_help_regret",        "help"),
            ("carol_decline_regret",     "decline"),
            ("carol_reciprocate_regret", "reciprocate"),
        ):
            v = to_float(row.get(col))
            if v is not None:
                w_carol.add_scalar(f"Regret/{short}", v, ep)

    # --- Reciprocity: Carol's adapted and observed --------------------------
    recip_rows = read_csv(PROJECT_ROOT / "adapted_reciprocity.csv")
    for row in recip_rows:
        ep = to_float(row.get("episode"))
        if ep is None:
            continue
        ep = int(ep)
        for col, name in (
            ("carol_adapted",         "Adapted"),
            ("carol_observed_ratio",  "Observed"),
            ("carol_phi",             "Exploitation_Flag"),
        ):
            v = to_float(row.get(col))
            if v is not None:
                w_carol.add_scalar(f"Reciprocity/{name}", v, ep)

    # --- Coupling view: Carol's reciprocity and Alice's normalised regret ---
    def col_absmax(rows, key):
        vals = [abs(to_float(r.get(key)) or 0.0) for r in rows]
        m = max(vals, default=1.0)
        return m if m > 0 else 1.0

    help_max    = col_absmax(alice_reg_rows, "help_alice")
    decline_max = col_absmax(alice_reg_rows, "decline_alice")

    for row in recip_rows:
        ep = to_float(row.get("episode"))
        if ep is None:
            continue
        ep = int(ep)
        adapted = to_float(row.get("carol_adapted"))
        if adapted is not None:
            w_coupling.add_scalar(
                "StorySignals/Carol_Reciprocity_Adapted", adapted, ep)

        crow = carol_by_ep.get(ep)
        if crow is not None:
            v = to_float(crow.get("carol_agreeableness"))
            if v is not None:
                w_coupling.add_scalar("StorySignals/Carol_Agreeableness", v, ep)

        arow = alice_reg_by_ep.get(ep)
        if arow is not None:
            h = to_float(arow.get("help_alice"))
            d = to_float(arow.get("decline_alice"))
            if h is not None:
                w_coupling.add_scalar(
                    "StorySignals/Alice_help_regret_norm", h / help_max, ep)
            if d is not None:
                w_coupling.add_scalar(
                    "StorySignals/Alice_decline_regret_norm",
                    d / decline_max, ep)

    # Alice's agreeableness also on coupling axis
    for row in alice_rows:
        ep = to_float(row.get("episode"))
        if ep is None:
            continue
        ep = int(ep)
        a = to_float(row.get("agreeableness"))
        if a is not None:
            w_coupling.add_scalar("StorySignals/Alice_Agreeableness", a, ep)

    for w in (w_alice, w_carol, w_coupling):
        w.flush()
        w.close()

    print(f"Wrote TensorBoard event files to: {RUNS_DIR}")
    print(f"Launch: tensorboard --logdir {RUNS_DIR.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
