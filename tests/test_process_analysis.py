import sys
from pathlib import Path
import pytest
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
sys.path.append(str(SRC_PATH))

from transform import validate_event_log, prepare_event_log
from kpis import case_lead_times
from process_analysis import detect_rework_cases, detect_ping_pong_cases
from alerts import create_case_alerts


def create_test_event_log():
    data = [
        {
            "case_id": "C001",
            "activity": "Claim Received",
            "timestamp": "2026-01-01 08:00:00",
            "team": "Customer Service",
            "status": "Completed",
            "priority": "Medium",
        },
        {
            "case_id": "C001",
            "activity": "Initial Review",
            "timestamp": "2026-01-01 10:00:00",
            "team": "Customer Service",
            "status": "Completed",
            "priority": "Medium",
        },
        {
            "case_id": "C001",
            "activity": "Technical Assessment",
            "timestamp": "2026-01-01 14:00:00",
            "team": "Technical",
            "status": "Completed",
            "priority": "Medium",
        },
        {
            "case_id": "C001",
            "activity": "Quality Review",
            "timestamp": "2026-01-02 14:00:00",
            "team": "Quality",
            "status": "Completed",
            "priority": "Medium",
        },
        {
            "case_id": "C001",
            "activity": "Technical Assessment",
            "timestamp": "2026-01-02 18:00:00",
            "team": "Technical",
            "status": "Completed",
            "priority": "Medium",
        },
        {
            "case_id": "C001",
            "activity": "Quality Review",
            "timestamp": "2026-01-03 18:00:00",
            "team": "Quality",
            "status": "Completed",
            "priority": "Medium",
        },
        {
            "case_id": "C001",
            "activity": "Decision",
            "timestamp": "2026-01-03 20:00:00",
            "team": "Quality",
            "status": "Completed",
            "priority": "Medium",
        },
        {
            "case_id": "C001",
            "activity": "Customer Notification",
            "timestamp": "2026-01-03 21:00:00",
            "team": "Customer Service",
            "status": "Completed",
            "priority": "Medium",
        },
        {
            "case_id": "C001",
            "activity": "Case Closed",
            "timestamp": "2026-01-03 22:00:00",
            "team": "Customer Service",
            "status": "Completed",
            "priority": "Medium",
        },
    ]

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return prepare_event_log(df)


def test_valid_event_log():
    df = create_test_event_log()

    assert validate_event_log(df) is True


def test_missing_required_column():
    df = create_test_event_log()
    df = df.drop(columns=["priority"])

    with pytest.raises(ValueError):
        validate_event_log(df)


def test_case_lead_time():
    df = create_test_event_log()

    lead_times = case_lead_times(df)

    assert len(lead_times) == 1
    assert lead_times.iloc[0]["lead_time_hours"] == 62


def test_rework_detection():
    df = create_test_event_log()

    rework = detect_rework_cases(df)

    assert len(rework) == 1
    assert rework.iloc[0]["case_id"] == "C001"
    assert rework.iloc[0]["rework_count"] == 1


def test_ping_pong_detection():
    df = create_test_event_log()

    ping_pong = detect_ping_pong_cases(df)

    assert len(ping_pong) == 0


def test_rework_alone_does_not_trigger_alert():
    df = create_test_event_log()

    alerts = create_case_alerts(df)

    assert len(alerts) == 1
    assert bool(alerts.iloc[0]["has_rework"]) is True
    assert bool(alerts.iloc[0]["alert"]) is False