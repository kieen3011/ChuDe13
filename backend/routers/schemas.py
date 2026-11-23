from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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

    class Config:
        from_attributes = True

# Demo State Schemas with Optimistic Concurrency Control (OCC)
class DemoStateData(BaseModel):
    groups: List[Dict[str, Any]] = Field(default_factory=list, description="Danh sách các nhóm chi tiêu")

class DemoStatePayload(BaseModel):
    expected_version: int = Field(..., ge=0, description="Phiên bản mong đợi của client (non-negative integer)")
    data: DemoStateData

class DemoStateResponse(BaseModel):
    id: int = 1
    version: int = Field(..., ge=0, description="Phiên bản hiện tại của dữ liệu (0 khi rỗng)")
    data: DemoStateData
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
