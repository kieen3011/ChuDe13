from fastapi import FastAPI
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models
from . import items
from . import demo

@asynccontextmanager
async def lifespan(_: FastAPI):
    # create_all only creates missing tables; it never drops or truncates data.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="API Chủ Đề 13",
    description="Backend Code by Lợi - Chủ đề 13",
    version="1.0.0",
    lifespan=lifespan,
)

# Same-origin deployment needs no CORS. Explicit origins can be enabled for a
# separately hosted frontend with CORS_ORIGINS=https://example.vercel.app,...
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )

# Nhúng các router vào app chính
app.include_router(items.router)
app.include_router(demo.router)

@app.get("/api/health", tags=["Health"])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


# Register the frontend last. FastAPI checks normal API routes before frontend
# files, and pyproject.toml keeps this frontend inside the Vercel Function.
frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.frontend("/", directory=frontend_dir, fallback=None)
