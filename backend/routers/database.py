from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Sử dụng SQLite để chạy cục bộ mượt mà, không cần cài server
SQLALCHEMY_DATABASE_URL = "sqlite:///./topic13_app.db"

# check_same_thread=False cần thiết cho SQLite trong FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Hàm tạo session an toàn, tự động đóng kết nối dù có lỗi xảy ra
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()