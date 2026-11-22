import customtkinter as ctk
from typing import Any, Callable, Dict, List


class DashboardView(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        groups: List[Dict[str, Any]],
        selected_group_id: str,
        on_select_group: Callable[[str], None],
        on_create_group: Callable[[str, List[str]], None],
        on_go_expense: Callable[[], None],
        on_go_settlement: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_select_group = on_select_group
        self.on_create_group = on_create_group
        self.on_go_expense = on_go_expense
        self.on_go_settlement = on_go_settlement

        self.grid_columnconfigure(0, weight=1, minsize=230)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="nsew")
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left, text="Danh sách nhóm", font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        self.group_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.group_scroll.grid(row=1, column=0, padx=8, pady=4, sticky="nsew")
        self.group_scroll.grid_columnconfigure(0, weight=1)

        create_card = ctk.CTkFrame(left, corner_radius=10)
        create_card.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        create_card.grid_columnconfigure(0, weight=1)

        self.ent_name = ctk.CTkEntry(create_card, placeholder_text="Tên nhóm mới")
        self.ent_name.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="ew")

        self.ent_members = ctk.CTkEntry(
            create_card, placeholder_text="Thành viên (cách nhau dấu phẩy)"
        )
        self.ent_members.grid(row=1, column=0, padx=8, pady=4, sticky="ew")

        ctk.CTkButton(create_card, text="+ Tạo nhóm", command=self._handle_create).grid(
            row=2, column=0, padx=8, pady=(4, 8), sticky="ew"
        )

        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, padx=(8, 0), pady=4, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(3, weight=1)

        top = ctk.CTkFrame(right, fg_color="transparent")
        top.grid(row=0, column=0, padx=14, pady=(14, 6), sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            top, text="Dashboard", font=ctk.CTkFont(size=19, weight="bold")
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(top, text="+ Hóa đơn", width=100, command=self.on_go_expense).grid(
            row=0, column=1, padx=(0, 8)
        )
        ctk.CTkButton(
            top,
            text="Tối ưu nợ →",
            width=110,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self.on_go_settlement,
        ).grid(row=0, column=2)

        self.lbl_members = ctk.CTkLabel(
            right, text="Thành viên: -", justify="left", wraplength=660
        )
        self.lbl_members.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="w")

        ctk.CTkLabel(
            right,
            text="Bảng tổng hợp tình trạng nợ",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=2, column=0, padx=14, pady=(4, 4), sticky="w")

        self.table_scroll = ctk.CTkScrollableFrame(right, corner_radius=8)
        self.table_scroll.grid(row=3, column=0, padx=14, pady=(0, 14), sticky="nsew")
        self.table_scroll.grid_columnconfigure((0, 1, 2), weight=1)

        self.refresh(groups, selected_group_id)

    def _handle_create(self) -> None:
        name = self.ent_name.get().strip()
        members = [m.strip() for m in self.ent_members.get().split(",") if m.strip()]
        if name and members:
            self.on_create_group(name, members)
            self.ent_name.delete(0, "end")
            self.ent_members.delete(0, "end")

    def refresh(self, groups: List[Dict[str, Any]], selected_group_id: str) -> None:
        for w in self.group_scroll.winfo_children():
            w.destroy()

        current = None
        for g in groups:
            active = g["id"] == selected_group_id
            if active:
                current = g
            ctk.CTkButton(
                self.group_scroll,
                text=f"{g['name']} ({len(g.get('members', []))})",
                anchor="w",
                fg_color=("#1F6AA5", "#1F6AA5") if active else ("gray82", "gray25"),
                text_color=("white", "white") if active else ("gray10", "gray90"),
                command=lambda gid=g["id"]: self.on_select_group(gid),
            ).grid(sticky="ew", pady=3, padx=2)

        if not current and groups:
            current = groups[0]
        if not current:
            return

        members = current.get("members", [])
        balances = current.get("balances", {})
        self.lbl_title.configure(text=f"Nhóm: {current['name']}")
        self.lbl_members.configure(text=f"Thành viên: {', '.join(members)}")

        for w in self.table_scroll.winfo_children():
            w.destroy()

        for c, h in enumerate(["Thành viên", "Số dư ròng", "Tình trạng"]):
            ctk.CTkLabel(
                self.table_scroll, text=h, font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=c, padx=10, pady=6, sticky="w")

        for r, m in enumerate(members, start=1):
            bal = float(balances.get(m, 0.0))
            if bal > 1e-6:
                st, clr = f"Được nhận +{bal:,.0f}đ", "#2E7D32"
            elif bal < -1e-6:
                st, clr = f"Nợ {abs(bal):,.0f}đ", "#C62828"
            else:
                st, clr = "Cân bằng", ("gray35", "gray70")

            ctk.CTkLabel(self.table_scroll, text=m).grid(
                row=r, column=0, padx=10, pady=5, sticky="w"
            )
            ctk.CTkLabel(self.table_scroll, text=f"{bal:+,.0f} đ", text_color=clr).grid(
                row=r, column=1, padx=10, pady=5, sticky="w"
            )
            ctk.CTkLabel(self.table_scroll, text=st, text_color=clr).grid(
                row=r, column=2, padx=10, pady=5, sticky="w"
            )