from __future__ import annotations

import pandas as pd
import streamlit as st

from analysis import (
    build_report,
    default_data_path,
    demo_data,
    load_data,
    minimum_sample_size,
    segment_performance,
    two_proportion_test,
)
from storage import list_runs, save_run


st.set_page_config(page_title="Growth Experiment Builder", page_icon="↗", layout="wide")
st.markdown(
    """
    <style>
    .block-container {max-width: 1220px; padding-top: 2rem;}
    [data-testid="stMetric"] {background:#f7f7f5; border:1px solid #e5e5df; padding:16px; border-radius:14px;}
    .eyebrow {font-size:.78rem; letter-spacing:.12em; color:#70706c; text-transform:uppercase; font-weight:700;}
    .decision {padding:18px 20px; border-radius:14px; background:#fff3ef; border-left:5px solid #ff2442;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="eyebrow">AI-native portfolio prototype</div>', unsafe_allow_html=True)
st.title("Growth Experiment Builder")
st.caption("From ambiguous growth question → testable hypothesis → statistical decision → reusable experiment review")

with st.sidebar:
    st.header("Experiment setup")
    experiment_name = st.text_input("Experiment name", "Paid exposure conversion test")
    hypothesis = st.text_area(
        "Hypothesis",
        "Showing the campaign ad increases conversion compared with the PSA control.",
    )
    alpha = st.select_slider("Significance level α", [0.01, 0.05, 0.10], value=0.05)
    uploaded = st.file_uploader("Optional: upload compatible CSV", type=["csv"])
    st.caption("No upload needed for the synthetic demo. Upload the Kaggle CSV to reproduce the portfolio analysis.")


@st.cache_data(show_spinner=False)
def get_data(source):
    return load_data(source)


try:
    if uploaded is not None:
        df = get_data(uploaded)
        data_label = "Uploaded dataset"
    elif default_data_path().exists():
        df = get_data(default_data_path())
        data_label = "Local Kaggle dataset"
    else:
        df = demo_data()
        data_label = "Synthetic demo dataset"
except Exception as exc:
    st.error(f"Could not load data: {exc}")
    st.stop()

groups = df["test group"].value_counts()
if not {"ad", "psa"}.issubset(groups.index):
    st.error("This prototype expects `ad` and `psa` in the test group column.")
    st.stop()

result = two_proportion_test(df, alpha=alpha)

tab1, tab2, tab3, tab4 = st.tabs(["Decision", "Segments", "Plan next test", "Experiment log"])

with tab1:
    st.subheader("Executive decision")
    cols = st.columns(5)
    cols[0].metric("Users", f"{len(df):,}", help=data_label)
    cols[1].metric("Treatment CVR", f"{result.treatment_rate:.2%}")
    cols[2].metric("Control CVR", f"{result.control_rate:.2%}")
    cols[3].metric("Relative lift", f"{result.relative_lift:+.2%}")
    cols[4].metric("p-value", f"{result.p_value:.4g}")

    rollout = result.significant and result.absolute_lift > 0
    headline = "Evidence supports further rollout evaluation" if rollout else "Evidence is insufficient for rollout"
    st.markdown(
        f'<div class="decision"><strong>{headline}</strong><br>'
        f'Estimated absolute lift: {result.absolute_lift:+.2%}; '
        f'95% CI [{result.ci_low:+.2%}, {result.ci_high:+.2%}].</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("#### Conversion comparison")
        chart = pd.DataFrame(
            {"Group": ["Treatment · ad", "Control · PSA"], "Conversion rate": [result.treatment_rate, result.control_rate]}
        ).set_index("Group")
        st.bar_chart(chart, color="#ff2442", horizontal=True)
    with right:
        st.markdown("#### Statistical interpretation")
        st.write(
            "The two-proportion z-test evaluates whether the observed conversion difference is larger than expected from sampling variation."
        )
        st.progress(min(float(abs(result.relative_lift)), 1.0), text=f"Observed relative lift: {result.relative_lift:+.2%}")
        st.caption("Statistical significance is not the same as business significance; validate cost and experience guardrails before scaling.")

    decision_rule = f"Two-sided α={alpha:.0%}; consider rollout only when p < α, lift is positive, and guardrail metrics remain acceptable."
    report = build_report(result, hypothesis, decision_rule)
    b1, b2 = st.columns([1, 4])
    if b1.button("Save run", type="primary"):
        save_run(experiment_name, hypothesis, result.as_dict())
        st.success("Experiment run saved to SQLite.")
    b2.download_button("Download Markdown review", report, file_name="experiment_review.md", mime="text/markdown")

with tab2:
    st.subheader("Exploratory segment diagnostics")
    st.warning("Segment cuts are exploratory unless defined before the experiment. Use them to form new hypotheses—not to manufacture significance.")
    dimension_label = st.radio("Analyze by", ["Exposure band", "Day of week", "Hour of day"], horizontal=True)
    dim_map = {"Exposure band": "exposure band", "Day of week": "most ads day", "Hour of day": "most ads hour"}
    segment = segment_performance(df, dim_map[dimension_label])
    pivot = segment.pivot(index=dim_map[dimension_label], columns="test group", values="conversion_rate")
    if dimension_label == "Day of week":
        order = [d for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] if d in pivot.index]
        pivot = pivot.reindex(order)
    st.line_chart(pivot, color=["#ff2442", "#4b5563"])
    display = segment.copy()
    display["conversion_rate"] = display["conversion_rate"].map(lambda x: f"{x:.2%}")
    display["absolute_lift"] = display["absolute_lift"].map(lambda x: f"{x:+.2%}" if pd.notna(x) else "—")
    st.dataframe(display, width="stretch", hide_index=True)

with tab3:
    st.subheader("Turn the next idea into a testable plan")
    c1, c2 = st.columns(2)
    baseline = c1.number_input("Baseline conversion", min_value=0.001, max_value=0.9, value=float(result.control_rate), format="%.4f")
    relative_mde = c2.slider("Minimum detectable relative lift", 0.05, 1.0, 0.15, 0.05)
    power = c1.slider("Statistical power", 0.70, 0.95, 0.80, 0.05)
    next_metric = c2.text_input("Primary metric", "Conversion rate")
    sample = minimum_sample_size(baseline, relative_mde, alpha=alpha, power=power)
    st.metric("Recommended sample per group", f"{sample:,}", help="Normal approximation for two independent proportions.")

    st.markdown("#### Experiment card")
    st.markdown(
        f"""
        - **Problem:** Conversion opportunity identified in the current journey.
        - **Hypothesis:** {hypothesis}
        - **Primary metric:** {next_metric}
        - **Target effect:** {relative_mde:.0%} relative improvement over a {baseline:.2%} baseline
        - **Sample:** at least {sample:,} users per group at {power:.0%} power and α={alpha:.0%}
        - **Guardrails:** complaint rate, cost per conversion, negative feedback, latency
        - **Stop rule:** do not stop early based only on a favorable interim p-value
        """
    )

with tab4:
    st.subheader("Saved experiment decisions")
    history = list_runs()
    if history:
        history_df = pd.DataFrame(history)
        keep = [c for c in ["id", "created_at", "experiment_name", "treatment_rate", "control_rate", "relative_lift", "p_value", "significant"] if c in history_df]
        st.dataframe(history_df[keep], width="stretch", hide_index=True)
    else:
        st.info("No runs saved yet. Save the current analysis from the Decision tab.")

st.divider()
st.caption(f"Portfolio project · {data_label} · Not affiliated with RED or any employer")
