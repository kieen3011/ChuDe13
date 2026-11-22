import customtkinter as ctk
from typing import Any, Callable, Dict, List


class SettlementView(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        group_name: str,
        settlements: List[Dict[str, Any]],
        on_qr: Callable[[str, str, float], str],
        on_export: Callable[[str], str],
        on_back: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_qr = on_qr
        self.on_export = on_export
        self.on_back = on_back

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, padx=14, pady=(10, 6), sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            top, text=f"Kết quả tối ưu nợ — {group_name}", font=ctk.CTkFont(size=19, weight="bold")
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")
        ctk.CTkButton(top, text="← Dashboard", fg_color="gray40", command=self.on_back).grid(
            row=0, column=1
        )

        self.rows = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.rows.grid(row=1, column=0, padx=14, pady=6, sticky="nsew")

        foot = ctk.CTkFrame(self, corner_radius=12)
        foot.grid(row=2, column=0, padx=14, pady=(6, 12), sticky="ew")
        foot.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(foot, text="Chọn VietQR ở từng dòng hoặc xuất báo cáo.")
        self.lbl_status.grid(row=0, column=0, padx=12, pady=10, sticky="w")

        ctk.CTkButton(
            foot, text="Xuất CSV", width=95, command=lambda: self._do_export("csv")
        ).grid(row=0, column=1, padx=(0, 6), pady=10)
        ctk.CTkButton(
            foot,
            text="Xuất Excel",
            width=95,
            fg_color="#1565C0",
            command=lambda: self._do_export("xlsx"),
        ).grid(row=0, column=2, padx=(0, 12), pady=10)

        self.refresh(group_name, settlements)

    def _do_qr(self, s: str, r: str, a: float) -> None:
        self.lbl_status.configure(text=self.on_qr(s, r, a))

    def _do_export(self, fmt: str) -> None:
        self.lbl_status.configure(text=self.on_export(fmt))

    def refresh(self, group_name: str, settlements: List[Dict[str, Any]]) -> None:
        self.lbl_title.configure(text=f"Kết quả tối ưu nợ — {group_name}")
        for w in self.rows.winfo_children():
            w.destroy()

        if not settlements:
            ctk.CTkLabel(self.rows, text="Tất cả đã cân bằng, không cần trả nợ.").pack(pady=20)
            return

        for item in settlements:
            s, r, a = item["from"], item["to"], float(item["amount"])
            line = ctk.CTkFrame(self.rows, corner_radius=10)
            line.pack(fill="x", padx=6, pady=5)
            line.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                line, text=f"{s} trả cho {r}", font=ctk.CTkFont(size=14, weight="bold")
            ).grid(row=0, column=0, padx=12, pady=10, sticky="w")
            ctk.CTkLabel(
                line,
                text=f"{a:,.0f} VND",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#2E7D32",
            ).grid(row=0, column=1, padx=8, pady=10, sticky="e")
            ctk.CTkButton(
                line, text="VietQR", width=85, command=lambda x=s, y=r, z=a: self._do_qr(x, y, z)
            ).grid(row=0, column=2, padx=(6, 12), pady=10)