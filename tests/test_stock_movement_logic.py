import pytest
from sqlalchemy import select

from warehouse.models import Product, Warehouse, StockItem, StockMovement
from warehouse.repository import StockMovementRepository, ProductRepository, WarehouseRepository
from warehouse.schemas import ProductCreateSchema, WarehouseCreateSchema


@pytest.fixture
async def sample_product(db_session):
    repo = ProductRepository(db_session)
    product = await repo.create(
        ProductCreateSchema(
            brand="TestBrand",
            model="TestModel",
            color="Red",
            description="Test Product"
        ),
        sku="TEST-SKU-001"
    )
    return product


@pytest.fixture
async def sample_warehouse(db_session):
    repo = WarehouseRepository(db_session)
    warehouse = await repo.create(
        WarehouseCreateSchema(name="Test Warehouse", location="Test Location")
    )
    return warehouse


@pytest.fixture
async def stock_movement_repo(db_session):
    return StockMovementRepository(db_session)


async def test_in_movement_creates_stock_item(
    stock_movement_repo,
    sample_product,
    sample_warehouse,
    db_session,
):
    movement = await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="IN",
        quantity=100,
        comment="Initial stock",
    )

    assert movement.id is not None
    assert movement.movement_type == "IN"
    assert movement.quantity == 100

    result = await db_session.execute(
        select(StockItem).where(
            StockItem.product == sample_product.id,
            StockItem.warehouse == sample_warehouse.id,
        )
    )
    stock_item = result.scalar_one_or_none()

    assert stock_item is not None
    assert stock_item.quantity == 100


async def test_in_movement_increases_existing_stock(
    stock_movement_repo,
    sample_product,
    sample_warehouse,
    db_session,
):
    stock_item = StockItem(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        quantity=50,
    )
    db_session.add(stock_item)
    await db_session.commit()

    await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="IN",
        quantity=30,
        comment="Additional stock",
    )

    await db_session.refresh(stock_item)
    assert stock_item.quantity == 80


async def test_out_movement_decreases_stock(
    stock_movement_repo,
    sample_product,
    sample_warehouse,
    db_session,
):
    stock_item = StockItem(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        quantity=100,
    )
    db_session.add(stock_item)
    await db_session.commit()

    movement = await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="OUT",
        quantity=25,
        comment="Sold items",
    )

    assert movement.movement_type == "OUT"
    assert movement.quantity == 25

    await db_session.refresh(stock_item)
    assert stock_item.quantity == 75


async def test_out_movement_fails_without_stock(
    stock_movement_repo,
    sample_product,
    sample_warehouse,
):
    with pytest.raises(ValueError) as exc_info:
        await stock_movement_repo.create(
            product=sample_product.id,
            warehouse=sample_warehouse.id,
            movement_type="OUT",
            quantity=10,
            comment="Should fail",
        )

    assert "Cannot create OUT movement" in str(exc_info.value)


async def test_out_movement_fails_with_insufficient_stock(
    stock_movement_repo,
    sample_product,
    sample_warehouse,
    db_session,
):
    stock_item = StockItem(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        quantity=10,
    )
    db_session.add(stock_item)
    await db_session.commit()

    with pytest.raises(ValueError) as exc_info:
        await stock_movement_repo.create(
            product=sample_product.id,
            warehouse=sample_warehouse.id,
            movement_type="OUT",
            quantity=20,
            comment="Should fail",
        )

    assert "Insufficient stock" in str(exc_info.value)


async def test_update_movement_quantity_updates_stock(
    stock_movement_repo,
    sample_product,
    sample_warehouse,
    db_session,
):
    movement = await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="IN",
        quantity=100,
        comment="Initial stock",
    )

    result = await db_session.execute(
        select(StockItem).where(
            StockItem.product == sample_product.id,
            StockItem.warehouse == sample_warehouse.id,
        )
    )
    stock_item = result.scalar_one()
    assert stock_item.quantity == 100

    await stock_movement_repo.update(movement, quantity=150)

    await db_session.refresh(stock_item)
    assert stock_item.quantity == 150


async def test_update_movement_type_from_in_to_out(
    stock_movement_repo,
    sample_product,
    sample_warehouse,
    db_session,
):
    await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="IN",
        quantity=100,
        comment="Initial stock",
    )

    movement = await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="IN",
        quantity=50,
        comment="Additional stock",
    )

    result = await db_session.execute(
        select(StockItem).where(
            StockItem.product == sample_product.id,
            StockItem.warehouse == sample_warehouse.id,
        )
    )
    stock_item = result.scalar_one()
    assert stock_item.quantity == 150

    await stock_movement_repo.update(movement, movement_type="OUT", quantity=30)

    await db_session.refresh(stock_item)
    assert stock_item.quantity == 70


async def test_delete_in_movement_decreases_stock(
    stock_movement_repo,
    sample_product,
    sample_warehouse,
    db_session,
):
    movement = await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="IN",
        quantity=100,
        comment="Initial stock",
    )

    result = await db_session.execute(
        select(StockItem).where(
            StockItem.product == sample_product.id,
            StockItem.warehouse == sample_warehouse.id,
        )
    )
    stock_item = result.scalar_one()
    assert stock_item.quantity == 100

    await stock_movement_repo.delete(movement)

    await db_session.refresh(stock_item)
    assert stock_item.quantity == 0


async def test_delete_out_movement_increases_stock(
    stock_movement_repo,
    sample_product,
    sample_warehouse,
    db_session,
):
    await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="IN",
        quantity=100,
        comment="Initial stock",
    )

    out_movement = await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="OUT",
        quantity=30,
        comment="Sale",
    )

    result = await db_session.execute(
        select(StockItem).where(
            StockItem.product == sample_product.id,
            StockItem.warehouse == sample_warehouse.id,
        )
    )
    stock_item = result.scalar_one()
    assert stock_item.quantity == 70

    await stock_movement_repo.delete(out_movement)

    await db_session.refresh(stock_item)
    assert stock_item.quantity == 100


async def test_delete_fails_when_would_cause_negative_stock(
    stock_movement_repo,
    sample_product,
    sample_warehouse,
    db_session,
):
    in_movement = await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="IN",
        quantity=100,
        comment="Initial stock",
    )

    await stock_movement_repo.create(
        product=sample_product.id,
        warehouse=sample_warehouse.id,
        movement_type="OUT",
        quantity=80,
        comment="Sale",
    )

    with pytest.raises(ValueError) as exc_info:
        await stock_movement_repo.delete(in_movement)

    assert "Cannot delete IN movement" in str(exc_info.value)
    assert "would result in negative stock" in str(exc_info.value)
