import customtkinter as ctk
from src.gui.bridge import GuiBridge
from src.gui.dashboard_view import DashboardView
from src.gui.expense_form_view import ExpenseFormView
from src.gui.settlement_view import SettlementView


class ChuDe13App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Chủ Đề 13 — Quản lý Chi tiêu Nhóm")
        self.geometry("1040x640")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.bridge = GuiBridge()
        groups = self.bridge.get_groups()
        self.selected_group_id = groups[0]["id"] if groups else ""

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        nav = ctk.CTkFrame(self, width=190, corner_radius=0)
        nav.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(nav, text="CHỦ ĐỀ 13", font=ctk.CTkFont(size=18, weight="bold")).pack(
            padx=16, pady=(24, 14)
        )
        ctk.CTkButton(nav, text="Dashboard", command=lambda: self.show("dashboard")).pack(
            fill="x", padx=14, pady=6
        )
        ctk.CTkButton(nav, text="Nhập hóa đơn", command=lambda: self.show("expense")).pack(
            fill="x", padx=14, pady=6
        )
        ctk.CTkButton(nav, text="Tối ưu nợ", command=lambda: self.show("settlement")).pack(
            fill="x", padx=14, pady=6
        )

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=1, padx=12, pady=12, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.dashboard_view = DashboardView(
            container,
            groups=groups,
            selected_group_id=self.selected_group_id,
            on_select_group=self._on_select_group,
            on_create_group=self._on_create_group,
            on_go_expense=lambda: self.show("expense"),
            on_go_settlement=lambda: self.show("settlement"),
        )
        self.dashboard_view.grid(row=0, column=0, sticky="nsew")

        self.expense_view = ExpenseFormView(
            container,
            groups=groups,
            selected_group_id=self.selected_group_id,
            on_submit=self._on_add_expense,
            on_back=lambda: self.show("dashboard"),
        )
        self.expense_view.grid(row=0, column=0, sticky="nsew")

        self.settlement_view = SettlementView(
            container,
            group_name=self._current_group_name(),
            settlements=self.bridge.compute_settlements(self.selected_group_id),
            on_qr=self.bridge.generate_vietqr,
            on_export=lambda fmt: self.bridge.export_report(self.selected_group_id, fmt),
            on_back=lambda: self.show("dashboard"),
        )
        self.settlement_view.grid(row=0, column=0, sticky="nsew")

        self.show("dashboard")

    def _current_group_name(self) -> str:
        g = next(
            (x for x in self.bridge.get_groups() if x["id"] == self.selected_group_id),
            None,
        )
        return g["name"] if g else ""

    def _refresh_all(self) -> None:
        groups = self.bridge.get_groups()
        if not any(x["id"] == self.selected_group_id for x in groups) and groups:
            self.selected_group_id = groups[0]["id"]
        self.dashboard_view.refresh(groups, self.selected_group_id)
        self.expense_view.refresh(groups, self.selected_group_id)
        self.settlement_view.refresh(
            self._current_group_name(),
            self.bridge.compute_settlements(self.selected_group_id),
        )

    def _on_select_group(self, gid: str) -> None:
        self.selected_group_id = gid
        self._refresh_all()

    def _on_create_group(self, name: str, members: list[str]) -> None:
        created = self.bridge.create_group(name, members)
        self.selected_group_id = created["id"]
        self._refresh_all()

    def _on_add_expense(
        self, gid: str, title: str, amount: float, payer: str, participants: list[str]
    ) -> bool:
        ok = self.bridge.add_expense(gid, title, amount, payer, participants)
        if ok:
            self.selected_group_id = gid
            self._refresh_all()
        return ok

    def show(self, name: str) -> None:
        self._refresh_all()
        {
            "dashboard": self.dashboard_view,
            "expense": self.expense_view,
            "settlement": self.settlement_view,
        }[target_key := name].tkraise()


if __name__ == "__main__":
    ChuDe13App().mainloop()