from typing import Annotated

from fastapi import APIRouter, Depends

from repository import ProductRepository
from schemas import SProductAdd, SProduct, SProductId

router = APIRouter(
    prefix="/products",
    tags=["Товары"],
)

@router.post("")
async def add_product(
        product: Annotated[SProductAdd, Depends()],
) -> SProductId:
    product_id = await ProductRepository.add_one(product)
    return {"ok": True, "product_id": product_id}


@router.get("")
async def get_products() -> list[SProduct]:
    products = await ProductRepository.find_all()
    return products