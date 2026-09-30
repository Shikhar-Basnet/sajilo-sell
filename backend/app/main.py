from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import ORJSONResponse

from app.api.v1 import api_router
from app.config import settings
from app.database import get_db

# View docs directly against the backend (http://localhost:8000/docs), not
# through the Next.js /api rewrite: Swagger UI fetches openapi.json from an
# absolute "/openapi.json" path, which the rewrite (only active under
# /api/*) doesn't intercept — it 404s against the frontend instead of the
# backend when loaded via localhost:3000/api/docs.
#
# Docs describe every route and schema, including admin-only ones — fine
# for local dev, not something to expose once this is deployed publicly.
_docs_enabled = settings.ENVIRONMENT != "production"

tags_metadata = [
    {"name": "auth", "description": "Registration, login, and token refresh."},
    {"name": "stores", "description": "Store creation and lookup, including the public by-slug storefront endpoint."},
    {"name": "products", "description": "Product management for store owners, and public product listings."},
    {"name": "admin", "description": "Admin-only endpoints, gated by role-based access control."},
    {"name": "dashboard", "description": "Aggregated dashboard payloads."},
]

app = FastAPI(
    title="Sajilo Sell API",
    description="Backend API for Sajilo Sell — operating software for Nepal's social sellers.",
    version="0.1.0",
    openapi_tags=tags_metadata,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
    default_response_class=ORJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=86400,
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