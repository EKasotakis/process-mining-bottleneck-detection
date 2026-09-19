import pandas as pd

from transform import load_event_log, validate_event_log, prepare_event_log


def waiting_time_by_activity(df):
    summary = (
        df.groupby("activity")["waiting_time_hours"]
        .agg(["count", "mean", "median", "max"])
        .sort_values("mean", ascending=False)
    )

    return summary


def case_lead_times(df):
    lead_times = (
        df.groupby("case_id")
        .agg(
            start_time=("timestamp", "min"),
            end_time=("timestamp", "max"),
            priority=("priority", "first"),
        )
        .reset_index()
    )

    lead_times["lead_time_hours"] = (
        lead_times["end_time"] - lead_times["start_time"]
    ).dt.total_seconds() / 3600

    return lead_times


def lead_time_by_priority(lead_times):
    return (
        lead_times.groupby("priority")["lead_time_hours"]
        .agg(["count", "mean", "median"])
        .sort_values("mean")
    )


def events_by_team(df):
    return (
        df.groupby("team")
        .agg(
            events=("activity", "count"),
            cases=("case_id", "nunique"),
        )
        .sort_values("events", ascending=False)
    )



if __name__ == "__main__":
    df = load_event_log("data/raw/event_log.csv")

    validate_event_log(df)
    df = prepare_event_log(df)

    print("\nWaiting time by activity:")
    print(waiting_time_by_activity(df))

    lead_times = case_lead_times(df)

    print("\nCase lead time summary:")
    print(lead_times["lead_time_hours"].describe())

    print("\nLead time by priority:")
    print(lead_time_by_priority(lead_times))

    print("\nEvents handled by team:")
    print(events_by_team(df))