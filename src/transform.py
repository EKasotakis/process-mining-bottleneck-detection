import pandas as pd


def load_event_log(filepath):
    df = pd.read_csv(filepath)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df



REQUIRED_COLUMNS = [
    "case_id",
    "activity",
    "timestamp",
    "team",
    "status",
    "priority",
]


def validate_event_log(df):
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Event log contains missing values")

    return True


def prepare_event_log(df):
    df = df.copy()

    df = df.sort_values(
        by=["case_id", "timestamp"]
    ).reset_index(drop=True)

    df["previous_timestamp"] = (
        df.groupby("case_id")["timestamp"].shift(1)
    )

    df["waiting_time_hours"] = (
        df["timestamp"] - df["previous_timestamp"]
    ).dt.total_seconds() / 3600

    df["previous_activity"] = (
    df.groupby("case_id")["activity"].shift(1)
)

    df["previous_team"] = (
        df.groupby("case_id")["team"].shift(1)
    )
    return df



if __name__ == "__main__":
    df = load_event_log("data/raw/event_log.csv")

    validate_event_log(df)

    df = prepare_event_log(df)

    print(df.head(15))

    print("\nWaiting time summary:")
    print(df["waiting_time_hours"].describe())