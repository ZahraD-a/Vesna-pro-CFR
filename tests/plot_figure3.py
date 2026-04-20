"""
Figure 3 — EMA-corrected reversal: 10 seeds, 400 episodes.
4-panel layout:

  (a) Carol ρ_observed trajectory  (b) φ(Carol) exploitation flag
  (c) Instantaneous decline_carol  (d) Cumulative decline_carol → zero-crossing

Output: results/fig3_reversal.png

Run from project root:
    python tests/plot_figure3.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

RESULTS_DIR = "results"
N_SEEDS     = 10
OUT         = "results/fig3_reversal.png"


def ms(dfs, col):
    arr = np.array([df[col].values for df in dfs])
    return arr.mean(0), arr.std(0)

def band(ax, ep, m, s, color, label, lw=2.2, alpha=0.15, ls="-",
         marker=None, every=50):
    kw = dict(color=color, linewidth=lw, label=label, linestyle=ls)
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
        ax.legend(fontsize=8.5, loc=legend_loc, framealpha=0.9,
                  edgecolor="lightgray")

def find_zero_crossing(ep, vals_list):
    crossings = []
    for vals in vals_list:
        for i in range(1, len(vals)):
            if vals[i-1] > 0 and vals[i] <= 0:
                crossings.append(int(ep[i]))
                break
    if not crossings:
        return None, None
    return float(np.mean(crossings)), float(np.std(crossings))

def find_last_phi_episode(ep, phi_series_list):
    last_eps = []
    for phi in phi_series_list:
        idxs = np.where(phi > 0)[0]
        if len(idxs):
            last_eps.append(int(ep[idxs[-1]]))
    if not last_eps:
        return None, None
    return float(np.mean(last_eps)), float(np.std(last_eps))


def main():
    regs, adapts = [], []
    for s in range(N_SEEDS):
        b = os.path.join(RESULTS_DIR, f"seed_{s}")
        regs.append(pd.read_csv(f"{b}/cfr_regrets.csv"))
        a = f"{b}/adapted_reciprocity.csv"
        if os.path.exists(a):
            adapts.append(pd.read_csv(a))

    n = len(regs)
    ep_r = regs[0]["episode"].values
    ep_a = adapts[0]["episode"].values if adapts else ep_r

    # compute decline_carol zero-crossing
    dc_series = [r["decline_carol"].values for r in regs]
    zc_mean, zc_std = find_zero_crossing(ep_r, dc_series)

    # compute phi deactivation episodes
    phi_series = [a["carol_phi"].values for a in adapts]
    phi_off_mean, phi_off_std = find_last_phi_episode(ep_a, phi_series)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9),
                             gridspec_kw={"hspace": 0.44, "wspace": 0.36})
    fig.suptitle(
        "VEsNA-Pro (EMA fix, α=0.12): Carol Exploitation Deactivation → Regret Reversal"
        f"  —  mean ± std, {n} seeds, 400 episodes",
        fontsize=12, fontweight="bold", y=1.01
    )

    # ── (a) Carol ρ_observed ────────────────────────────────────────────────
    ax = axes[0, 0]
    ax.set_title("(a)  Carol ρ_observed  (EMA, α=0.12)", fontsize=11, fontweight="bold")
    m, s = ms(adapts, "carol_observed_ratio")
    band(ax, ep_a, m, s, "#1565C0", "ρ_observed (EMA)", lw=2.4, marker="o", every=50)
    m2, s2 = ms(adapts, "carol_adapted")
    band(ax, ep_a, m2, s2, "#880E4F", "Carol adapted reciprocity", lw=2.0, ls="--")
    ax.axhline(0.2, color="#C62828", lw=1.2, ls=":", alpha=0.7,
               label="φ threshold (0.20)")
    ax.axhline(0.10, color="gray", lw=0.9, ls=":", alpha=0.5,
               label="Carol innate (0.10)")
    if phi_off_mean:
        ax.axvline(phi_off_mean, color="#C62828", lw=1.2, ls="--", alpha=0.6)
        ax.text(phi_off_mean + 5, 0.26,
                f"φ off\n≈ ep {phi_off_mean:.0f}", fontsize=8, color="#C62828")
    style(ax, ylabel="Reciprocity probability", ylim=(0.0, 1.0),
          legend_loc="center right")

    # ── (b) φ(Carol) exploitation flag ─────────────────────────────────────
    ax = axes[0, 1]
    ax.set_title("(b)  φ(Carol) Exploitation Flag", fontsize=11, fontweight="bold")
    phi_arr = np.array([a["carol_phi"].values for a in adapts])
    phi_m = phi_arr.mean(0)
    phi_s = phi_arr.std(0)
    ax.plot(ep_a, phi_m, color="#C62828", lw=2.4, label="φ active (fraction of seeds)")
    ax.fill_between(ep_a, np.clip(phi_m - phi_s, 0, 1),
                    np.clip(phi_m + phi_s, 0, 1), color="#C62828", alpha=0.15)
    ax.axhline(0, color="black", lw=0.7, alpha=0.4)
    ax.axhline(1, color="black", lw=0.7, alpha=0.2, ls=":")
    if phi_off_mean:
        ax.axvspan(phi_off_mean - phi_off_std, phi_off_mean + phi_off_std,
                   color="#C62828", alpha=0.12)
        ax.axvline(phi_off_mean, color="#C62828", lw=1.4, ls="--", alpha=0.75)
        ax.text(phi_off_mean + 5, 0.6,
                f"Last φ=1\n≈ ep {phi_off_mean:.0f} ± {phi_off_std:.0f}",
                fontsize=8.5, color="#C62828")
    ax.set_ylabel("φ(Carol) — exploitation active", fontsize=10)
    style(ax, ylim=(-0.05, 1.15), legend_loc="upper right")

    # ── (c) Instantaneous decline_carol regret ──────────────────────────────
    ax = axes[1, 0]
    ax.set_title("(c)  Instantaneous Δdecline_carol per Episode",
                 fontsize=11, fontweight="bold")
    WINDOW = 15
    kernel = np.ones(WINDOW) / WINDOW
    inst_arr = []
    for rr in regs:
        dc = rr["decline_carol"].values
        diff = np.diff(dc)
        smooth = np.convolve(diff, kernel, mode="valid")
        inst_arr.append(smooth)
    inst_arr = np.array(inst_arr)
    m_inst = inst_arr.mean(0)
    s_inst = inst_arr.std(0)
    ep_inst = ep_r[WINDOW:]
    ax.plot(ep_inst, m_inst, color="#C62828", lw=2.2,
            label=f"Δdecline_carol (smoothed w={WINDOW})")
    ax.fill_between(ep_inst, m_inst - s_inst, m_inst + s_inst,
                    color="#C62828", alpha=0.15)
    ax.axhline(0, color="black", lw=1.0, alpha=0.6)
    if phi_off_mean:
        ax.axvline(phi_off_mean, color="#C62828", lw=1.0, ls=":", alpha=0.5,
                   label=f"φ off (≈ ep {phi_off_mean:.0f})")
    # mark where trend reverses (max then descends)
    peak_idx = np.argmax(m_inst)
    ax.axvline(ep_inst[peak_idx], color="gray", lw=0.9, ls="--", alpha=0.5)
    ax.text(ep_inst[peak_idx] + 5, m_inst.max() * 0.7,
            f"peak\nep {ep_inst[peak_idx]}", fontsize=8, color="gray")
    style(ax, ylabel="Δ decline_carol regret / episode", legend_loc="upper right")

    # ── (d) Cumulative decline_carol regret ─────────────────────────────────
    ax = axes[1, 1]
    title_zc = f"≈ ep {zc_mean:.0f} ± {zc_std:.0f}" if zc_mean else "> 400 ep"
    ax.set_title(f"(d)  Cumulative decline_carol  →  zero-crossing {title_zc}",
                 fontsize=11, fontweight="bold")
    dc_m, dc_s = ms(regs, "decline_carol")
    hc_m, hc_s = ms(regs, "help_carol")
    band(ax, ep_r, dc_m, dc_s, "#C62828", "decline_carol regret",
         lw=2.4, marker="s", every=50)
    band(ax, ep_r, hc_m, hc_s, "#1565C0", "help_carol regret",
         lw=2.0, marker="o", every=50)
    ax.axhline(0, color="black", lw=1.0, alpha=0.6)
    if zc_mean:
        ax.axvspan(zc_mean - zc_std, zc_mean + zc_std,
                   color="#C62828", alpha=0.12)
        ax.axvline(zc_mean, color="#C62828", lw=1.4, ls="--", alpha=0.75)
        ax.text(zc_mean + 8, dc_m.min() * 0.4,
                f"Mean zero-crossing\n≈ ep {zc_mean:.0f} ± {zc_std:.0f}",
                fontsize=8.5, color="#C62828")
    if phi_off_mean:
        ax.axvline(phi_off_mean, color="gray", lw=1.0, ls=":", alpha=0.5,
                   label=f"φ off (≈ ep {phi_off_mean:.0f})")
    style(ax, ylabel="Cumulative regret (Alice → Carol)", legend_loc="upper left")

    os.makedirs("results", exist_ok=True)
    plt.savefig(OUT, dpi=200, bbox_inches="tight")
    print(f"Saved: {OUT}")
    plt.close()

    print(f"\n=== EMA reversal stats ({n} seeds, 400 ep) ===")
    if phi_off_mean:
        print(f"  phi(Carol) last active: ep {phi_off_mean:.0f} +/- {phi_off_std:.0f}")
    if zc_mean:
        print(f"  decline_carol zero-crossing: ep {zc_mean:.0f} +/- {zc_std:.0f}")
    else:
        print("  decline_carol: mean trending to zero but not all seeds cross by ep 400")
        print(f"  decline_carol mean at ep 400: {dc_m[-1]:.1f}")

    print(f"\n  Carol rho_observed at ep 400: {ms(adapts, 'carol_observed_ratio')[0][-1]:.4f}")
    print(f"  Carol adapted reciprocity at ep 400: {ms(adapts, 'carol_adapted')[0][-1]:.4f}")


if __name__ == "__main__":
    main()
