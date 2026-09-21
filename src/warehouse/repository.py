from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from warehouse.models import Product, StockMovement, Warehouse, StockItem
from warehouse.schemas import (
    ProductCreateSchema,
    ProductUpdateSchema,
    WarehouseCreateSchema,
    WarehouseUpdateSchema,
)


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, offset: int = 0, limit: int = 100) -> list[Product]:
        result = await self.db.execute(select(Product).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def get(self, product_id: int) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.sku == sku))
        return result.scalar_one_or_none()

    async def create(self, data: ProductCreateSchema, sku: str | None = None) -> Product:
        payload = data.model_dump(exclude={"brand", "model", "color"})
        if sku is not None:
            payload["sku"] = sku
        product = Product(**payload)
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update(self, product: Product, data: ProductUpdateSchema) -> Product:
        for field, value in data.model_dump(exclude_unset=True).items():
            if field in {"brand", "model", "color"}:
                continue
            setattr(product, field, value)

        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        await self.db.delete(product)
        await self.db.commit()


class WarehouseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, offset: int = 0, limit: int = 100) -> list[Warehouse]:
        result = await self.db.execute(select(Warehouse).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def get(self, warehouse_id: int) -> Warehouse | None:
        result = await self.db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Warehouse | None:
        result = await self.db.execute(select(Warehouse).where(Warehouse.name == name))
        return result.scalar_one_or_none()

    async def create(self, data: WarehouseCreateSchema) -> Warehouse:
        warehouse = Warehouse(**data.model_dump())
        self.db.add(warehouse)
        await self.db.commit()
        await self.db.refresh(warehouse)
        return warehouse

    async def update(
        self,
        warehouse: Warehouse,
        data: WarehouseUpdateSchema,
    ) -> Warehouse:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(warehouse, field, value)

        await self.db.commit()
        await self.db.refresh(warehouse)
        return warehouse

    async def delete(self, warehouse: Warehouse) -> None:
        # remove associated stock items first
        await self.db.execute(
            select(StockItem).where(StockItem.warehouse == warehouse.id)
        )
        result = await self.db.execute(select(StockItem).where(StockItem.warehouse == warehouse.id))
        items = result.scalars().all()
        for it in items:
            await self.db.delete(it)

        await self.db.delete(warehouse)
        await self.db.commit()


class StockItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, offset: int = 0, limit: int = 100) -> list[StockItem]:
        result = await self.db.execute(select(StockItem).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def get(self, stockitem_id: int) -> StockItem | None:
        result = await self.db.execute(select(StockItem).where(StockItem.id == stockitem_id))
        return result.scalar_one_or_none()

    async def create(self, data: "StockItemCreateSchema") -> StockItem:
        # avoid circular import at module level
        from warehouse.schemas import StockItemCreateSchema

        stockitem = StockItem(**data.model_dump())
        self.db.add(stockitem)
        await self.db.commit()
        await self.db.refresh(stockitem)
        return stockitem

    async def update(self, stockitem: StockItem, data: "StockItemUpdateSchema") -> StockItem:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(stockitem, field, value)

        await self.db.commit()
        await self.db.refresh(stockitem)
        return stockitem

    async def delete(self, stockitem: StockItem) -> None:
        await self.db.delete(stockitem)
        await self.db.commit()


class StockMovementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, offset: int = 0, limit: int = 100) -> list["StockMovement"]:
        # avoid circular import at module level
        from warehouse.models import StockMovement

        result = await self.db.execute(select(StockMovement).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def get(self, movement_id: int) -> "StockMovement" | None:
        # avoid circular import at module level
        from warehouse.models import StockMovement

        result = await self.db.execute(
            select(StockMovement).where(StockMovement.id == movement_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: "StockMovementCreateSchema") -> "StockMovement":
        # avoid circular import at module level
        from warehouse.models import StockMovement
        from warehouse.schemas import StockMovementCreateSchema

        movement = StockMovement(**data.model_dump())
        self.db.add(movement)
        await self.db.commit()
        await self.db.refresh(movement)
        return movement

    async def update(
        self,
        movement: "StockMovement",
        data: "StockMovementUpdateSchema",
    ) -> "StockMovement":
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(movement, field, value)

        await self.db.commit()
        await self.db.refresh(movement)
        return movement

    async def delete(self, movement: "StockMovement") -> None:
        await self.db.delete(movement)
        await self.db.commit()
