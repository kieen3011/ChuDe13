from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from .database import Base

class Item(Base):
    __tablename__ = "items" # Lợi đổi tên bảng theo Chủ đề 13

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, default="Không có mô tả")
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

class DemoState(Base):
    __tablename__ = "demo_state"

    id = Column(Integer, primary_key=True, default=1)
    version = Column(Integer, nullable=False, default=1)
    # Using PostgreSQL JSONB with standard JSON fallback for portability
    data = Column(JSONB().with_variant(JSON, "sqlite"), nullable=False, default=dict)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
