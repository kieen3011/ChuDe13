from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from pydantic import ConfigDict, field_validator, model_validator
from datetime import datetime

# Dữ liệu yêu cầu khi tạo mới (Bắt buộc)
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Tên không được để trống")
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="Giá phải lớn hơn 0")
    
# Dữ liệu trả về cho Frontend
class ItemResponse(ItemCreate):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

# Demo State Schemas with Optimistic Concurrency Control (OCC)
class ExpenseState(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0, le=1_000_000_000_000)
    payer: str = Field(..., min_length=1, max_length=100)
    participants: List[str] = Field(..., min_length=1, max_length=200)

    @field_validator("participants")
    @classmethod
    def participants_are_unique(cls, value: List[str]) -> List[str]:
        if any(not participant.strip() for participant in value):
            raise ValueError("Tên thành viên không được để trống")
        if len(set(value)) != len(value):
            raise ValueError("Danh sách người tham gia không được trùng lặp")
        return value


class GroupState(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    members: List[str] = Field(..., min_length=1, max_length=200)
    balances: Dict[str, float] = Field(default_factory=dict)
    expenses: List[ExpenseState] = Field(default_factory=list, max_length=5000)

    @model_validator(mode="after")
    def validate_group_references(self):
        if any(not member.strip() for member in self.members):
            raise ValueError("Tên thành viên không được để trống")
        if len(set(self.members)) != len(self.members):
            raise ValueError("Danh sách thành viên không được trùng lặp")

        member_set = set(self.members)
        if not set(self.balances).issubset(member_set):
            raise ValueError("Số dư chứa thành viên không thuộc nhóm")
        for expense in self.expenses:
            if expense.payer not in member_set:
                raise ValueError("Người trả tiền phải thuộc nhóm")
            if not set(expense.participants).issubset(member_set):
                raise ValueError("Người tham gia khoản chi phải thuộc nhóm")
        return self


class DemoStateData(BaseModel):
    model_config = ConfigDict(extra="allow")

    groups: List[GroupState] = Field(
        default_factory=list,
        max_length=100,
        description="Danh sách các nhóm chi tiêu",
    )

class DemoStatePayload(BaseModel):
    expected_version: int = Field(..., ge=0, description="Phiên bản mong đợi của client (non-negative integer)")
    data: DemoStateData

class DemoStateResponse(BaseModel):
    id: int = 1
    version: int = Field(..., ge=0, description="Phiên bản hiện tại của dữ liệu (0 khi rỗng)")
    data: DemoStateData
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
