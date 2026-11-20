from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base

class Item(Base):
    __tablename__ = "items" # Lợi đổi tên bảng theo Chủ đề 13

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, default="Không có mô tả")
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)