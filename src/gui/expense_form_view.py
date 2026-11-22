import customtkinter as ctk
from typing import Any, Callable, Dict, List


class ExpenseFormView(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        groups: List[Dict[str, Any]],
        selected_group_id: str,
        on_submit: Callable[[str, str, float, str, List[str]], bool],
        on_back: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.groups = groups
        self.on_submit = on_submit
        self.on_back = on_back
        self.vars: Dict[str, ctk.BooleanVar] = {}

        self.grid_columnconfigure(0, weight=1)
        card = ctk.CTkFrame(self, corner_radius=12)
        card.grid(row=0, column=0, padx=16, pady=12, sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Nhập hóa đơn chi tiêu", font=ctk.CTkFont(size=19, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=18, pady=(16, 10), sticky="w")

        ctk.CTkLabel(card, text="Nhóm:").grid(row=1, column=0, padx=18, pady=7, sticky="w")
        self.opt_group = ctk.CTkOptionMenu(card, values=[""], command=self._on_group_change)
        self.opt_group.grid(row=1, column=1, padx=18, pady=7, sticky="ew")

        ctk.CTkLabel(card, text="Tên khoản chi:").grid(row=2, column=0, padx=18, pady=7, sticky="w")
        self.ent_title = ctk.CTkEntry(card, placeholder_text="VD: Tiền ăn, Cà phê, Vé xe...")
        self.ent_title.grid(row=2, column=1, padx=18, pady=7, sticky="ew")

        ctk.CTkLabel(card, text="Số tiền (VND):").grid(row=3, column=0, padx=18, pady=7, sticky="w")
        self.ent_amount = ctk.CTkEntry(card, placeholder_text="VD: 120000")
        self.ent_amount.grid(row=3, column=1, padx=18, pady=7, sticky="ew")

        ctk.CTkLabel(card, text="Người trả:").grid(row=4, column=0, padx=18, pady=7, sticky="w")
        self.opt_payer = ctk.CTkOptionMenu(card, values=[""])
        self.opt_payer.grid(row=4, column=1, padx=18, pady=7, sticky="ew")

        ctk.CTkLabel(card, text="Thành viên chia:").grid(
            row=5, column=0, padx=18, pady=7, sticky="nw"
        )
        self.box_members = ctk.CTkScrollableFrame(card, height=130)
        self.box_members.grid(row=5, column=1, padx=18, pady=7, sticky="ew")

        self.lbl_msg = ctk.CTkLabel(card, text="")
        self.lbl_msg.grid(row=6, column=0, columnspan=2, padx=18, pady=4, sticky="w")

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.grid(row=7, column=0, columnspan=2, padx=18, pady=(6, 18), sticky="e")
        ctk.CTkButton(btns, text="← Dashboard", fg_color="gray40", command=self.on_back).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(btns, text="Lưu hóa đơn", command=self._save).pack(side="left")

        self.refresh(groups, selected_group_id)

    def _on_group_change(self, gname: str) -> None:
        grp = next((g for g in self.groups if g["name"] == gname), None)
        if not grp:
            return
        members = grp.get("members", [])
        self.opt_payer.configure(values=members if members else [""])
        if members:
            self.opt_payer.set(members[0])

        for w in self.box_members.winfo_children():
            w.destroy()
        self.vars.clear()
        for m in members:
            v = ctk.BooleanVar(value=True)
            self.vars[m] = v
            ctk.CTkCheckBox(self.box_members, text=m, variable=v).pack(anchor="w", padx=6, pady=2)

    def _save(self) -> None:
        grp = next((g for g in self.groups if g["name"] == self.opt_group.get()), None)
        if not grp:
            return
        try:
            amt = float(self.ent_amount.get().replace(",", "").strip())
        except ValueError:
            self.lbl_msg.configure(text="Số tiền không hợp lệ.", text_color="#C62828")
            return
        participants = [m for m, v in self.vars.items() if v.get()]
        if amt <= 0 or not participants:
            self.lbl_msg.configure(
                text="Nhập số tiền > 0 và chọn ít nhất 1 thành viên.", text_color="#C62828"
            )
            return
        if self.on_submit(
            grp["id"],
            self.ent_title.get().strip() or "Khoản chi",
            amt,
            self.opt_payer.get(),
            participants,
        ):
            self.ent_title.delete(0, "end")
            self.ent_amount.delete(0, "end")
            self.lbl_msg.configure(text="Đã lưu hóa đơn thành công!", text_color="#2E7D32")

    def refresh(self, groups: List[Dict[str, Any]], selected_group_id: str) -> None:
        self.groups = groups
        names = [g["name"] for g in groups]
        if not names:
            return
        self.opt_group.configure(values=names)
        cur = next((g for g in groups if g["id"] == selected_group_id), groups[0])
        self.opt_group.set(cur["name"])
        self._on_group_change(cur["name"])