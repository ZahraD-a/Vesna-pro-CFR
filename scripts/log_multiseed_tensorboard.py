#!/usr/bin/env python3
"""Write per-seed and mean TensorBoard event files from a 10-seed run.

Reads results/seed_<n>/{personality_evolution.csv,
carol_personality_evolution.csv, cfr_regrets.csv,
carol_cfr_regrets.csv, adapted_reciprocity.csv} for every available
seed and writes:

    runs/multiseed/seed_<n>/   one run per seed (Alice and Carol scalars)
    runs/multiseed/mean/       one run holding the across-seed mean of
                               every scalar (acts as the "central" line)
    runs/multiseed/std/        one run holding the across-seed std

In TensorBoard, each run is plotted with its own colour by default. The
"mean" run will appear thicker on top of the per-seed cloud once you
toggle the runs you want.

Usage (from project root):
    python3 scripts/log_multiseed_tensorboard.py
    tensorboard --logdir runs/multiseed
"""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from torch.utils.tensorboard import SummaryWriter
except ImportError:
    try:
        from tensorboardX import SummaryWriter
    except ImportError:
        sys.stderr.write("Requires torch or tensorboardX.\n")
        sys.exit(1)


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
RUNS    = ROOT / "runs" / "multiseed"

OCEAN = ["openness", "conscientiousness", "extraversion",
         "agreeableness", "neuroticism"]

ALICE_REGRET_VS_CAROL = ["help_alice", "decline_alice", "teach_alice"]
ALICE_REGRET_VS_BOB   = ["help_bob", "decline_bob", "delay_bob"]
ALICE_REGRET_VS_DAVE  = ["help_dave", "decline_dave", "suggest_dave"]


def collect_seeds():
    out = {}
    for d in sorted(RESULTS.glob("seed_*")):
        try:
            s = int(d.name.split("_")[1])
        except (IndexError, ValueError):
            continue
        out[s] = d
    return out


def load_seed_dfs(seed_dir):
    """Load every CSV present for a seed; returns dict name -> DataFrame."""
    files = {
        "alice":      "personality_evolution.csv",
        "carol":      "carol_personality_evolution.csv",
        "alice_reg":  "cfr_regrets.csv",
        "carol_reg":  "carol_cfr_regrets.csv",
        "recip":      "adapted_reciprocity.csv",
    }
    out = {}
    for k, f in files.items():
        p = seed_dir / f
        if p.exists():
            df = pd.read_csv(p)
            if "episode" in df.columns:
                df["episode"] = pd.to_numeric(df["episode"],
                                              errors="coerce")
                df = df.dropna(subset=["episode"]).astype({"episode": int})
            out[k] = df
    return out


def write_seed_run(writer, dfs):
    """Emit every scalar for one seed."""
    if "alice" in dfs:
        for _, row in dfs["alice"].iterrows():
            ep = int(row["episode"])
            for trait in OCEAN:
                if trait in row:
                    writer.add_scalar(f"alice/OCEAN/{trait.capitalize()}",
                                      float(row[trait]), ep)
            for m in ("stress", "satisfaction", "social_energy"):
                if m in row:
                    try:
                        writer.add_scalar(
                            f"alice/Mood/{m.capitalize()}",
                            float(row[m]), ep)
                    except (ValueError, TypeError):
                        pass
            if "total_reward" in row:
                try:
                    writer.add_scalar("alice/Reward/Total",
                                      float(row["total_reward"]), ep)
                except (ValueError, TypeError):
                    pass

    if "alice_reg" in dfs:
        for _, row in dfs["alice_reg"].iterrows():
            ep = int(row["episode"])
            for a in ALICE_REGRET_VS_BOB:
                if a in row:
                    writer.add_scalar(f"alice/Regret_Bob/{a}",
                                      float(row[a]), ep)
            for a in ALICE_REGRET_VS_CAROL:
                if a in row:
                    writer.add_scalar(f"alice/Regret_Carol/{a}",
                                      float(row[a]), ep)
            for a in ALICE_REGRET_VS_DAVE:
                if a in row:
                    writer.add_scalar(f"alice/Regret_Dave/{a}",
                                      float(row[a]), ep)

    if "carol" in dfs:
        for _, row in dfs["carol"].iterrows():
            ep = int(row["episode"])
            for trait in OCEAN:
                col = f"carol_{trait}"
                if col in row:
                    writer.add_scalar(f"carol/OCEAN/{trait.capitalize()}",
                                      float(row[col]), ep)

    if "carol_reg" in dfs:
        for _, row in dfs["carol_reg"].iterrows():
            ep = int(row["episode"])
            for col, name in (("carol_help_regret",        "help"),
                              ("carol_decline_regret",     "decline"),
                              ("carol_reciprocate_regret", "reciprocate")):
                if col in row:
                    writer.add_scalar(f"carol/Regret/{name}",
                                      float(row[col]), ep)

    if "recip" in dfs:
        for _, row in dfs["recip"].iterrows():
            ep = int(row["episode"])
            for col, name in (("carol_adapted",        "Adapted"),
                              ("carol_observed_ratio", "Observed"),
                              ("carol_phi",            "Exploitation_Flag")):
                if col in row:
                    try:
                        writer.add_scalar(f"carol/Reciprocity/{name}",
                                          float(row[col]), ep)
                    except (ValueError, TypeError):
                        pass


# --- mean and std aggregation -----------------------------------------------

OCEAN_TAGS = {f"alice/OCEAN/{t.capitalize()}": ("alice", t)
              for t in OCEAN}
OCEAN_TAGS.update({f"carol/OCEAN/{t.capitalize()}": ("carol", f"carol_{t}")
                   for t in OCEAN})

REGRET_TAGS = {f"alice/Regret_Carol/{a}": ("alice_reg", a)
               for a in ALICE_REGRET_VS_CAROL}
REGRET_TAGS.update({f"alice/Regret_Bob/{a}": ("alice_reg", a)
                    for a in ALICE_REGRET_VS_BOB})
REGRET_TAGS.update({f"alice/Regret_Dave/{a}": ("alice_reg", a)
                    for a in ALICE_REGRET_VS_DAVE})

RECIP_TAGS = {
    "carol/Reciprocity/Adapted":          ("recip", "carol_adapted"),
    "carol/Reciprocity/Observed":         ("recip", "carol_observed_ratio"),
}


def stack_on_grid(per_seed_dfs, df_key, value_col, grid):
    rows = []
    for s, dfs in per_seed_dfs.items():
        df = dfs.get(df_key)
        if df is None or value_col not in df.columns:
            continue
        df = df.sort_values("episode")
        rows.append(np.interp(grid, df["episode"].to_numpy(),
                              df[value_col].to_numpy(dtype=float)))
    if not rows:
        return None
    return np.vstack(rows)


def write_mean_std_run(mean_writer, std_writer, per_seed_dfs, grid):
    all_tags = list(OCEAN_TAGS.items()) + list(REGRET_TAGS.items()) \
        + list(RECIP_TAGS.items())
    for tag, (df_key, value_col) in all_tags:
        stack = stack_on_grid(per_seed_dfs, df_key, value_col, grid)
        if stack is None:
            continue
        m = stack.mean(axis=0)
        s = stack.std(axis=0)
        for i, ep in enumerate(grid):
            mean_writer.add_scalar(tag, float(m[i]), int(ep))
            std_writer.add_scalar(tag, float(s[i]), int(ep))


def main():
    seeds = collect_seeds()
    if not seeds:
        sys.stderr.write("No results/seed_* found.\n")
        return 1

    if RUNS.exists():
        # Wipe previous TensorBoard tree to avoid mixing colours.
        for child in RUNS.glob("**/*"):
            if child.is_file():
                child.unlink()
        for child in sorted(RUNS.glob("*"), reverse=True):
            if child.is_dir():
                try:
                    child.rmdir()
                except OSError:
                    pass
    RUNS.mkdir(parents=True, exist_ok=True)

    per_seed_dfs = {}
    for seed, sdir in seeds.items():
        dfs = load_seed_dfs(sdir)
        per_seed_dfs[seed] = dfs
        run_dir = RUNS / f"seed_{seed:02d}"
        writer = SummaryWriter(str(run_dir))
        write_seed_run(writer, dfs)
        writer.flush()
        writer.close()
        print(f"  wrote {run_dir.name}")

    # Aggregated mean and std on the common grid.
    max_eps = []
    for dfs in per_seed_dfs.values():
        for k in ("alice", "alice_reg", "carol", "carol_reg", "recip"):
            df = dfs.get(k)
            if df is not None and "episode" in df.columns and len(df):
                max_eps.append(int(df["episode"].max()))
    n_eps = min(max_eps) if max_eps else 0
    grid = np.arange(0, n_eps + 1)

    mean_w = SummaryWriter(str(RUNS / "mean"))
    std_w  = SummaryWriter(str(RUNS / "std"))
    write_mean_std_run(mean_w, std_w, per_seed_dfs, grid)
    mean_w.flush(); mean_w.close()
    std_w.flush();  std_w.close()
    print(f"  wrote mean + std (grid 0..{n_eps})")

    print(f"\nDone. Launch:\n  tensorboard --logdir runs/multiseed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
