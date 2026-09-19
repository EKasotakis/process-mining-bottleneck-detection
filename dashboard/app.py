import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st



PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

sys.path.append(str(SRC_PATH))

from database import read_event_log
from transform import validate_event_log, prepare_event_log
from kpis import case_lead_times, waiting_time_by_activity
from process_analysis import detect_rework_cases, detect_ping_pong_cases
from alerts import create_case_alerts
from process_flow import build_process_flow, classify_transitions, create_process_sankey


st.set_page_config(
    page_title="Process Mining & Bottleneck Detection",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_data():
    df = read_event_log()

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    validate_event_log(df)

    return prepare_event_log(df)


df = load_data()

st.sidebar.header("Filters")

priority_options = sorted(
    df["priority"].unique().tolist()
)

selected_priorities = st.sidebar.multiselect(
    "Priority",
    options=priority_options,
    default=priority_options,
)

filtered_df = df[
    df["priority"].isin(selected_priorities)
].copy()

if filtered_df.empty:
    st.warning("Select at least one priority.")
    st.stop()


case_options = sorted(
    filtered_df["case_id"].unique().tolist()
)

selected_case = st.sidebar.selectbox(
    "Inspect Case",
    options=["None"] + case_options,
)


st.title("Process Mining & Bottleneck Detection")

st.caption(
    "Operational analysis of a synthetic customer quality-claim process."
)

lead_times = case_lead_times(filtered_df)
rework = detect_rework_cases(filtered_df)
ping_pong = detect_ping_pong_cases(filtered_df)
alerts = create_case_alerts(filtered_df)

total_cases = filtered_df["case_id"].nunique()

avg_lead_time = lead_times["lead_time_hours"].mean()

rework_rate = len(rework) / total_cases * 100

ping_pong_rate = len(ping_pong) / total_cases * 100

flagged_cases = alerts["alert"].sum()



col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Total Cases",
    f"{total_cases:,}",
)

col2.metric(
    "Avg Lead Time",
    f"{avg_lead_time:.1f} h",
)

col3.metric(
    "Rework Rate",
    f"{rework_rate:.1f}%",
)

col4.metric(
    "Ping-Pong Rate",
    f"{ping_pong_rate:.1f}%",
)

col5.metric(
    "Flagged Cases",
    f"{flagged_cases}",
)


st.header("As-Is Process Flow")

process_flow = build_process_flow(filtered_df)
process_flow = classify_transitions(process_flow)

process_fig = create_process_sankey(process_flow)

with st.expander("View Process Transitions"):
    st.dataframe(
        process_flow[
            [
                "previous_activity",
                "activity",
                "transition_count",
                "transition_percentage",
                "avg_wait_hours",
                "flow_type",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.plotly_chart(
    process_fig,
    use_container_width=True,
)


st.header("Process Bottlenecks")

waiting_summary = (
    waiting_time_by_activity(filtered_df)
    .reset_index()
)

waiting_summary = waiting_summary[
    waiting_summary["activity"] != "Claim Received"
]


fig_waiting = px.bar(
    waiting_summary,
    x="activity",
    y="mean",
    labels={
        "activity": "Activity",
        "mean": "Average Waiting Time (Hours)",
    },
    title="Average Waiting Time by Activity",
)

fig_waiting.update_layout(
    xaxis_tickangle=-35
)

st.plotly_chart(
    fig_waiting,
    use_container_width=True,
)

st.info(
    "Request Additional Information has the longest elapsed waiting "
    "time, but largely represents external customer dependency. "
    "Quality Review is the largest internal process bottleneck."
)

st.header("Case Lead Time")

fig_lead_time = px.histogram(
    lead_times,
    x="lead_time_hours",
    nbins=30,
    labels={
        "lead_time_hours": "Lead Time (Hours)",
    },
    title="Distribution of Case Lead Times",
)

st.plotly_chart(
    fig_lead_time,
    use_container_width=True,
)


rework_case_ids = set(rework["case_id"])

lead_times["process_type"] = lead_times["case_id"].apply(
    lambda case_id: (
        "Rework"
        if case_id in rework_case_ids
        else "No Rework"
    )
)


rework_comparison = (
    lead_times.groupby("process_type")["lead_time_hours"]
    .mean()
    .reset_index()
)


fig_rework = px.bar(
    rework_comparison,
    x="process_type",
    y="lead_time_hours",
    labels={
        "process_type": "Case Type",
        "lead_time_hours": "Average Lead Time (Hours)",
    },
    title="Impact of Rework on Lead Time",
)

st.plotly_chart(
    fig_rework,
    use_container_width=True,
)


no_rework_mean = rework_comparison.loc[
    rework_comparison["process_type"] == "No Rework",
    "lead_time_hours",
].iloc[0]

rework_mean = rework_comparison.loc[
    rework_comparison["process_type"] == "Rework",
    "lead_time_hours",
].iloc[0]

rework_increase = (
    (rework_mean - no_rework_mean)
    / no_rework_mean
    * 100
)

st.warning(
    f"Cases involving Technical–Quality rework take "
    f"{rework_increase:.0f}% longer on average."
)


st.header("Cases Requiring Attention")

flagged = alerts[
    alerts["alert"]
].copy()

flagged = flagged.sort_values(
    "lead_time_hours",
    ascending=False,
)


st.dataframe(
    flagged[
        [
            "case_id",
            "priority",
            "lead_time_hours",
            "slow_case",
            "ping_pong",
            "excessive_wait",
            "alert_reason",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)


if selected_case != "None":
    st.header(f"Case Explorer — {selected_case}")

    case_events = filtered_df[
        filtered_df["case_id"] == selected_case
    ].copy()

    st.dataframe(
        case_events[
            [
                "activity",
                "timestamp",
                "team",
                "waiting_time_hours",
                "priority",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )