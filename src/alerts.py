import pandas as pd

from transform import load_event_log, validate_event_log, prepare_event_log
from process_analysis import detect_rework_cases, detect_ping_pong_cases


LEAD_TIME_THRESHOLD_HOURS = 120
WAIT_TIME_THRESHOLD_HOURS = 48


def detect_slow_cases(df):
    cases = (
        df.groupby("case_id")
        .agg(
            start_time=("timestamp", "min"),
            end_time=("timestamp", "max"),
            priority=("priority", "first"),
        )
        .reset_index()
    )

    cases["lead_time_hours"] = (
        cases["end_time"] - cases["start_time"]
    ).dt.total_seconds() / 3600

    cases["slow_case"] = (
        cases["lead_time_hours"] > LEAD_TIME_THRESHOLD_HOURS
    )

    return cases


def detect_excessive_waits(df):
    excessive_waits = df[
        df["waiting_time_hours"] > WAIT_TIME_THRESHOLD_HOURS
    ].copy()

    return excessive_waits[
        [
            "case_id",
            "previous_activity",
            "activity",
            "previous_team",
            "team",
            "waiting_time_hours",
            "priority",
        ]
    ]


def create_case_alerts(df):
    cases = detect_slow_cases(df)

    rework_cases = set(
        detect_rework_cases(df)["case_id"]
    )

    ping_pong_cases = set(
        detect_ping_pong_cases(df)["case_id"]
    )

    excessive_wait_cases = set(
        detect_excessive_waits(df)["case_id"]
    )

    cases["has_rework"] = cases["case_id"].isin(rework_cases)

    cases["ping_pong"] = cases["case_id"].isin(ping_pong_cases)

    cases["excessive_wait"] = cases["case_id"].isin(
        excessive_wait_cases
    )

    cases["alert"] = (
        cases["slow_case"]
        | cases["ping_pong"]
        | cases["excessive_wait"]
    )
    cases["alert_reason"] = cases.apply(
    add_alert_reason,
    axis=1,
    )

    return cases


def add_alert_reason(row):
    reasons = []

    if row["slow_case"]:
        reasons.append("Lead time exceeded threshold")

    if row["ping_pong"]:
        reasons.append("Repeated Technical-Quality rework")

    if row["excessive_wait"]:
        reasons.append("Excessive stage waiting time")

    return "; ".join(reasons)


def detect_lead_time_outliers(cases):
    q1 = cases["lead_time_hours"].quantile(0.25)
    q3 = cases["lead_time_hours"].quantile(0.75)

    iqr = q3 - q1

    upper_bound = q3 + 1.5 * iqr

    outliers = cases[
        cases["lead_time_hours"] > upper_bound
    ].copy()

    return outliers, upper_bound


if __name__ == "__main__":
    df = load_event_log("data/raw/event_log.csv")

    validate_event_log(df)
    df = prepare_event_log(df)

    alerts = create_case_alerts(df)

    flagged = alerts[alerts["alert"]]

    print(f"\nTotal cases: {len(alerts)}")
    print(f"Flagged cases: {len(flagged)}")
    print(
        f"Alert rate: "
        f"{len(flagged) / len(alerts) * 100:.1f}%"
    )

    print("\nAlert reasons:")
    print(flagged["alert_reason"].value_counts())

    print("\nSlowest flagged cases:")
    print(
        flagged.sort_values(
            "lead_time_hours",
            ascending=False,
        ).head(10)
    )
    outliers, upper_bound = detect_lead_time_outliers(alerts)

    print(
        f"\nStatistical lead-time outlier threshold: "
        f"{upper_bound:.1f} hours"
    )

    print(f"Statistical outliers: {len(outliers)}")