import pandas as pd
import pm4py

from transform import load_event_log, validate_event_log, prepare_event_log


def prepare_for_pm4py(df):
    pm_df = df.rename(
        columns={
            "case_id": "case:concept:name",
            "activity": "concept:name",
            "timestamp": "time:timestamp",
        }
    ).copy()

    pm_df = pm4py.format_dataframe(
        pm_df,
        case_id="case:concept:name",
        activity_key="concept:name",
        timestamp_key="time:timestamp",
    )

    return pm_df


def discover_dfg(pm_df):
    dfg, start_activities, end_activities = (
        pm4py.discover_dfg(pm_df)
    )

    return dfg, start_activities, end_activities



def get_process_variants(pm_df):
    variants = pm4py.get_variants_as_tuples(pm_df)

    variant_summary = []

    for variant, case_ids in variants.items():
        variant_summary.append(
            {
                "variant": " → ".join(variant),
                "case_count": len(case_ids),
            }
        )

    return (
        pd.DataFrame(variant_summary)
        .sort_values("case_count", ascending=False)
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    df = load_event_log("data/raw/event_log.csv")

    validate_event_log(df)
    df = prepare_event_log(df)

    pm_df = prepare_for_pm4py(df)

    dfg, start_activities, end_activities = discover_dfg(pm_df)

    print("\nStart activities:")
    print(start_activities)

    print("\nEnd activities:")
    print(end_activities)

    print("\nDirectly-Follows Graph:")
    for transition, frequency in sorted(
        dfg.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        print(f"{transition}: {frequency}")

    pm4py.view_dfg(
        dfg,
        start_activities,
        end_activities,
    )
    variants = get_process_variants(pm_df)

    print("\nProcess variants:")
    print(variants.to_string(index=False))