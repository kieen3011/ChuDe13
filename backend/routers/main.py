from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models
from . import items

# Táº¡o báº£ng trong CSDL náº¿u chÆ°a cÃ³
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Chá»§ Äá» 13",
    description="Backend Code by Lá»£i",
    version="1.0.0"
)

# Cáº¥u hÃ¬nh CORS cá»±c ká»³ quan trá»ng Ä‘á»ƒ Frontend (React/Vue/HTML) cÃ³ thá»ƒ gá»i API mÃ  khÃ´ng bá»‹ cháº·n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong thá»±c táº¿ nÃªn Ä‘á»•i thÃ nh URL cá»§a frontend (vd: http://localhost:3000)
    allow_credentials=True,
    allow_methods=["*"],  # Cho phÃ©p má»i phÆ°Æ¡ng thá»©c GET, POST, PUT, DELETE
    allow_headers=["*"],
)

# NhÃºng router cá»§a Lá»£i vÃ o app chÃ­nh
app.include_router(items.router)

@app.get("/")
def root():
    return {"message": "Server backend Chá»§ Äá» 13 Ä‘ang cháº¡y mÆ°á»£t mÃ !"}
