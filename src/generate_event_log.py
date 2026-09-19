import random
from datetime import datetime, timedelta

import pandas as pd


# Reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)


# Teams responsible for each activity
ACTIVITY_TEAMS = {
    "Claim Received": "Customer Service",
    "Initial Review": "Customer Service",
    "Request Additional Information": "Customer Service",
    "Technical Assessment": "Technical",
    "Quality Review": "Quality",
    "Decision": "Quality",
    "Customer Notification": "Customer Service",
    "Case Closed": "Customer Service",
}


NORMAL_PROCESS = [
    "Claim Received",
    "Initial Review",
    "Technical Assessment",
    "Quality Review",
    "Decision",
    "Customer Notification",
    "Case Closed",
]

PROCESS_VARIANTS = {
    "normal": NORMAL_PROCESS,

    "missing_information": [
        "Claim Received",
        "Initial Review",
        "Request Additional Information",
        "Initial Review",
        "Technical Assessment",
        "Quality Review",
        "Decision",
        "Customer Notification",
        "Case Closed",
    ],

    "technical_rework": [
        "Claim Received",
        "Initial Review",
        "Technical Assessment",
        "Quality Review",
        "Technical Assessment",
        "Quality Review",
        "Decision",
        "Customer Notification",
        "Case Closed",
    ],

    "ping_pong": [
        "Claim Received",
        "Initial Review",
        "Technical Assessment",
        "Quality Review",
        "Technical Assessment",
        "Quality Review",
        "Technical Assessment",
        "Quality Review",
        "Decision",
        "Customer Notification",
        "Case Closed",
    ],
}

PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

# Typical waiting time before each activity, in hours.
WAIT_TIME_RANGES = {
    "Initial Review": (1, 6),
    "Request Additional Information": (12, 48),
    "Technical Assessment": (4, 18),
    "Quality Review": (12, 36),
    "Decision": (2, 8),
    "Customer Notification": (1, 4),
    "Case Closed": (1, 6),
}

PRIORITY_MULTIPLIERS = {
    "Low": 1.2,
    "Medium": 1.0,
    "High": 0.8,
    "Critical": 0.5,
}

ABNORMAL_DELAY_PROBABILITY = 0.05
ABNORMAL_DELAY_MULTIPLIER = 3.0

VARIANT_WEIGHTS = {
    "normal": 0.65,
    "missing_information": 0.18,
    "technical_rework": 0.12,
    "ping_pong": 0.05,
}

PRIORITY_WEIGHTS = {
    "Low": 0.15,
    "Medium": 0.50,
    "High": 0.25,
    "Critical": 0.10,
}


def generate_waiting_time(activity, priority):
    min_hours, max_hours = WAIT_TIME_RANGES[activity]

    waiting_hours = random.uniform(min_hours, max_hours)

    # Adjust waiting time according to case priority
    waiting_hours *= PRIORITY_MULTIPLIERS[priority]

    # Occasionally simulate an unusually long delay
    if random.random() < ABNORMAL_DELAY_PROBABILITY:
        waiting_hours *= ABNORMAL_DELAY_MULTIPLIER

    return waiting_hours


def generate_case(case_id, start_time, variant, priority):
    activities = PROCESS_VARIANTS[variant]

    events = []
    current_time = start_time

    for i, activity in enumerate(activities):
        if i > 0:
            waiting_hours = generate_waiting_time(activity=activity, priority=priority,)
            current_time += timedelta(hours=waiting_hours)

        event = {
            "case_id": case_id,
            "activity": activity,
            "timestamp": current_time,
            "team": ACTIVITY_TEAMS[activity],
            "status": "Completed",
            "priority": priority,
        }

        events.append(event)

    return events


def generate_event_log(num_cases=750):
    all_events = []

    variants = list(VARIANT_WEIGHTS.keys())
    variant_weights = list(VARIANT_WEIGHTS.values())

    priorities = list(PRIORITY_WEIGHTS.keys())
    priority_weights = list(PRIORITY_WEIGHTS.values())

    base_date = datetime(2026, 1, 1, 8, 0)

    for i in range(1, num_cases + 1):
        case_id = f"C{i:04d}"

        variant = random.choices(
            variants,
            weights=variant_weights,
            k=1,
        )[0]

        priority = random.choices(
            priorities,
            weights=priority_weights,
            k=1,
        )[0]

        # Cases arrive throughout roughly six months
        start_offset_days = random.randint(0, 180)
        start_offset_hours = random.randint(0, 10)

        start_time = (
            base_date
            + timedelta(days=start_offset_days)
            + timedelta(hours=start_offset_hours)
        )

        case_events = generate_case(
            case_id=case_id,
            start_time=start_time,
            variant=variant,
            priority=priority,
        )

        all_events.extend(case_events)

    return pd.DataFrame(all_events)



if __name__ == "__main__":
    df = generate_event_log(num_cases=750)

    output_path = "data/raw/event_log.csv"
    df.to_csv(output_path, index=False)

    print(f"Generated {len(df):,} events")
    print(f"Generated {df['case_id'].nunique():,} cases")
    print(f"Saved event log to: {output_path}")

    print("\nFirst 10 events:")
    print(df.head(10))