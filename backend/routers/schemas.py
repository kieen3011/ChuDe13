from pydantic import BaseModel, Field
from typing import Optional

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