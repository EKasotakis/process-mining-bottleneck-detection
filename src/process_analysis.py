import pandas as pd

from transform import load_event_log, validate_event_log, prepare_event_log


def activity_repetitions(df):
    repetitions = (
        df.groupby(["case_id", "activity"])
        .size()
        .reset_index(name="activity_count")
    )

    repetitions = repetitions[
        repetitions["activity_count"] > 1
    ]

    return repetitions


def get_transitions(df):
    transitions = df[
        df["previous_activity"].notna()
    ].copy()

    transitions["transition"] = (
        transitions["previous_activity"]
        + " → "
        + transitions["activity"]
    )

    return transitions


def detect_rework_cases(df):
    transitions = get_transitions(df)

    rework = transitions[
        (transitions["previous_activity"] == "Quality Review")
        & (transitions["activity"] == "Technical Assessment")
    ]

    rework_summary = (
        rework.groupby("case_id")
        .size()
        .reset_index(name="rework_count")
    )

    return rework_summary


def detect_ping_pong_cases(df):
    rework = detect_rework_cases(df)

    ping_pong = rework[
        rework["rework_count"] >= 2
    ].copy()

    return ping_pong


def compare_rework_lead_time(df):
    case_summary = (
        df.groupby("case_id")
        .agg(
            start_time=("timestamp", "min"),
            end_time=("timestamp", "max"),
        )
        .reset_index()
    )

    case_summary["lead_time_hours"] = (
        case_summary["end_time"]
        - case_summary["start_time"]
    ).dt.total_seconds() / 3600

    rework_cases = set(
        detect_rework_cases(df)["case_id"]
    )

    case_summary["has_rework"] = (
        case_summary["case_id"].isin(rework_cases)
    )

    return (
        case_summary.groupby("has_rework")["lead_time_hours"]
        .agg(["count", "mean", "median"])
    )


if __name__ == "__main__":
    df = load_event_log("data/raw/event_log.csv")

    validate_event_log(df)
    df = prepare_event_log(df)

    repetitions = activity_repetitions(df)
    transitions = get_transitions(df)
    rework = detect_rework_cases(df)
    ping_pong = detect_ping_pong_cases(df)

    print(f"\nPing-pong cases: {len(ping_pong)}")
    print(
        f"Ping-pong rate: "
        f"{len(ping_pong) / df['case_id'].nunique() * 100:.1f}%"
    )

    print("\nRework cases:")
    print(rework.head(20))

    print(f"\nCases with technical rework: {len(rework)}")
    print(
        f"Rework rate: "
        f"{len(rework) / df['case_id'].nunique() * 100:.1f}%"
    )

    print("\nMost common transitions:")
    print(
        transitions["transition"]
        .value_counts()
        .head(15)
    )
    print("\nRepeated activities:")
    print(repetitions.head(20))

    print("\nLead time: rework vs no rework:")
    print(compare_rework_lead_time(df))