from typing import Optional
from pydantic import BaseModel


class SProductAdd(BaseModel): # Для ввода в БД (чтобы не указывать id)
    name: str
    description: Optional[str] = None
    ozon_id: int


class SProduct(SProductAdd): # Для вывода из БД (чтобы был id на выходе)
    id: int


class SProductId(BaseModel): # Для ответа на запрос о добавлении товара
    ok: bool = True
    product_id: int