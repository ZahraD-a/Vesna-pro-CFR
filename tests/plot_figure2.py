"""
Figure 2 — 10 seeds, 300 episodes.
6-panel layout (2 rows × 3 cols):

  (a) Alice Personality      (b) Bob Regrets       (c) Carol Regrets
  (d) Dave Regrets           (e) Carol Reciprocity  (f) Regret Gap Growth Rate

All lines = mean ± std across 10 seeds.
Output: results/fig2_personality_regrets.png

Run from project root:
    python tests/plot_figure2.py
"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

RESULTS_DIR = "results/reversal"
N_SEEDS     = 10
TRIM_EP     = 400   # show first N episodes for convergence panels
OUT         = "results/fig2_personality_regrets.png"

# ── Publication colour palette ────────────────────────────────────────────────
OCEAN = {                        # trait  : (colour,  label)
    "openness":          ("#2196F3", "Openness (O)"),
    "conscientiousness": ("#4CAF50", "Conscientiousness (C)"),
    "extraversion":      ("#FF9800", "Extraversion (E)"),
    "agreeableness":     ("#F44336", "Agreeableness (A)"),
    "neuroticism":       ("#9C27B0", "Neuroticism (N)"),
}
MARKERS = ["o", "s", "^", "D", "v"]

BOB_STYLE   = {"help_bob":    ("#1565C0","s","Help"),
               "decline_bob": ("#C62828","^","Decline"),
               "delay_bob":   ("#2E7D32","D","Delay")}
CAROL_STYLE = {"help_alice":    ("#1565C0","s","Help"),
               "decline_alice": ("#C62828","^","Decline"),
               "teach_alice":   ("#2E7D32","D","Teach")}
DAVE_STYLE  = {"help_dave":    ("#1565C0","s","Help"),
               "decline_dave": ("#C62828","^","Decline"),
               "suggest_dave": ("#2E7D32","D","Suggest")}


# ── helpers ───────────────────────────────────────────────────────────────────
def load_seeds(d, n):
    pers, regs, adapts = [], [], []
    for s in range(n):
        b = os.path.join(d, f"seed_{s}")
        pers.append(pd.read_csv(f"{b}/personality_evolution.csv"))
        regs.append(pd.read_csv(f"{b}/cfr_regrets.csv"))
        a = f"{b}/adapted_reciprocity.csv"
        if os.path.exists(a):
            adapts.append(pd.read_csv(a))
    return pers, regs, adapts

def ms(dfs, col):
    arr = np.array([df[col].values for df in dfs])
    return arr.mean(0), arr.std(0)

def band(ax, ep, m, s, color, label, lw=2.0, alpha=0.15,
         marker=None, every=25):
    kw = dict(color=color, linewidth=lw, label=label)
    if marker:
        kw.update(marker=marker, markersize=4.5,
                  markevery=every, markerfacecolor="white",
                  markeredgecolor=color, markeredgewidth=1.2)
    ax.plot(ep, m, **kw)
    ax.fill_between(ep, m - s, m + s, color=color, alpha=alpha)

def style(ax, ylabel="", ylim=None, legend_loc="best", legend=True):
    ax.set_xlabel("Episode", fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)
    if ylim:
        ax.set_ylim(ylim)
    ax.grid(alpha=0.20, linestyle="--", linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(50))
    if legend:
        ax.legend(fontsize=8, loc=legend_loc, framealpha=0.9,
                  edgecolor="lightgray")


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    pers, regs, adapts = load_seeds(RESULTS_DIR, N_SEEDS)
    n = len(pers)
    # trim to TRIM_EP episodes for convergence view
    pers   = [p[p["episode"] <= TRIM_EP].reset_index(drop=True) for p in pers]
    regs   = [r[r["episode"] <= TRIM_EP].reset_index(drop=True) for r in regs]
    adapts = [a[a["episode"] <= TRIM_EP].reset_index(drop=True) for a in adapts]
    ep_p = pers[0]["episode"].values
    ep_r = regs[0]["episode"].values
    ep_a = adapts[0]["episode"].values

    fig, axes = plt.subplots(2, 3, figsize=(16, 9),
                             gridspec_kw={"hspace": 0.42, "wspace": 0.34})

    n_ep = int(ep_r[-1])
    fig.suptitle(
        "VEsNA-Pro: Personality Evolution and Per-Colleague Regrets"
        f"  —  mean +/- std, {n} seeds, {n_ep} episodes",
        fontsize=12, fontweight="bold", y=1.01
    )

    every = 25   # marker every N episodes

    # ── (a) Alice personality ─────────────────────────────────────────────────
    ax = axes[0, 0]
    ax.set_title("(a)  Alice's Personality", fontsize=11, fontweight="bold")
    for i, (trait, (color, label)) in enumerate(OCEAN.items()):
        m, s = ms(pers, trait)
        band(ax, ep_p, m, s, color, label, marker=MARKERS[i], every=every)
    ax.axhline(0.5, color="black", lw=0.8, ls=":", alpha=0.35, label="Initial (0.5)")
    style(ax, ylabel="Trait value", ylim=(0.0, 1.0), legend_loc="center right")

    # ── (b) Bob ───────────────────────────────────────────────────────────────
    ax = axes[0, 1]
    ax.set_title("(b)  Bob  (Senior, reciprocity 0.40)", fontsize=11, fontweight="bold")
    ax.axhline(0, color="black", lw=0.7, alpha=0.4)
    for col, (color, marker, label) in BOB_STYLE.items():
        m, s = ms(regs, col)
        band(ax, ep_r, m, s, color, label, marker=marker, every=every)
    style(ax, ylabel="Cumulative regret", legend_loc="lower left")

    # ── (c) Carol ─────────────────────────────────────────────────────────────
    ax = axes[0, 2]
    ax.set_title("(c)  Carol  (Exploitative, reciprocity 0.10→0.84)",
                 fontsize=11, fontweight="bold")
    ax.axhline(0, color="black", lw=0.7, alpha=0.4)
    for col, (color, marker, label) in CAROL_STYLE.items():
        m, s = ms(regs, col)
        band(ax, ep_r, m, s, color, label, marker=marker, every=every)
    style(ax, ylabel="Cumulative regret", legend_loc="lower left")

    # ── (d) Dave ──────────────────────────────────────────────────────────────
    ax = axes[1, 0]
    ax.set_title("(d)  Dave  (Reciprocal, reciprocity 0.90)",
                 fontsize=11, fontweight="bold")
    ax.axhline(0, color="black", lw=0.7, alpha=0.4)
    for col, (color, marker, label) in DAVE_STYLE.items():
        m, s = ms(regs, col)
        band(ax, ep_r, m, s, color, label, marker=marker, every=every)
    style(ax, ylabel="Cumulative regret", legend_loc="lower left")

    # ── (e) Carol adaptive reciprocity ───────────────────────────────────────
    ax = axes[1, 1]
    ax.set_title("(e)  Colleague Adaptive Reciprocity",
                 fontsize=11, fontweight="bold")
    for col, color, label, innate in [
        ("carol_adapted", "#C62828", "Carol (innate 0.10)", 0.10),
        ("bob_adapted",   "#1565C0", "Bob   (innate 0.40)", 0.40),
        ("dave_adapted",  "#2E7D32", "Dave  (innate 0.90)", 0.90),
    ]:
        m, s = ms(adapts, col)
        band(ax, ep_a, m, s, color, label, lw=2.1, marker="o", every=every)
        ax.axhline(innate, color=color, lw=0.9, ls="--", alpha=0.40)
    ax.axhline(0.85, color="gray", lw=0.9, ls=":", alpha=0.55,
               label="Adaptation cap (0.85)")
    ax.axvspan(150, 300, color="gray", alpha=0.05)
    ax.text(158, 0.03, "converged", fontsize=8, color="gray")
    style(ax, ylabel="Reciprocity probability", ylim=(0.0, 1.0),
          legend_loc="center right")

    # ── (f) Carol regret-gap growth rate ─────────────────────────────────────
    ax = axes[1, 2]
    ax.set_title("(f)  Carol Regret-Gap Growth Rate\n"
                 "(decline − help) Δ per episode  →  0 = equilibrium reached",
                 fontsize=11, fontweight="bold")

    WINDOW = 20
    kernel = np.ones(WINDOW) / WINDOW
    all_rates = []
    for rr in regs:
        gap   = rr["decline_alice"].values - rr["help_alice"].values
        rate  = np.diff(gap)
        smoothed = np.convolve(rate, kernel, mode="valid")
        all_rates.append(smoothed)

    arr   = np.array(all_rates)
    m, s  = arr.mean(0), arr.std(0)
    ep_rate = ep_r[WINDOW:]

    ax.plot(ep_rate, m, color="#C62828", lw=2.2, label="Gap growth rate (smoothed)")
    ax.fill_between(ep_rate, m - s, m + s, color="#C62828", alpha=0.15)
    ax.axhline(0, color="black", lw=0.9, alpha=0.5)
    ax.axvspan(150, 300, color="gray", alpha=0.05)
    ax.text(158, m.max() * 0.12, "≈ 0\n(equilibrium)", fontsize=8, color="gray")
    style(ax, ylabel="Δ regret gap per episode", legend_loc="upper right")

    os.makedirs("results", exist_ok=True)
    plt.savefig(OUT, dpi=200, bbox_inches="tight")
    print(f"Saved: {OUT}")
    plt.close()

    # summary
    print(f"\n=== Final personality (ep {n_ep}, {n} seeds) ===")
    arr = np.array([[p.iloc[-1][t] for t in
                     ["openness","conscientiousness","extraversion",
                      "agreeableness","neuroticism"]] for p in pers])
    for i, nm in enumerate(["O","C","E","A","N"]):
        print(f"  {nm}: {arr[:,i].mean():.4f} ± {arr[:,i].std():.4f}")

    carol_final = np.array([a["carol_adapted"].iloc[-1] for a in adapts])
    print(f"\n  Carol reciprocity: {carol_final.mean():.4f} ± {carol_final.std():.4f}"
          f"  (innate 0.10)")


if __name__ == "__main__":
    main()
