from transform import load_event_log, validate_event_log, prepare_event_log
from process_analysis import compare_rework_lead_time


QUALITY_WAIT_REDUCTION = 0.25
REWORK_REDUCTION = 0.50


def calculate_improvement_scenario(df):
    baseline_lead_time = (
        df.groupby("case_id")
        .agg(
            start_time=("timestamp", "min"),
            end_time=("timestamp", "max"),
        )
    )

    baseline_lead_time["lead_time_hours"] = (
        baseline_lead_time["end_time"]
        - baseline_lead_time["start_time"]
    ).dt.total_seconds() / 3600

    baseline_average = baseline_lead_time[
        "lead_time_hours"
    ].mean()

    quality_events = df[
        df["activity"] == "Quality Review"
    ]

    avg_quality_wait = quality_events[
        "waiting_time_hours"
    ].mean()

    quality_saving_per_review = (
        avg_quality_wait
        * QUALITY_WAIT_REDUCTION
    )

    rework_comparison = compare_rework_lead_time(df)

    return {
        "baseline_average_lead_time": baseline_average,
        "avg_quality_wait": avg_quality_wait,
        "quality_saving_per_review": quality_saving_per_review,
        "rework_comparison": rework_comparison,
    }


def simulate_quality_improvement(df):
    simulated = df.copy()

    quality_mask = (
        simulated["activity"] == "Quality Review"
    )

    simulated.loc[
        quality_mask,
        "quality_wait_saving"
    ] = (
        simulated.loc[
            quality_mask,
            "waiting_time_hours"
        ]
        * QUALITY_WAIT_REDUCTION
    )

    simulated["quality_wait_saving"] = (
        simulated["quality_wait_saving"]
        .fillna(0)
    )

    return simulated


def calculate_rework_loop_cost(df):
    rework_returns = df[
        (df["previous_activity"] == "Quality Review")
        & (df["activity"] == "Technical Assessment")
    ].copy()

    return rework_returns["waiting_time_hours"].mean()


def simulate_to_be(df):
    simulated = simulate_quality_improvement(df)

    case_savings = (
        simulated.groupby("case_id")
        .agg(
            quality_wait_saving=(
                "quality_wait_saving",
                "sum",
            ),
        )
        .reset_index()
    )

    case_times = (
        df.groupby("case_id")
        .agg(
            start_time=("timestamp", "min"),
            end_time=("timestamp", "max"),
        )
        .reset_index()
    )

    case_times["as_is_lead_time"] = (
        case_times["end_time"]
        - case_times["start_time"]
    ).dt.total_seconds() / 3600

    rework_mask = (
        (df["previous_activity"] == "Quality Review")
        & (df["activity"] == "Technical Assessment")
    )

    rework_counts = (
        df[rework_mask]
        .groupby("case_id")
        .size()
        .rename("rework_count")
        .reset_index()
    )

    case_savings = case_savings.merge(
        rework_counts,
        on="case_id",
        how="left",
    )

    case_savings["rework_count"] = (
        case_savings["rework_count"]
        .fillna(0)
    )

    rework_loop_cost = calculate_rework_loop_cost(df)

    case_savings["expected_rework_saving"] = (
        case_savings["rework_count"]
        * REWORK_REDUCTION
        * rework_loop_cost
    )

    results = case_times.merge(
        case_savings,
        on="case_id",
        how="left",
    )

    results["total_saving"] = (
        results["quality_wait_saving"]
        + results["expected_rework_saving"]
    )

    results["to_be_lead_time"] = (
        results["as_is_lead_time"]
        - results["total_saving"]
    )

    return results


def summarize_scenario(results):
    as_is = results["as_is_lead_time"].mean()
    to_be = results["to_be_lead_time"].mean()

    hours_saved = as_is - to_be

    improvement_pct = (
        hours_saved / as_is * 100
    )

    total_hours_saved = (
        results["total_saving"].sum()
    )

    return {
        "as_is_avg_lead_time": as_is,
        "to_be_avg_lead_time": to_be,
        "avg_hours_saved": hours_saved,
        "lead_time_improvement_pct": improvement_pct,
        "total_hours_saved": total_hours_saved,
    }


def summarize_scenario(results):
    as_is = results["as_is_lead_time"].mean()
    to_be = results["to_be_lead_time"].mean()

    hours_saved = as_is - to_be

    improvement_pct = (
        hours_saved / as_is * 100
    )

    total_hours_saved = (
        results["total_saving"].sum()
    )

    return {
        "as_is_avg_lead_time": as_is,
        "to_be_avg_lead_time": to_be,
        "avg_hours_saved": hours_saved,
        "lead_time_improvement_pct": improvement_pct,
        "total_hours_saved": total_hours_saved,
    }


if __name__ == "__main__":
    df = load_event_log(
        "data/raw/event_log.csv"
    )

    validate_event_log(df)
    df = prepare_event_log(df)

    results = simulate_to_be(df)
    summary = summarize_scenario(results)

    print("\n--- Improvement Scenario ---")

    print(
        f"As-Is average lead time: "
        f"{summary['as_is_avg_lead_time']:.2f} h"
    )

    print(
        f"To-Be average lead time: "
        f"{summary['to_be_avg_lead_time']:.2f} h"
    )

    print(
        f"Average saving per case: "
        f"{summary['avg_hours_saved']:.2f} h"
    )

    print(
        f"Lead-time improvement: "
        f"{summary['lead_time_improvement_pct']:.1f}%"
    )

    print(
        f"Total hours saved across dataset: "
        f"{summary['total_hours_saved']:.1f} h"
    )