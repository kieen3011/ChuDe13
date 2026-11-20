import csv
import json
from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.luong_stats_logger import (
    count_breaches_by_location,
    count_breaches_by_location_and_severity,
    count_breaches_by_severity,
    export_alert_logs_csv,
    export_report_json,
)


def test_tc01_breach_by_location():
    """Kiểm thử thống kê tổng số lần vượt ngưỡng theo từng vị trí."""
    records = [
        {"location": "Site-1", "value": 120, "threshold": 100, "severity": "CRITICAL"},
        {"location": "Site-1", "value": 105, "threshold": 100, "severity": "WARNING"},
        {"location": "Site-2", "value": 150, "threshold": 100, "severity": "CRITICAL"},
        {"location": "Site-3", "value": 90, "threshold": 100, "severity": "INFO"},
    ]
    assert count_breaches_by_location(records) == {"Site-1": 2, "Site-2": 1}


def test_tc02_breach_by_severity_and_matrix():
    """Kiểm thử thống kê vượt ngưỡng theo mức độ cảnh báo và ma trận vị trí x mức độ."""
    records = [
        {"location": "Site-1", "value": 120, "threshold": 100, "severity": "CRITICAL"},
        {"location": "Site-1", "value": 105, "threshold": 100, "severity": "WARNING"},
        {"location": "Site-2", "value": 150, "threshold": 100, "severity": "CRITICAL"},
    ]
    assert count_breaches_by_severity(records) == {"CRITICAL": 2, "WARNING": 1}
    assert count_breaches_by_location_and_severity(records) == {
        "Site-1": {"CRITICAL": 1, "WARNING": 1},
        "Site-2": {"CRITICAL": 1},
    }


def test_tc03_equal_or_below_threshold():
    """Kiểm thử trường hợp bằng ngưỡng hoặc nhỏ hơn ngưỡng không tính là vượt ngưỡng."""
    records = [
        {"location": "Site-1", "value": 100, "threshold": 100, "severity": "WARNING"},
        {"location": "Site-1", "value": 40, "threshold": 100, "severity": "INFO"},
    ]
    assert count_breaches_by_location(records) == {}
    assert count_breaches_by_severity(records) == {}


def test_tc04_empty_list(tmp_path: Path):
    """Kiểm thử danh sách rỗng không gây lỗi và xuất file rỗng hợp lệ."""
    assert count_breaches_by_location([]) == {}
    assert count_breaches_by_severity([]) == {}

    csv_file = export_alert_logs_csv([], tmp_path / "alert_logs.csv")
    json_file = export_report_json([], tmp_path / "report.json")
    assert csv_file.exists()
    assert json_file.exists()

    data = json.loads(json_file.read_text(encoding="utf-8"))
    assert data["summary"]["total_records"] == 0
    assert data["summary"]["total_breaches"] == 0


def test_tc05_error_and_malformed_records():
    """Kiểm thử bản ghi lỗi, thiếu trường, kiểu dữ liệu sai không làm crash chương trình."""
    records = [
        {"value": 110, "threshold": 100},  # thiếu location & severity -> UNKNOWN
        {"location": "Site-1", "value": "invalid", "threshold": 100, "severity": "CRITICAL", "status": "ERROR"},
        {"location": "Site-1", "value": True, "threshold": 0, "severity": "WARNING"},
        12345,  # phần tử không phải dict
    ]
    assert count_breaches_by_location(records) == {"UNKNOWN": 1}
    assert count_breaches_by_severity(records) == {"UNKNOWN": 1}


def test_tc06_export_csv_and_json(tmp_path: Path):
    """Kiểm thử xuất alert_logs.csv và report.json đúng dữ liệu."""
    records = [
        {
            "timestamp": "2026-11-20T10:00:00Z",
            "location": "Site-1",
            "metric": "quota",
            "value": 200,
            "threshold": 100,
            "severity": "CRITICAL",
            "message": "Vượt hạn mức",
        },
        {
            "timestamp": "2026-11-20T10:05:00Z",
            "location": "Site-2",
            "metric": "quota",
            "value": 50,
            "threshold": 100,
            "severity": "INFO",
            "message": "Bình thường",
        },
    ]
    csv_path = export_alert_logs_csv(records, tmp_path / "alert_logs.csv")
    json_path = export_report_json(records, tmp_path / "report.json")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["location"] == "Site-1"
    assert rows[0]["is_breach"] == "True"

    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["summary"]["total_records"] == 2
    assert report["summary"]["total_breaches"] == 1
    assert report["breaches_by_location"] == {"Site-1": 1}
    assert report["breaches_by_severity"] == {"CRITICAL": 1}


def test_tc07_invalid_root_type():
    """Kiểm thử truyền sai kiểu dữ liệu tổng thể (không phải list) ném TypeError."""
    with pytest.raises(TypeError):
        count_breaches_by_location({"not": "a list"})  # type: ignore[arg-type]