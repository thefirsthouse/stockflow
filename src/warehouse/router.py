from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from warehouse.dependencies import (ProductDep,
    SessionDep,
    WarehouseDep,
    StockItemDep,
    WarehouseDep,
)
from warehouse.repository import ProductRepository, WarehouseRepository, StockItemRepository
from warehouse.schemas import (
    StockItemCreateSchema,
    StockItemReadSchema,
    StockItemUpdateSchema,
    ProductCreateSchema,
    ProductReadSchema,
    ProductUpdateSchema,
    WarehouseCreateSchema,
    WarehouseReadSchema,
    WarehouseUpdateSchema,
    StockMovementCreateSchema,
    StockMovementReadSchema,
    RemainderReadSchema,
)
from warehouse.service import SKUGenerator, StockMovementService

warehouse_router = APIRouter(tags=["warehouse"])


def get_product_repository(db: SessionDep) -> ProductRepository:
    return ProductRepository(db)


def get_warehouse_repository(db: SessionDep) -> WarehouseRepository:
    return WarehouseRepository(db)


def get_stockitem_repository(db: SessionDep):
    from warehouse.repository import StockItemRepository

    return StockItemRepository(db)


ProductRepositoryDep = Annotated[
    ProductRepository,
    Depends(get_product_repository),
]
WarehouseRepositoryDep = Annotated[
    WarehouseRepository,
    Depends(get_warehouse_repository),
]

StockItemRepositoryDep = Annotated[
    StockItemRepository,
    Depends(get_stockitem_repository),
]

def get_stock_movement_service(
    db: SessionDep,
) -> StockMovementService:
    return StockMovementService(db)


StockMovementServiceDep = Annotated[
    StockMovementService,
    Depends(get_stock_movement_service),
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
    sku_generator: SKUGenerator = Depends(SKUGenerator),
):
    generated_sku = sku_generator.generate_sku(
        brand=product_data.brand,
        model=product_data.model,
        color=product_data.color,
    )

    existing_product = await repository.get_by_sku(generated_sku)
    if existing_product is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with this SKU already exists",
        )

    return await repository.create(product_data, sku=generated_sku)


@warehouse_router.get("/products/{product_id}", response_model=ProductReadSchema)
async def get_product(product: ProductDep):
    return product


@warehouse_router.patch("/products/{product_id}", response_model=ProductReadSchema)
async def update_product(
    product_data: ProductUpdateSchema,
    product: ProductDep,
    repository: ProductRepositoryDep,
):
    if product_data.brand is not None or product_data.model is not None:
        generated_sku = SKUGenerator().generate_sku(
            brand=(product_data.brand or product.sku.split("-")[0]),
            model=(product_data.model or product.sku.split("-")[1]),
            color=(product_data.color or ""),
        )
        if generated_sku != product.sku:
            existing_product = await repository.get_by_sku(generated_sku)
            if existing_product is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Product with this SKU already exists",
                )
            product.sku = generated_sku

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


# Stock items CRUD


@warehouse_router.get("/stock-items", response_model=list[StockItemReadSchema])
async def list_stock_items(
    repository: StockItemRepositoryDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return await repository.list(offset=offset, limit=limit)


@warehouse_router.post(
    "/stock-items",
    response_model=StockItemReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_stock_item(
    stockitem_data: StockItemCreateSchema,
    repository: StockItemRepositoryDep,
):
    return await repository.create(stockitem_data)


@warehouse_router.get("/stock-items/{stockitem_id}", response_model=StockItemReadSchema)
async def get_stock_item(stockitem: StockItemDep):
    return stockitem


@warehouse_router.patch("/stock-items/{stockitem_id}", response_model=StockItemReadSchema)
async def update_stock_item(
    stockitem_data: StockItemUpdateSchema,
    stockitem: StockItemDep,
    repository: StockItemRepositoryDep,
):
    return await repository.update(stockitem, stockitem_data)


@warehouse_router.delete(
    "/stock-items/{stockitem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_stock_item(
    stockitem: StockItemDep,
    repository: StockItemRepositoryDep,
) -> None:
    await repository.delete(stockitem)


# Remainders - Stock view with filters


@warehouse_router.get("/remainders", response_model=list[RemainderReadSchema])
async def list_remainders(
    repository: StockItemRepositoryDep,
    warehouse_id: Annotated[int | None, Query(ge=1)] = None,
    product_id: Annotated[int | None, Query(ge=1)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    remainders = await repository.list_remainders(
        warehouse_id=warehouse_id,
        product_id=product_id,
        offset=offset,
        limit=limit,
    )
    return remainders


@warehouse_router.post(
    "/stock/movements",
    response_model=StockMovementReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_stock_movement(
    movement_data: StockMovementCreateSchema,
    service: StockMovementServiceDep,
):
    return await service.create_movement(movement_data)
