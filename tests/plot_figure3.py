"""
Figure 3 — Standard CFR reversal: 10 seeds, 2000 episodes.
5-panel layout (2 rows x 3 cols, last cell empty):

  (a) Carol adapted reciprocity    (b) Carol rho_observed
  (c) phi(Carol) exploitation flag (d) Instantaneous decline_carol
  (e) Cumulative decline_carol -> zero-crossing

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

REVERSAL_DIR = "results/reversal"
N_SEEDS      = 10
OUT          = "results/fig3_reversal.png"


def ms(dfs, col):
    arr = np.array([df[col].values for df in dfs])
    return arr.mean(0), arr.std(0)

def band(ax, ep, m, s, color, label, lw=2.2, alpha=0.15, ls="-",
         marker=None, every=200):
    kw = dict(color=color, linewidth=lw, label=label, linestyle=ls)
    if marker:
        kw.update(marker=marker, markersize=4.5,
                  markevery=every, markerfacecolor="white",
                  markeredgecolor=color, markeredgewidth=1.2)
    ax.plot(ep, m, **kw)
    ax.fill_between(ep, m - s, m + s, color=color, alpha=alpha)

def style(ax, ylabel="", ylim=None, legend_loc="best", legend=True, every=200):
    ax.set_xlabel("Episode", fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)
    if ylim:
        ax.set_ylim(ylim)
    ax.grid(alpha=0.20, linestyle="--", linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(200))
    if legend:
        ax.legend(fontsize=8.5, loc=legend_loc, framealpha=0.9,
                  edgecolor="lightgray")

def find_crossing(ep, vals_list, threshold=0.0, upward=False):
    """Find first episode where vals cross threshold.
    upward=True: find first crossing from below to above.
    upward=False: find first crossing from above to below, then back above (upward after dip).
    For rho_observed crossing 0.20 upward after initial dip: use upward=True and
    skip the very first crossing if rho starts above threshold.
    """
    crossings = []
    for vals in vals_list:
        dipped = vals[0] > threshold  # starts above — wait for dip then recovery
        for i in range(1, len(vals)):
            if dipped and vals[i-1] < threshold:
                dipped = False  # has dipped below
            if not dipped and vals[i-1] < threshold and vals[i] >= threshold:
                crossings.append(int(ep[i])); break
        if not crossings or crossings[-1] == 0:
            # fallback: simple upward crossing
            for i in range(1, len(vals)):
                if vals[i-1] < threshold and vals[i] >= threshold:
                    crossings.append(int(ep[i])); break
    if not crossings:
        return None, None
    return float(np.mean(crossings)), float(np.std(crossings))


def main():
    n_seeds = 0
    regs, adapts = [], []
    for s in range(N_SEEDS):
        b = os.path.join(REVERSAL_DIR, f"seed_{s}")
        r = f"{b}/cfr_regrets.csv"
        a = f"{b}/adapted_reciprocity.csv"
        if os.path.exists(r) and os.path.exists(a):
            regs.append(pd.read_csv(r))
            adapts.append(pd.read_csv(a))
            n_seeds += 1
    print(f"Loaded {n_seeds} seeds")

    ep_r = regs[0]["episode"].values
    ep_a = adapts[0]["episode"].values
    n_ep = int(ep_r[-1])

    # compute key milestones
    phi_series  = [a["carol_phi"].values for a in adapts]
    rho_series  = [a["carol_observed_ratio"].values for a in adapts]
    dc_series   = [r["decline_carol"].values for r in regs]

    # last episode phi=1 per seed
    phi_off_eps = []
    for phi in phi_series:
        idxs = np.where(phi == 1)[0]
        if len(idxs): phi_off_eps.append(int(ep_a[idxs[-1]]))
    phi_off_mean = float(np.mean(phi_off_eps)) if phi_off_eps else None
    phi_off_std  = float(np.std(phi_off_eps))  if phi_off_eps else None

    # rho crosses 0.20 upward (after initial dip below 0.20)
    rho_cross_mean, rho_cross_std = find_crossing(ep_a, rho_series, threshold=0.20)

    # decline_carol cumulative zero-crossing (from positive to zero/negative)
    dc_series_neg = [(-v) for v in dc_series]  # flip so we find downward cross at 0
    zc_mean, zc_std = find_crossing(ep_r, dc_series_neg, threshold=0.0)

    fig, axes = plt.subplots(2, 3, figsize=(18, 9),
                             gridspec_kw={"hspace": 0.44, "wspace": 0.34})
    fig.suptitle(
        "VEsNA-Pro: Standard CFR — Conservative Trust Recovery and Social Reversal"
        f"  (mean +/- std, {n_seeds} seeds, {n_ep} episodes)",
        fontsize=12, fontweight="bold", y=1.01
    )

    def vline(ax, x, label, color="gray", ls="--", lw=1.1, ypos=0.92):
        ax.axvline(x, color=color, lw=lw, ls=ls, alpha=0.7)
        ax.text(x + n_ep * 0.015, ax.get_ylim()[0] +
                (ax.get_ylim()[1] - ax.get_ylim()[0]) * ypos,
                label, fontsize=8, color=color)

    # ── (a) Carol adapted reciprocity ──────────────────────────────────────
    ax = axes[0, 0]
    ax.set_title("(a)  Carol Adapted Reciprocity", fontsize=11, fontweight="bold")
    m, s = ms(adapts, "carol_adapted")
    m2, s2 = ms(adapts, "bob_adapted")
    band(ax, ep_a, m,  s,  "#C62828", "Carol (innate 0.10)", lw=2.4, marker="o")
    band(ax, ep_a, m2, s2, "#1565C0", "Bob   (innate 0.40)", lw=2.0, marker="s")
    ax.axhline(0.85, color="gray", lw=0.9, ls=":", alpha=0.5,
               label="Adaptation cap (0.85)")
    ax.axhline(0.10, color="#C62828", lw=0.8, ls=":", alpha=0.4)
    style(ax, ylabel="Reciprocity probability", ylim=(0.0, 1.0),
          legend_loc="center right")

    # ── (b) rho_observed ───────────────────────────────────────────────────
    ax = axes[0, 1]
    ax.set_title("(b)  Carol rho_observed  (cumulative ratio)", fontsize=11, fontweight="bold")
    m, s = ms(adapts, "carol_observed_ratio")
    band(ax, ep_a, m, s, "#1565C0", "rho_observed(Carol)", lw=2.4, marker="o")
    ax.axhline(0.20, color="#C62828", lw=1.2, ls="--", alpha=0.7,
               label="phi threshold (0.20)")
    ax.axhline(0.10, color="gray", lw=0.9, ls=":", alpha=0.5,
               label="Carol innate (0.10)")
    if rho_cross_mean:
        ax.axvline(rho_cross_mean, color="#C62828", lw=1.3, ls="--", alpha=0.7)
        ax.text(rho_cross_mean + n_ep * 0.015, 0.28,
                f"rho crosses 0.20\nep {rho_cross_mean:.0f} +/- {rho_cross_std:.0f}",
                fontsize=8, color="#C62828")
    style(ax, ylabel="Observed reciprocity ratio", ylim=(0.0, 1.0),
          legend_loc="upper left")

    # ── (c) phi(Carol) ──────────────────────────────────────────────────────
    ax = axes[0, 2]
    ax.set_title("(c)  phi(Carol)  Exploitation Flag", fontsize=11, fontweight="bold")
    phi_arr = np.array([a["carol_phi"].values for a in adapts])
    phi_m = phi_arr.mean(0)
    phi_s = phi_arr.std(0)
    ax.plot(ep_a, phi_m, color="#C62828", lw=2.4,
            label="phi active (fraction of seeds)")
    ax.fill_between(ep_a, np.clip(phi_m - phi_s, 0, 1),
                    np.clip(phi_m + phi_s, 0, 1), color="#C62828", alpha=0.15)
    ax.axhline(0, color="black", lw=0.6, alpha=0.3)
    ax.axhline(1, color="black", lw=0.6, alpha=0.2, ls=":")
    if phi_off_mean:
        ax.axvspan(phi_off_mean - phi_off_std, phi_off_mean + phi_off_std,
                   color="#C62828", alpha=0.12)
        ax.axvline(phi_off_mean, color="#C62828", lw=1.4, ls="--", alpha=0.75)
        ax.text(phi_off_mean + n_ep * 0.015, 0.55,
                f"Last phi=1\nep {phi_off_mean:.0f} +/- {phi_off_std:.0f}",
                fontsize=8.5, color="#C62828")
    ax.set_ylabel("phi(Carol) — exploitation active", fontsize=10)
    style(ax, ylim=(-0.05, 1.15), legend_loc="upper right")

    # ── (d) Instantaneous decline_carol ─────────────────────────────────────
    ax = axes[1, 0]
    ax.set_title("(d)  Instantaneous Delta decline_carol per Episode",
                 fontsize=11, fontweight="bold")
    WINDOW = 30
    kernel = np.ones(WINDOW) / WINDOW
    inst_list = []
    for rr in regs:
        dc = rr["decline_carol"].values
        diff = np.diff(dc)
        smooth = np.convolve(diff, kernel, mode="valid")
        inst_list.append(smooth)
    inst_arr = np.array(inst_list)
    m_inst = inst_arr.mean(0)
    s_inst = inst_arr.std(0)
    ep_inst = ep_r[WINDOW:]

    ax.plot(ep_inst, m_inst, color="#C62828", lw=2.2,
            label=f"Delta decline_carol (smoothed w={WINDOW})")
    ax.fill_between(ep_inst, m_inst - s_inst, m_inst + s_inst,
                    color="#C62828", alpha=0.15)
    ax.axhline(0, color="black", lw=1.0, alpha=0.6)

    # mark sign change
    sign_change = None
    for i in range(1, len(m_inst)):
        if m_inst[i-1] > 0 and m_inst[i] <= 0:
            sign_change = ep_inst[i]; break
    if sign_change:
        ax.axvline(sign_change, color="gray", lw=1.1, ls="--", alpha=0.6)
        ax.text(sign_change + n_ep * 0.015,
                m_inst.max() * 0.6,
                f"sign change\nep {sign_change:.0f}",
                fontsize=8, color="gray")
    if phi_off_mean:
        ax.axvline(phi_off_mean, color="#C62828", lw=0.9, ls=":", alpha=0.5,
                   label=f"phi off (ep {phi_off_mean:.0f})")
    style(ax, ylabel="Delta decline_carol / episode", legend_loc="upper right")

    # ── (e) Cumulative decline_carol ─────────────────────────────────────────
    ax = axes[1, 1]
    title_zc = f"ep {zc_mean:.0f} +/- {zc_std:.0f}" if zc_mean else "> 2000 ep"
    ax.set_title(f"(e)  Cumulative decline_carol  ->  zero-crossing {title_zc}",
                 fontsize=11, fontweight="bold")
    dc_m, dc_s = ms(regs, "decline_carol")
    hc_m, hc_s = ms(regs, "help_carol")
    band(ax, ep_r, dc_m, dc_s, "#C62828", "decline_carol regret",
         lw=2.4, marker="s", every=200)
    band(ax, ep_r, hc_m, hc_s, "#1565C0", "help_carol regret",
         lw=2.0, marker="o", every=200)
    ax.axhline(0, color="black", lw=1.0, alpha=0.6)
    if zc_mean:
        ax.axvspan(zc_mean - zc_std, zc_mean + zc_std,
                   color="#C62828", alpha=0.12)
        ax.axvline(zc_mean, color="#C62828", lw=1.4, ls="--", alpha=0.75)
        y_label = min(dc_m.min() * 0.5, -200)
        ax.text(zc_mean + n_ep * 0.015, y_label,
                f"Social reversal\nep {zc_mean:.0f} +/- {zc_std:.0f}",
                fontsize=8.5, color="#C62828")
    if phi_off_mean:
        ax.axvline(phi_off_mean, color="gray", lw=0.9, ls=":", alpha=0.5,
                   label=f"phi off (ep {phi_off_mean:.0f})")
    style(ax, ylabel="Cumulative regret (Alice -> Carol)", legend_loc="upper left")

    # ── hide unused panel ────────────────────────────────────────────────────
    axes[1, 2].set_visible(False)

    os.makedirs("results", exist_ok=True)
    plt.savefig(OUT, dpi=200, bbox_inches="tight")
    print(f"Saved: {OUT}")
    plt.close()

    print(f"\n=== Standard CFR reversal stats ({n_seeds} seeds, {n_ep} ep) ===")
    if phi_off_mean:
        print(f"  phi last active:           ep {phi_off_mean:.0f} +/- {phi_off_std:.0f}")
    if rho_cross_mean:
        print(f"  rho crosses 0.20:          ep {rho_cross_mean:.0f} +/- {rho_cross_std:.0f}")
    if zc_mean:
        print(f"  decline_carol zero-cross:  ep {zc_mean:.0f} +/- {zc_std:.0f}")
    else:
        print(f"  decline_carol still positive at ep {n_ep}: {dc_m[-1]:.0f}")
    print(f"  Carol rho_observed at ep{n_ep}: {ms(adapts, 'carol_observed_ratio')[0][-1]:.4f}")
    print(f"  Carol adapted recip at ep{n_ep}: {ms(adapts, 'carol_adapted')[0][-1]:.4f}")


if __name__ == "__main__":
    main()
