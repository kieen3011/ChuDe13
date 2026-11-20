import json
from pathlib import Path
import sys

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


def sample_records() -> list[dict]:
    """Bộ dữ liệu mẫu giả lập phục vụ chạy thống kê và kiểm thử."""
    return [
        {
            "timestamp": "2026-11-20T08:00:00Z",
            "location": "KhuVuc-A",
            "metric": "expense_limit_pct",
            "value": 125,
            "threshold": 100,
            "severity": "CRITICAL",
            "message": "Vượt ngưỡng ngân sách mức nghiêm trọng",
        },
        {
            "timestamp": "2026-11-20T08:10:00Z",
            "location": "KhuVuc-A",
            "metric": "expense_limit_pct",
            "value": 108,
            "threshold": 100,
            "severity": "WARNING",
            "message": "Vượt ngưỡng ngân sách mức cảnh báo",
        },
        {
            "timestamp": "2026-11-20T08:20:00Z",
            "location": "KhuVuc-B",
            "metric": "expense_limit_pct",
            "value": 115,
            "threshold": 100,
            "severity": "WARNING",
            "message": "Vượt ngưỡng chi tiêu tại KhuVuc-B",
        },
        {
            "timestamp": "2026-11-20T08:30:00Z",
            "location": "KhuVuc-B",
            "metric": "expense_limit_pct",
            "value": 100,
            "threshold": 100,
            "severity": "WARNING",
            "message": "Bằng ngưỡng quy định (chưa vượt ngưỡng)",
        },
        {
            "timestamp": "2026-11-20T08:40:00Z",
            "location": "KhuVuc-C",
            "metric": "expense_limit_pct",
            "value": 65,
            "threshold": 100,
            "severity": "INFO",
            "message": "Dưới ngưỡng, trạng thái bình thường",
        },
        {
            "timestamp": "2026-11-20T08:50:00Z",
            "metric": "expense_limit_pct",
            "value": 130,
            "threshold": 100,
            "severity": "CRITICAL",
            "message": "Vượt ngưỡng nhưng thiếu location -> gán UNKNOWN",
        },
        {
            "timestamp": "2026-11-20T09:00:00Z",
            "location": "KhuVuc-C",
            "metric": "expense_limit_pct",
            "value": "bad_value",
            "threshold": 100,
            "severity": "CRITICAL",
            "status": "ERROR",
            "message": "Bản ghi lỗi dữ liệu đầu vào",
        },
    ]


def main() -> None:
    records = sample_records()
    out_dir = ROOT_DIR / "outputs"

    by_loc = count_breaches_by_location(records)
    by_sev = count_breaches_by_severity(records)
    by_matrix = count_breaches_by_location_and_severity(records)

    csv_path = export_alert_logs_csv(records, out_dir / "alert_logs.csv")
    json_path = export_report_json(records, out_dir / "report.json")

    print("=== KẾT QUẢ THỐNG KÊ THỰC NGHIỆM ===")
    print("Tổng bản ghi:", len(records))
    print("Vượt ngưỡng theo vị trí:", json.dumps(by_loc, ensure_ascii=False))
    print("Vượt ngưỡng theo mức độ:", json.dumps(by_sev, ensure_ascii=False))
    print("Ma trận vị trí x mức độ:", json.dumps(by_matrix, ensure_ascii=False))
    print("File CSV:", csv_path)
    print("File JSON:", json_path)


if __name__ == "__main__":
    main()