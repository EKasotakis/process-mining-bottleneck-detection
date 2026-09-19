import pandas as pd

from transform import load_event_log, validate_event_log, prepare_event_log
import plotly.graph_objects as go


REWORK_TRANSITIONS = {
    ("Quality Review", "Technical Assessment"),
    ("Request Additional Information", "Initial Review"),
}


def build_process_flow(df):
    transitions = df[
        df["previous_activity"].notna()
    ].copy()

    flow = (
        transitions
        .groupby(
            ["previous_activity", "activity"]
        )
        .agg(
            transition_count=("case_id", "count"),
            cases=("case_id", "nunique"),
            avg_wait_hours=("waiting_time_hours", "mean"),
            median_wait_hours=("waiting_time_hours", "median"),
        )
        .reset_index()
    )

    flow = flow.sort_values(
        "transition_count",
        ascending=False,
    )

    outgoing_totals = (
    flow.groupby("previous_activity")["transition_count"]
    .transform("sum")
    )

    flow["transition_percentage"] = (
        flow["transition_count"]
        / outgoing_totals
        * 100
    )

    return flow


def classify_transitions(flow):
    flow = flow.copy()

    flow["flow_type"] = flow.apply(
        lambda row: (
            "Rework / Return"
            if (
                row["previous_activity"],
                row["activity"],
            ) in REWORK_TRANSITIONS
            else "Forward"
        ),
        axis=1,
    )

    return flow


def create_process_sankey(flow):
    activities = sorted(
        set(flow["previous_activity"])
        | set(flow["activity"])
    )

    activity_index = {
        activity: i
        for i, activity in enumerate(activities)
    }

    sources = [
        activity_index[activity]
        for activity in flow["previous_activity"]
    ]

    targets = [
        activity_index[activity]
        for activity in flow["activity"]
    ]

    values = flow["transition_count"].tolist()

    fig = go.Figure(
        go.Sankey(
            node=dict(
                label=activities,
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
            ),
        )
    )

    fig.update_layout(
        title="As-Is Process Flow",
        font_size=12,
    )

    return fig


if __name__ == "__main__":
    df = load_event_log("data/raw/event_log.csv")

    validate_event_log(df)
    df = prepare_event_log(df)

    flow = build_process_flow(df)

    REWORK_TRANSITIONS = {
    ("Quality Review", "Technical Assessment"),
    ("Request Additional Information", "Initial Review"),
    }

    flow = classify_transitions(flow)

    flow.to_csv(
    "data/processed/process_flow.csv",
    index=False,
    )

    fig = create_process_sankey(flow)

    fig.show()

    print("\nActual process transitions:")
    print(flow.to_string(index=False))