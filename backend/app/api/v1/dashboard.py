from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tenant_db, require_role
from app.core.cache import set_no_store
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.dashboard import SellerDashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/seller", response_model=SellerDashboardOut)
async def seller_dashboard(
    response: Response,
    current_user: User = Depends(require_role("seller")),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Store + products in ONE request (saves a full round trip from Nepal)."""
    set_no_store(response)

    result = await db.execute(select(Store).where(Store.owner_id == current_user.id))
    store = result.scalar_one_or_none()

    products: list[Product] = []
    if store is not None:
        rows = await db.execute(
            select(Product).where(Product.store_id == store.id).order_by(Product.created_at.desc())
        )
        products = list(rows.scalars().all())

    return {"store": store, "products": products}