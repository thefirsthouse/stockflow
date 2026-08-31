from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from warehouse.models import Product, StockMovement, Warehouse
from warehouse.repository import ProductRepository, WarehouseRepository

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


async def get_product_by_id(
    product_id: Annotated[int, Path(gt=0)],
    db: SessionDep,
) -> Product:
    product = await ProductRepository(db).get(product_id)
    if product is None:
        raise not_found("Product not found")
    return product


async def get_warehouse_by_id(
    warehouse_id: Annotated[int, Path(gt=0)],
    db: SessionDep,
) -> Warehouse:
    warehouse = await WarehouseRepository(db).get(warehouse_id)
    if warehouse is None:
        raise not_found("Warehouse not found")
    return warehouse


async def get_stock_movement_by_id(
    movement_id: Annotated[int, Path(gt=0)],
    db: SessionDep,
) -> StockMovement:
    result = await db.execute(
        select(StockMovement).where(StockMovement.id == movement_id)
    )
    movement = result.scalar_one_or_none()
    if movement is None:
        raise not_found("Stock movement not found")
    return movement


ProductDep = Annotated[Product, Depends(get_product_by_id)]
WarehouseDep = Annotated[Warehouse, Depends(get_warehouse_by_id)]
StockMovementDep = Annotated[StockMovement, Depends(get_stock_movement_by_id)]
