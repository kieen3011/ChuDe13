from sqlalchemy import Column, Integer, String, Float, Boolean
from .database import Base

class Item(Base):
    __tablename__ = "items" # Lá»£i Ä‘á»•i tÃªn báº£ng theo Chá»§ Ä‘á» 13

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, default="KhÃ´ng cÃ³ mÃ´ táº£")
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
