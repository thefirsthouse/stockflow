from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from warehouse.models import Product, Warehouse, StockItem, StockMovement
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

    async def create(
        self,
        product: int,
        warehouse: int,
        movement_type: str,
        quantity: int,
        comment: str | None = None,
    ) -> StockMovement:
        result = await self.db.execute(
            select(StockItem).where(
                StockItem.product == product,
                StockItem.warehouse == warehouse,
            )
        )
        stock_item = result.scalar_one_or_none()

        if movement_type == "OUT":
            if stock_item is None:
                raise ValueError(
                    f"Cannot create OUT movement: product {product} not found in warehouse {warehouse}"
                )
            if stock_item.quantity < quantity:
                raise ValueError(
                    f"Insufficient stock: available {stock_item.quantity}, requested {quantity}"
                )
            stock_item.quantity -= quantity
        else:
            if stock_item is None:
                stock_item = StockItem(
                    product=product,
                    warehouse=warehouse,
                    quantity=quantity,
                )
                self.db.add(stock_item)
            else:
                stock_item.quantity += quantity

        movement = StockMovement(
            product=product,
            warehouse=warehouse,
            movement_type=movement_type,
            quantity=quantity,
            comment=comment or "",
        )

        self.db.add(movement)
        await self.db.flush()

        return movement

    async def list(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[StockMovement]:
        result = await self.db.execute(
            select(StockMovement).offset(offset).limit(limit)
        )
        return list(result.scalars().all()
    )

    async def get(self, movement_id: int) -> StockMovement | None:
        result = await self.db.execute(
            select(StockMovement).where(
                StockMovement.id == movement_id
            )
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        movement: StockMovement,
        product: int | None = None,
        warehouse: int | None = None,
        movement_type: str | None = None,
        quantity: int | None = None,
        comment: str | None = None,
    ) -> StockMovement:
        original_product = movement.product
        original_warehouse = movement.warehouse
        original_type = movement.movement_type
        original_quantity = movement.quantity

        new_product = product if product is not None else original_product
        new_warehouse = warehouse if warehouse is not None else original_warehouse
        new_type = movement_type if movement_type is not None else original_type
        new_quantity = quantity if quantity is not None else original_quantity

        same_location = (original_product == new_product and original_warehouse == new_warehouse)

        if same_location:
            result = await self.db.execute(
                select(StockItem).where(
                    StockItem.product == original_product,
                    StockItem.warehouse == original_warehouse,
                )
            )
            stock_item = result.scalar_one_or_none()

            if stock_item:
                net_change = 0
                
                if original_type == "IN":
                    net_change -= original_quantity
                else:
                    net_change += original_quantity
                
                if new_type == "IN":
                    net_change += new_quantity
                else:
                    net_change -= new_quantity
                
                new_stock_level = stock_item.quantity + net_change
                
                if new_stock_level < 0:
                    raise ValueError(
                        f"Insufficient stock: current {stock_item.quantity}, net change {net_change}, would result in {new_stock_level}"
                    )
                
                stock_item.quantity = new_stock_level
            else:
                if new_type == "OUT":
                    raise ValueError(
                        f"Cannot update to OUT movement: product {new_product} not found in warehouse {new_warehouse}"
                    )
                stock_item = StockItem(
                    product=new_product,
                    warehouse=new_warehouse,
                    quantity=new_quantity,
                )
                self.db.add(stock_item)
        else:
            result = await self.db.execute(
                select(StockItem).where(
                    StockItem.product == original_product,
                    StockItem.warehouse == original_warehouse,
                )
            )
            original_stock_item = result.scalar_one_or_none()

            if original_stock_item:
                if original_type == "IN":
                    if original_stock_item.quantity < original_quantity:
                        raise ValueError(
                            f"Cannot update movement: would result in negative stock in original location"
                        )
                    original_stock_item.quantity -= original_quantity
                else:
                    original_stock_item.quantity += original_quantity

            result = await self.db.execute(
                select(StockItem).where(
                    StockItem.product == new_product,
                    StockItem.warehouse == new_warehouse,
                )
            )
            new_stock_item = result.scalar_one_or_none()

            if new_type == "OUT":
                if new_stock_item is None:
                    raise ValueError(
                        f"Cannot update to OUT movement: product {new_product} not found in warehouse {new_warehouse}"
                    )
                if new_stock_item.quantity < new_quantity:
                    raise ValueError(
                        f"Insufficient stock: available {new_stock_item.quantity}, requested {new_quantity}"
                    )
                new_stock_item.quantity -= new_quantity
            else:
                if new_stock_item is None:
                    new_stock_item = StockItem(
                        product=new_product,
                        warehouse=new_warehouse,
                        quantity=new_quantity,
                    )
                    self.db.add(new_stock_item)
                else:
                    new_stock_item.quantity += new_quantity

        if product is not None:
            movement.product = product
        if warehouse is not None:
            movement.warehouse = warehouse
        if movement_type is not None:
            movement.movement_type = movement_type
        if quantity is not None:
            movement.quantity = quantity
        if comment is not None:
            movement.comment = comment

        await self.db.flush()
        return movement

    async def delete(self, movement: StockMovement) -> None:
        movement_type = movement.movement_type

        result = await self.db.execute(
            select(StockItem).where(
                StockItem.product == movement.product,
                StockItem.warehouse == movement.warehouse,
            )
        )
        stock_item = result.scalar_one_or_none()

        if stock_item:
            if movement_type == "IN":
                if stock_item.quantity < movement.quantity:
                    raise ValueError(
                        f"Cannot delete IN movement: would result in negative stock (current: {stock_item.quantity}, movement: {movement.quantity})"
                    )
                stock_item.quantity -= movement.quantity
            else:
                stock_item.quantity += movement.quantity

        await self.db.delete(movement)
        await self.db.flush()
