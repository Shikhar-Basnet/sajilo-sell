from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import api_router
from app.database import get_db

app = FastAPI(title="Sajilo Sell API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://shikharbasnet.com.np",
        "https://www.shikharbasnet.com.np",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/v1")


@app.get("/")
def root():
    return {"message": "Sajilo Sell API is alive"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "sajilo-sell-backend"}


@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"status": "ok", "db_check": result.scalar()}