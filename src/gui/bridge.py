from typing import Any, Dict, List


class GuiBridge:
    """Lớp trung gian nối UI với các module nghiệp vụ của ChuDe13."""

    def __init__(self) -> None:
        self._groups: List[Dict[str, Any]] = [
            {
                "id": "g1",
                "name": "Nhóm Chủ Đề 13",
                "members": ["Lương", "Kiên", "Lợi", "Thục", "Lộc"],
                "balances": {
                    "Lương": 150000.0,
                    "Kiên": -50000.0,
                    "Lợi": -40000.0,
                    "Thục": -60000.0,
                    "Lộc": 0.0,
                },
                "expenses": [
                    {
                        "title": "Ăn trưa team",
                        "amount": 250000.0,
                        "payer": "Lương",
                        "participants": ["Lương", "Kiên", "Lợi", "Thục", "Lộc"],
                    }
                ],
            }
        ]

    def get_groups(self) -> List[Dict[str, Any]]:
        # TODO: nối hàm lấy nhóm/số dư từ backend hoặc luong_stats_logger nếu có
        return self._groups

    def create_group(self, name: str, members: List[str]) -> Dict[str, Any]:
        clean_members = [m.strip() for m in members if m.strip()]
        new_group = {
            "id": f"g{len(self._groups) + 1}",
            "name": name.strip(),
            "members": clean_members,
            "balances": {m: 0.0 for m in clean_members},
            "expenses": [],
        }
        self._groups.append(new_group)
        return new_group

    def add_expense(
        self,
        group_id: str,
        title: str,
        amount: float,
        payer: str,
        participants: List[str],
    ) -> bool:
        # TODO: gọi hàm lưu hóa đơn / chia tiền từ expense_service.py & expense_split.py
        group = next((g for g in self._groups if g["id"] == group_id), None)
        if not group or amount <= 0 or not participants:
            return False

        group["expenses"].append(
            {
                "title": title.strip() or "Khoản chi",
                "amount": amount,
                "payer": payer,
                "participants": list(participants),
            }
        )

        share = amount / len(participants)
        for m in group["members"]:
            group["balances"].setdefault(m, 0.0)
            if m == payer:
                group["balances"][m] += amount
            if m in participants:
                group["balances"][m] -= share
        return True

    def compute_settlements(self, group_id: str) -> List[Dict[str, Any]]:
        # TODO: gọi hàm tối ưu nợ từ settlement_service.py
        group = next((g for g in self._groups if g["id"] == group_id), None)
        if not group:
            return []

        debtors = [[p, -b] for p, b in group["balances"].items() if b < -1e-6]
        creditors = [[p, b] for p, b in group["balances"].items() if b > 1e-6]
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)

        transfers: List[Dict[str, Any]] = []
        i = j = 0
        while i < len(debtors) and j < len(creditors):
            pay = min(debtors[i][1], creditors[j][1])
            transfers.append(
                {
                    "from": debtors[i][0],
                    "to": creditors[j][0],
                    "amount": round(pay, 0),
                }
            )
            debtors[i][1] -= pay
            creditors[j][1] -= pay
            if debtors[i][1] <= 1e-6:
                i += 1
            if creditors[j][1] <= 1e-6:
                j += 1
        return transfers

    def generate_vietqr(self, sender: str, receiver: str, amount: float) -> str:
        # TODO: nối module tạo VietQR trong src/integrations/vietqr/
        return f"VietQR sẵn sàng: {sender} -> {receiver} | {amount:,.0f} VND"

    def export_report(self, group_id: str, fmt: str) -> str:
        # TODO: nối module xuất file CSV/Excel trong src/exports/
        return f"Đã chuẩn bị xuất báo cáo nhóm [{group_id}] dạng {fmt.upper()}"