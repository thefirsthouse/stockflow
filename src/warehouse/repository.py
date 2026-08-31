from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from warehouse.models import Product, Warehouse
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

    async def create(self, data: ProductCreateSchema) -> Product:
        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update(self, product: Product, data: ProductUpdateSchema) -> Product:
        for field, value in data.model_dump(exclude_unset=True).items():
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
        await self.db.delete(warehouse)
        await self.db.commit()
