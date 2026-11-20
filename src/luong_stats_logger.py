import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def normalize_records(records: Any) -> list[dict[str, Any]]:
    """Chuẩn hóa danh sách bản ghi đầu vào và xử lý an toàn trường hợp thiếu/sai kiểu dữ liệu."""
    if not isinstance(records, list):
        raise TypeError("Dữ liệu đầu vào phải là một danh sách (list) các bản ghi.")

    normalized_records: list[dict[str, Any]] = []
    for idx, item in enumerate(records):
        if not isinstance(item, dict):
            normalized_records.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "location": "UNKNOWN",
                    "metric": "",
                    "value": "",
                    "threshold": "",
                    "severity": "UNKNOWN",
                    "status": "ERROR",
                    "is_breach": False,
                    "message": f"Bản ghi không hợp lệ tại chỉ mục {idx}",
                }
            )
            continue

        raw_location = item.get("location")
        location = (
            str(raw_location).strip()
            if raw_location is not None and str(raw_location).strip()
            else "UNKNOWN"
        )

        raw_severity = item.get("severity")
        severity = (
            str(raw_severity).strip().upper()
            if raw_severity is not None and str(raw_severity).strip()
            else "UNKNOWN"
        )

        raw_status = item.get("status")
        status = (
            str(raw_status).strip().upper()
            if raw_status is not None and str(raw_status).strip()
            else ""
        )

        value = item.get("value")
        threshold = item.get("threshold")

        valid_value = isinstance(value, (int, float)) and not isinstance(value, bool)
        valid_threshold = isinstance(threshold, (int, float)) and not isinstance(threshold, bool)

        if status == "ERROR":
            is_breach = False
        elif status == "BREACH":
            is_breach = True
        elif valid_value and valid_threshold:
            is_breach = value > threshold
        else:
            is_breach = False

        if not status:
            if is_breach:
                status = "BREACH"
            elif valid_value and valid_threshold:
                status = "OK"
            else:
                status = "ERROR"

        raw_ts = item.get("timestamp")
        timestamp = (
            str(raw_ts).strip()
            if raw_ts is not None and str(raw_ts).strip()
            else datetime.now(timezone.utc).isoformat()
        )

        normalized_records.append(
            {
                "timestamp": timestamp,
                "location": location,
                "metric": str(item.get("metric") or ""),
                "value": value if valid_value else "",
                "threshold": threshold if valid_threshold else "",
                "severity": severity,
                "status": status,
                "is_breach": is_breach,
                "message": str(item.get("message") or ""),
            }
        )

    return normalized_records


def count_breaches_by_location(records: list[dict[str, Any]]) -> dict[str, int]:
    """Thống kê tổng số lần vượt ngưỡng theo từng vị trí."""
    normalized = normalize_records(records)
    counts: Counter[str] = Counter()
    for row in normalized:
        if row["is_breach"]:
            counts[row["location"]] += 1
    return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))


def count_breaches_by_severity(records: list[dict[str, Any]]) -> dict[str, int]:
    """Thống kê tổng số lần vượt ngưỡng theo mức độ cảnh báo."""
    normalized = normalize_records(records)
    counts: Counter[str] = Counter()
    for row in normalized:
        if row["is_breach"]:
            counts[row["severity"]] += 1
    return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))


def count_breaches_by_location_and_severity(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """Thống kê số lần vượt ngưỡng theo từng vị trí và từng mức độ cảnh báo."""
    normalized = normalize_records(records)
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    for row in normalized:
        if row["is_breach"]:
            matrix[row["location"]][row["severity"]] += 1
    return {
        loc: dict(sorted(sev_counts.items(), key=lambda x: (-x[1], x[0])))
        for loc, sev_counts in sorted(matrix.items())
    }


def export_alert_logs_csv(records: list[dict[str, Any]], output_path: str | Path) -> Path:
    """Xuất lịch sử hoạt động ra file alert_logs.csv."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_records(records)

    fieldnames = [
        "timestamp",
        "location",
        "metric",
        "value",
        "threshold",
        "severity",
        "status",
        "is_breach",
        "message",
    ]

    with path.open(mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in normalized:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    return path


def export_report_json(records: list[dict[str, Any]], output_path: str | Path) -> Path:
    """Xuất kết quả thống kê tổng hợp ra file report.json."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_records(records)

    total_breaches = sum(1 for row in normalized if row["is_breach"])
    total_ok = sum(1 for row in normalized if row["status"] == "OK")
    total_errors = sum(1 for row in normalized if row["status"] == "ERROR")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_records": len(normalized),
            "total_breaches": total_breaches,
            "total_ok": total_ok,
            "total_errors": total_errors,
        },
        "breaches_by_location": count_breaches_by_location(records),
        "breaches_by_severity": count_breaches_by_severity(records),
        "breaches_by_location_and_severity": count_breaches_by_location_and_severity(records),
    }

    with path.open(mode="w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return path