from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models
from . import items
from . import demo

# Tạo bảng trong CSDL nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Chủ Đề 13",
    description="Backend Code by Lợi - Chủ đề 13",
    version="1.0.0"
)

# Cấu hình CORS cực kỳ quan trọng để Frontend (React/Vue/HTML) có thể gọi API mà không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong thực tế nên đổi thành URL của frontend
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép mọi phương thức GET, POST, PUT, DELETE
    allow_headers=["*"],
)

# Nhúng các router vào app chính
app.include_router(items.router)
app.include_router(demo.router)

@app.get("/")
def root():
    return {"message": "Server backend Chủ Đề 13 đang chạy mượt mà!"}
