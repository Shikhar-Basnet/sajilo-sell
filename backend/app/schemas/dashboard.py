from pydantic import BaseModel

from app.schemas.product import ProductOut
from app.schemas.store import StoreOut


class SellerDashboardOut(BaseModel):
    store: StoreOut | None
    products: list[ProductOut]