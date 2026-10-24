from datetime import datetime

import pytest
from pydantic import ValidationError

from warehouse.schemas import (
    MovementType,
    ProductCreateSchema,
    ProductReadSchema,
    ProductUpdateSchema,
    StockMovementCreateSchema,
    StockMovementReadSchema,
    StockTransferCreateSchema,
    WarehouseCreateSchema,
    WarehouseReadSchema,
    WarehouseUpdateSchema,
)


def test_product_schemas_validate_valid_payloads():
    create_schema = ProductCreateSchema(brand="TestBrand", model="TestModel", description="Test product")
    update_schema = ProductUpdateSchema(description=None)
    read_schema = ProductReadSchema(id=1, sku="SKU-001", description="Test product")

    assert create_schema.brand == "TestBrand"
    assert update_schema.description is None
    assert read_schema.id == 1


def test_product_schema_rejects_empty_sku():
    with pytest.raises(ValidationError):
        ProductCreateSchema(brand="", model="TestModel", description="Test product")


def test_warehouse_schemas_validate_valid_payloads():
    create_schema = WarehouseCreateSchema(name="Main", location="Moscow")
    update_schema = WarehouseUpdateSchema(location="Saint Petersburg")
    read_schema = WarehouseReadSchema(id=1, name="Main", location="Moscow")

    assert create_schema.name == "Main"
    assert update_schema.location == "Saint Petersburg"
    assert read_schema.id == 1


def test_warehouse_schema_rejects_empty_name_and_location():
    with pytest.raises(ValidationError):
        WarehouseCreateSchema(name="", location="")


def test_stock_movement_schemas_validate_valid_payloads():
    created_at = datetime.now()
    create_schema = StockMovementCreateSchema(
        product=1,
        warehouse=1,
        movement_type="IN",
        quantity=5,
        comment="Initial stock",
    )
    read_schema = StockMovementReadSchema(
        id=1,
        product=1,
        warehouse=1,
        movement_type=MovementType.in_,
        quantity=5,
        created_at=created_at,
        comment="Initial stock",
    )

    assert create_schema.movement_type == MovementType.in_
    assert read_schema.created_at == created_at


def test_stock_movement_schema_rejects_invalid_values():
    with pytest.raises(ValidationError):
        StockMovementCreateSchema(
            product=0,
            warehouse=0,
            movement_type="transfer",
            quantity=0,
        )


def test_stock_transfer_schema_validates_warehouses_and_quantity():
    transfer = StockTransferCreateSchema(
        product=1,
        source_warehouse=1,
        destination_warehouse=2,
        quantity=5,
    )

    assert transfer.source_warehouse == 1
    assert transfer.destination_warehouse == 2
    assert transfer.quantity == 5

    with pytest.raises(ValidationError):
        StockTransferCreateSchema(
            product=1,
            source_warehouse=1,
            destination_warehouse=1,
            quantity=5,
        )

    with pytest.raises(ValidationError):
        StockTransferCreateSchema(
            product=1,
            source_warehouse=1,
            destination_warehouse=2,
            quantity=0,
        )
