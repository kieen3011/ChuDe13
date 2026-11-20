from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import items

# Tạo bảng trong CSDL nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Chủ Đề 13",
    description="Backend Code by Lợi",
    version="1.0.0"
)

# Cấu hình CORS cực kỳ quan trọng để Frontend (React/Vue/HTML) có thể gọi API mà không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong thực tế nên đổi thành URL của frontend (vd: http://localhost:3000)
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép mọi phương thức GET, POST, PUT, DELETE
    allow_headers=["*"],
)

# Nhúng router của Lợi vào app chính
app.include_router(items.router)

@app.get("/")
def root():
    return {"message": "Server backend Chủ Đề 13 đang chạy mượt mà!"}