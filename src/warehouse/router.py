from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from warehouse.dependencies import ProductDep, SessionDep, WarehouseDep
from warehouse.repository import ProductRepository, WarehouseRepository
from warehouse.schemas import (
    ProductCreateSchema,
    ProductReadSchema,
    ProductUpdateSchema,
    WarehouseCreateSchema,
    WarehouseReadSchema,
    WarehouseUpdateSchema,
)

warehouse_router = APIRouter(tags=["warehouse"])


def get_product_repository(db: SessionDep) -> ProductRepository:
    return ProductRepository(db)


def get_warehouse_repository(db: SessionDep) -> WarehouseRepository:
    return WarehouseRepository(db)


ProductRepositoryDep = Annotated[
    ProductRepository,
    Depends(get_product_repository),
]
WarehouseRepositoryDep = Annotated[
    WarehouseRepository,
    Depends(get_warehouse_repository),
]


@warehouse_router.get("/products", response_model=list[ProductReadSchema])
async def list_products(
    repository: ProductRepositoryDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return await repository.list(offset=offset, limit=limit)


@warehouse_router.post(
    "/products",
    response_model=ProductReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    product_data: ProductCreateSchema,
    repository: ProductRepositoryDep,
):
    existing_product = await repository.get_by_sku(product_data.sku)
    if existing_product is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with this SKU already exists",
        )

    return await repository.create(product_data)


@warehouse_router.get("/products/{product_id}", response_model=ProductReadSchema)
async def get_product(product: ProductDep):
    return product


@warehouse_router.patch("/products/{product_id}", response_model=ProductReadSchema)
async def update_product(
    product_data: ProductUpdateSchema,
    product: ProductDep,
    repository: ProductRepositoryDep,
):
    if product_data.sku is not None and product_data.sku != product.sku:
        existing_product = await repository.get_by_sku(product_data.sku)
        if existing_product is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product with this SKU already exists",
            )

    return await repository.update(product, product_data)


@warehouse_router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product(
    product: ProductDep,
    repository: ProductRepositoryDep,
) -> None:
    await repository.delete(product)


@warehouse_router.get("/warehouses", response_model=list[WarehouseReadSchema])
async def list_warehouses(
    repository: WarehouseRepositoryDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return await repository.list(offset=offset, limit=limit)


@warehouse_router.post(
    "/warehouses",
    response_model=WarehouseReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_warehouse(
    warehouse_data: WarehouseCreateSchema,
    repository: WarehouseRepositoryDep,
):
    existing_warehouse = await repository.get_by_name(warehouse_data.name)
    if existing_warehouse is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Warehouse with this name already exists",
        )

    return await repository.create(warehouse_data)


@warehouse_router.get("/warehouses/{warehouse_id}", response_model=WarehouseReadSchema)
async def get_warehouse(warehouse: WarehouseDep):
    return warehouse


@warehouse_router.patch(
    "/warehouses/{warehouse_id}",
    response_model=WarehouseReadSchema,
)
async def update_warehouse(
    warehouse_data: WarehouseUpdateSchema,
    warehouse: WarehouseDep,
    repository: WarehouseRepositoryDep,
):
    if warehouse_data.name is not None and warehouse_data.name != warehouse.name:
        existing_warehouse = await repository.get_by_name(warehouse_data.name)
        if existing_warehouse is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Warehouse with this name already exists",
            )

    return await repository.update(warehouse, warehouse_data)


@warehouse_router.delete(
    "/warehouses/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_warehouse(
    warehouse: WarehouseDep,
    repository: WarehouseRepositoryDep,
) -> None:
    await repository.delete(warehouse)
