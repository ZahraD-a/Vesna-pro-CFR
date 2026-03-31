import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit as st

# Page config
st.set_page_config(page_title="CFR Regret Visualization", layout="wide")

st.title("VEsNA-Pro CFR: Counterfactual Regret Minimization Analysis")

# Strategy info
STRATEGIES = {
    "try_new_shop": {"name": "Try New Shop", "color": "#EF553B", "success_rate": 0.6},
    "go_regular_shop": {"name": "Regular Shop", "color": "#00CC96", "success_rate": 0.85},
    "make_at_home": {"name": "Make at Home", "color": "#636EFA", "success_rate": 0.95}
}

def load_data():
    """Load CFR regret and personality evolution data."""
    try:
        regrets_df = pd.read_csv("cfr_regrets.csv")
        personality_df = pd.read_csv("personality_evolution.csv")
        return regrets_df, personality_df
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}")
        st.info("Run the CFR simulation first to generate data files.")
        return None, None

def compute_implied_strategy(row):
    """Compute implied strategy probabilities from regrets using regret matching."""
    regrets = [
        max(0, row["try_new_shop"]),
        max(0, row["go_regular_shop"]),
        max(0, row["make_at_home"])
    ]
    total = sum(regrets)

    if total < 0.001:
        return {k: 1.0/3 for k in STRATEGIES.keys()}

    return {
        "try_new_shop": regrets[0] / total,
        "go_regular_shop": regrets[1] / total,
        "make_at_home": regrets[2] / total
    }

def main():
    regrets_df, personality_df = load_data()

    if regrets_df is None or personality_df is None:
        return

    # Sidebar controls
    st.sidebar.header("Controls")

    # Episode range selector
    max_ep = regrets_df["episode"].max()
    ep_range = st.sidebar.slider(
        "Episode Range",
        min_value=0,
        max_value=int(max_ep),
        value=(0, int(max_ep))
    )

    # Filter data
    regrets_filtered = regrets_df[
        (regrets_df["episode"] >= ep_range[0]) &
        (regrets_df["episode"] <= ep_range[1])
    ]
    personality_filtered = personality_df[
        (personality_df["episode"] >= ep_range[0]) &
        (personality_df["episode"] <= ep_range[1])
    ]

    # Metrics at top
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Episodes", int(max_ep))
    with col2:
        final_ep = personality_filtered.iloc[-1]
        st.metric("Final Cautious", f"{final_ep['cautious']:.3f}")
    with col3:
        st.metric("Final Bold", f"{final_ep['bold']:.3f}")

    # Tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Regret Evolution", "Implied Strategy", "Personality Traits", "Summary"])

    with tab1:
        st.header("Cumulative Regrets Over Time")

        fig = go.Figure()

        for key, info in STRATEGIES.items():
            fig.add_trace(go.Scatter(
                x=regrets_filtered["episode"],
                y=regrets_filtered[key],
                mode='lines',
                name=info["name"],
                line=dict(color=info["color"], width=2)
            ))

        fig.update_layout(
            title="Cumulative Counterfactual Regrets",
            xaxis_title="Episode",
            yaxis_title="Cumulative Regret",
            hovermode="x unified",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info("""
        **Interpretation**: Higher regret means the agent regrets NOT taking that action more.
        Positive regrets indicate actions that would have performed better than what was chosen.
        The CFR algorithm uses these regrets to update the strategy toward optimal play.
        """)

    with tab2:
        st.header("Implied Strategy from Regrets")

        # Compute implied strategy for each episode
        implied_probs = []
        for _, row in regrets_filtered.iterrows():
            probs = compute_implied_strategy(row)
            implied_probs.append(probs)

        implied_df = pd.DataFrame(implied_probs)
        implied_df["episode"] = regrets_filtered["episode"].values

        fig = go.Figure()

        for key, info in STRATEGIES.items():
            fig.add_trace(go.Scatter(
                x=implied_df["episode"],
                y=implied_df[key] * 100,
                mode='lines',
                name=info["name"],
                line=dict(color=info["color"], width=2),
                fill='tozeroy' if key == "make_at_home" else None
            ))

        # Add reference line for optimal (should converge to make_at_home ~95%)
        fig.add_hline(
            y=95,
            line_dash="dash",
            line_color="gray",
            annotation_text="Expected Optimal (95%)"
        )

        fig.update_layout(
            title="Implied Strategy Probabilities (Regret Matching)",
            xaxis_title="Episode",
            yaxis_title="Probability (%)",
            hovermode="x unified",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info("""
        **Interpretation**: The CFR algorithm computes strategy probabilities as:
        σ(a) = [R(a)]+ / Σ[R(a')]+

        Where [R(a)]+ = max(0, R(a)) is the positive regret for action a.
        As training progresses, this should converge to the optimal strategy.
        """)

    with tab3:
        st.header("Personality Evolution")

        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=["Cautious", "Bold", "Curious"]
        )

        traits = ["cautious", "bold", "curious"]
        colors = ["#636EFA", "#EF553B", "#00CC96"]

        for i, (trait, color) in enumerate(zip(traits, colors), 1):
            fig.add_trace(go.Scatter(
                x=personality_filtered["episode"],
                y=personality_filtered[trait],
                mode='lines',
                name=trait.capitalize(),
                line=dict(color=color, width=2),
                showlegend=False
            ), row=1, col=i)

            # Add expected convergence line for cautious (should go high)
            if trait == "cautious":
                fig.add_hline(
                    y=0.8,
                    line_dash="dash",
                    line_color="gray",
                    row=1, col=i
                )

        fig.update_layout(
            title="Personality Traits Over Training",
            height=400,
            showlegend=False
        )

        for i in range(1, 4):
            fig.update_yaxes(range=[0, 1], row=1, col=i)
            fig.update_xaxes(title_text="Episode", row=1, col=i)

        st.plotly_chart(fig, use_container_width=True)

        # Correlation with success rates
        st.subheader("Trait-Success Correlation")
        st.write("""
        The CFR learning should discover that:
        - **Cautious** trait correlates with higher success (make_at_home: 95%)
        - **Bold** trait correlates with lower success (try_new_shop: 60%)
        - **Curious** has mixed effects

        Therefore, cautious should increase while bold decreases over training.
        """)

    with tab4:
        st.header("Training Summary")

        # Final regrets
        st.subheader("Final Cumulative Regrets")
        final_regrets = regrets_filtered.iloc[-1]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                STRATEGIES["try_new_shop"]["name"],
                f"{final_regrets['try_new_shop']:.2f}",
                help="Low expected reward (60%)"
            )
        with col2:
            st.metric(
                STRATEGIES["go_regular_shop"]["name"],
                f"{final_regrets['go_regular_shop']:.2f}",
                help="Medium expected reward (85%)"
            )
        with col3:
            st.metric(
                STRATEGIES["make_at_home"]["name"],
                f"{final_regrets['make_at_home']:.2f}",
                help="High expected reward (95%)"
            )

        # Final implied strategy
        st.subheader("Final Implied Strategy")
        final_probs = compute_implied_strategy(final_regrets)

        for key, prob in final_probs.items():
            st.metric(
                STRATEGIES[key]["name"],
                f"{prob*100:.1f}%",
                delta=f"vs {STRATEGIES[key]['success_rate']*100:.0f}% optimal"
            )

        # Convergence check
        st.subheader("Convergence Analysis")

        # Check if regrets have stabilized
        last_10 = regrets_filtered.tail(10)
        try_new_var = last_10["try_new_shop"].std()
        make_var = last_10["make_at_home"].std()

        if try_new_var < 0.1 and make_var < 0.1:
            st.success("✓ Regrets appear to have converged (low variance in last 10 episodes)")
        else:
            st.warning("⚠ Regrets still changing - may need more training")

        # Personality drift
        st.subheader("Personality Change")
        first_pers = personality_filtered.iloc[0]
        last_pers = personality_filtered.iloc[-1]

        pers_col1, pers_col2, pers_col3 = st.columns(3)
        with pers_col1:
            delta_cautious = last_pers["cautious"] - first_pers["cautious"]
            st.metric("Cautious Δ", f"{delta_cautious:+.3f}")
        with pers_col2:
            delta_bold = last_pers["bold"] - first_pers["bold"]
            st.metric("Bold Δ", f"{delta_bold:+.3f}")
        with pers_col3:
            delta_curious = last_pers["curious"] - first_pers["curious"]
            st.metric("Curious Δ", f"{delta_curious:+.3f}")

        # Download buttons
        st.subheader("Download Data")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download Regrets CSV",
                regrets_filtered.to_csv(index=False),
                "cfr_regrets.csv",
                "text/csv"
            )
        with col2:
            st.download_button(
                "Download Personality CSV",
                personality_filtered.to_csv(index=False),
                "personality_evolution.csv",
                "text/csv"
            )

if __name__ == "__main__":
    main()
