import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status   # add Response
from app.core.cache import set_public_cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_owned_store, get_tenant_db, set_tenant_context
from app.core.audit import log_action
from app.database import get_db
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.product import ProductCreate, ProductOut, ProductPublicOut, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    current_user: User = Depends(get_current_user),
    store: Store = Depends(get_owned_store),
    db: AsyncSession = Depends(get_tenant_db),
):
    product = Product(store_id=store.id, **payload.model_dump())
    db.add(product)
    await db.flush()

    await log_action(
        db, table_name="products", record_id=str(product.id), action="CREATE", actor_id=str(current_user.id)
    )
    await db.commit()

    await set_tenant_context(db, current_user.id)
    await db.refresh(product)
    return product


@router.get("/me", response_model=list[ProductOut])
async def list_my_products(
    store: Store = Depends(get_owned_store),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(
        select(Product).where(Product.store_id == store.id).order_by(Product.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    current_user: User = Depends(get_current_user),
    store: Store = Depends(get_owned_store),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    # RLS already hides this row entirely if it belongs to someone else's
    # store, but we check store_id explicitly too — defense in depth, and
    # it gives a clean 404 instead of relying solely on the DB silently
    # returning zero rows.
    if product is None or product.store_id != store.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(product, field, value)

    await db.flush()
    await log_action(
        db,
        table_name="products",
        record_id=str(product.id),
        action="UPDATE",
        actor_id=str(current_user.id),
        changes=changes,
    )
    await db.commit()

    await set_tenant_context(db, current_user.id)
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    store: Store = Depends(get_owned_store),
    db: AsyncSession = Depends(get_tenant_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if product is None or product.store_id != store.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    await db.delete(product)
    await log_action(
        db, table_name="products", record_id=str(product_id), action="DELETE", actor_id=str(current_user.id)
    )
    await db.commit()


@router.get("/by-store-slug/{slug}", response_model=list[ProductPublicOut])
async def list_public_products(slug: str, response: Response, db: AsyncSession = Depends(get_db)):
    set_public_cache(response, s_maxage=30, swr=300)   # shorter: prices change more often
    """
    Public storefront listing — no auth required. Relies on the
    products_public_read RLS policy (is_active = true); no tenant
    context is set for this request.
    """
    store_result = await db.execute(select(Store).where(Store.slug == slug))
    store = store_result.scalar_one_or_none()
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    result = await db.execute(
        select(Product)
        .where(Product.store_id == store.id, Product.is_active.is_(True))
        .order_by(Product.created_at.desc())
    )
    return result.scalars().all()