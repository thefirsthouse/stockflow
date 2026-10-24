import random
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from warehouse.models import Product, StockItem, StockMovement, Warehouse
from warehouse.schemas import StockMovementCreateSchema, StockTransferCreateSchema


class SKUGenerator:
    def __init__(self):
        pass

    def generate_sku(
        self,
        brand: str,
        model: str,
        color: Optional[str] = None,
    ) -> str:
        """
        Generate a SKU based on brand, model, and optional color.

        Format:
        BRAND-MODEL-COLOR-RANDOMNUMBER
        """
        brand_part = brand.upper().replace(" ", "")
        model_part = model.upper().replace(" ", "")
        color_part = color.upper().replace(" ", "") if color else ""

        random_number = random.randint(1000, 9999)

        return f"{brand_part}-{model_part}-{color_part}-{random_number}"


class StockMovementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_movement(
        self,
        data: StockMovementCreateSchema,
    ) -> StockMovement:
        async with self.db.begin():
            product = await self._get_product(data.product)
            warehouse = await self._get_warehouse(data.warehouse)

            stock_item = await self._get_stock_item_for_update(
                product.id,
                warehouse.id,
            )

            if data.movement_type == "IN":
                stock_item = await self._handle_in(
                    stock_item=stock_item,
                    product_id=product.id,
                    warehouse_id=warehouse.id,
                    quantity=data.quantity,
                )

            elif data.movement_type == "OUT":
                await self._handle_out(
                    stock_item=stock_item,
                    quantity=data.quantity,
                )

            movement = StockMovement(
                product=product.id,
                warehouse=warehouse.id,
                movement_type=data.movement_type,
                quantity=data.quantity,
                comment=data.comment,
            )

            self.db.add(movement)

            await self.db.flush()

            return movement

    async def transfer_stock(
        self,
        data: StockTransferCreateSchema,
    ) -> dict[str, StockMovement]:
        async with self.db.begin():
            product = await self._get_product(data.product)
            source_warehouse = await self._get_warehouse(data.source_warehouse)
            destination_warehouse = await self._get_warehouse(
                data.destination_warehouse
            )

            source_stock = await self._get_stock_item_for_update(
                product.id,
                source_warehouse.id,
            )
            await self._handle_out(source_stock, data.quantity)

            destination_stock = await self._get_stock_item_for_update(
                product.id,
                destination_warehouse.id,
            )
            await self._handle_in(
                stock_item=destination_stock,
                product_id=product.id,
                warehouse_id=destination_warehouse.id,
                quantity=data.quantity,
            )

            comment_suffix = f": {data.comment}" if data.comment else ""
            outgoing_movement = StockMovement(
                product=product.id,
                warehouse=source_warehouse.id,
                movement_type="OUT",
                quantity=data.quantity,
                comment=(
                    f"Transfer to warehouse {destination_warehouse.name} "
                    f"(ID {destination_warehouse.id}){comment_suffix}"
                ),
            )
            incoming_movement = StockMovement(
                product=product.id,
                warehouse=destination_warehouse.id,
                movement_type="IN",
                quantity=data.quantity,
                comment=(
                    f"Transfer from warehouse {source_warehouse.name} "
                    f"(ID {source_warehouse.id}){comment_suffix}"
                ),
            )
            self.db.add_all([outgoing_movement, incoming_movement])
            await self.db.flush()

            return {
                "outgoing_movement": outgoing_movement,
                "incoming_movement": incoming_movement,
            }

    async def _get_product(self, product_id: int) -> Product:
        result = await self.db.execute(
            select(Product)
            .where(Product.id == product_id)
            .with_for_update()
        )

        product = result.scalar_one_or_none()

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        return product

    async def _get_warehouse(self, warehouse_id: int) -> Warehouse:
        result = await self.db.execute(
            select(Warehouse)
            .where(Warehouse.id == warehouse_id)
            .with_for_update()
        )

        warehouse = result.scalar_one_or_none()

        if warehouse is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse not found",
            )

        return warehouse

    async def _get_stock_item_for_update(
        self,
        product_id: int,
        warehouse_id: int,
    ) -> StockItem | None:
        result = await self.db.execute(
            select(StockItem)
            .where(
                StockItem.product == product_id,
                StockItem.warehouse == warehouse_id,
            )
            .with_for_update()
        )

        return result.scalar_one_or_none()

    async def _handle_in(
        self,
        stock_item: StockItem | None,
        product_id: int,
        warehouse_id: int,
        quantity: int,
    ) -> StockItem:
        if stock_item is None:
            stock_item = StockItem(
                product=product_id,
                warehouse=warehouse_id,
                quantity=quantity,
            )

            self.db.add(stock_item)

        else:
            stock_item.quantity += quantity

        return stock_item

    async def _handle_out(
        self,
        stock_item: StockItem | None,
        quantity: int,
    ) -> None:
        if stock_item is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock",
            )

        if stock_item.quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock",
            )

        stock_item.quantity -= quantity
