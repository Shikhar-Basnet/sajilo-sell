from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.products import router as products_router
from app.api.v1.stores import router as stores_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(stores_router)
api_router.include_router(products_router)
api_router.include_router(admin_router)