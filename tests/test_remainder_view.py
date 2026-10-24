import pytest
from sqlalchemy import select

from warehouse.models import Product, Warehouse, StockItem
from warehouse.repository import StockItemRepository, ProductRepository, WarehouseRepository
from warehouse.schemas import ProductCreateSchema, WarehouseCreateSchema


@pytest.fixture
async def product1(db_session):
    repo = ProductRepository(db_session)
    product = await repo.create(
        ProductCreateSchema(
            brand="Apple",
            model="iPhone",
            color="Black",
            description="Smartphone"
        ),
        sku="APPLE-IPHONE-BLACK"
    )
    return product


@pytest.fixture
async def product2(db_session):
    repo = ProductRepository(db_session)
    product = await repo.create(
        ProductCreateSchema(
            brand="Samsung",
            model="Galaxy",
            color="White",
            description="Android Phone"
        ),
        sku="SAMSUNG-GALAXY-WHITE"
    )
    return product


@pytest.fixture
async def warehouse1(db_session):
    repo = WarehouseRepository(db_session)
    warehouse = await repo.create(
        WarehouseCreateSchema(name="Main Warehouse", location="Moscow")
    )
    return warehouse


@pytest.fixture
async def warehouse2(db_session):
    repo = WarehouseRepository(db_session)
    warehouse = await repo.create(
        WarehouseCreateSchema(name="Secondary Warehouse", location="Saint Petersburg")
    )
    return warehouse


@pytest.fixture
async def stock_item_repo(db_session):
    return StockItemRepository(db_session)


async def test_list_remainders_returns_all_items(
    stock_item_repo,
    product1,
    product2,
    warehouse1,
    warehouse2,
    db_session,
):
    stock1 = StockItem(product=product1.id, warehouse=warehouse1.id, quantity=100)
    stock2 = StockItem(product=product2.id, warehouse=warehouse1.id, quantity=50)
    stock3 = StockItem(product=product1.id, warehouse=warehouse2.id, quantity=75)
    
    db_session.add_all([stock1, stock2, stock3])
    await db_session.commit()

    remainders = await stock_item_repo.list_remainders()

    assert len(remainders) == 3
    
    remainder_1 = next(r for r in remainders if r["product_id"] == product1.id and r["warehouse_id"] == warehouse1.id)
    assert remainder_1["product_sku"] == "APPLE-IPHONE-BLACK"
    assert remainder_1["product_description"] == "Smartphone"
    assert remainder_1["warehouse_name"] == "Main Warehouse"
    assert remainder_1["warehouse_location"] == "Moscow"
    assert remainder_1["quantity"] == 100


async def test_list_remainders_filters_by_warehouse(
    stock_item_repo,
    product1,
    product2,
    warehouse1,
    warehouse2,
    db_session,
):
    stock1 = StockItem(product=product1.id, warehouse=warehouse1.id, quantity=100)
    stock2 = StockItem(product=product2.id, warehouse=warehouse1.id, quantity=50)
    stock3 = StockItem(product=product1.id, warehouse=warehouse2.id, quantity=75)
    
    db_session.add_all([stock1, stock2, stock3])
    await db_session.commit()

    remainders = await stock_item_repo.list_remainders(warehouse_id=warehouse1.id)

    assert len(remainders) == 2
    assert all(r["warehouse_id"] == warehouse1.id for r in remainders)
    assert all(r["warehouse_name"] == "Main Warehouse" for r in remainders)


async def test_list_remainders_filters_by_product(
    stock_item_repo,
    product1,
    product2,
    warehouse1,
    warehouse2,
    db_session,
):
    stock1 = StockItem(product=product1.id, warehouse=warehouse1.id, quantity=100)
    stock2 = StockItem(product=product2.id, warehouse=warehouse1.id, quantity=50)
    stock3 = StockItem(product=product1.id, warehouse=warehouse2.id, quantity=75)
    
    db_session.add_all([stock1, stock2, stock3])
    await db_session.commit()

    remainders = await stock_item_repo.list_remainders(product_id=product1.id)

    assert len(remainders) == 2
    assert all(r["product_id"] == product1.id for r in remainders)
    assert all(r["product_sku"] == "APPLE-IPHONE-BLACK" for r in remainders)


async def test_list_remainders_filters_by_both_warehouse_and_product(
    stock_item_repo,
    product1,
    product2,
    warehouse1,
    warehouse2,
    db_session,
):
    stock1 = StockItem(product=product1.id, warehouse=warehouse1.id, quantity=100)
    stock2 = StockItem(product=product2.id, warehouse=warehouse1.id, quantity=50)
    stock3 = StockItem(product=product1.id, warehouse=warehouse2.id, quantity=75)
    
    db_session.add_all([stock1, stock2, stock3])
    await db_session.commit()

    remainders = await stock_item_repo.list_remainders(
        warehouse_id=warehouse1.id,
        product_id=product1.id
    )

    assert len(remainders) == 1
    assert remainders[0]["product_id"] == product1.id
    assert remainders[0]["warehouse_id"] == warehouse1.id
    assert remainders[0]["quantity"] == 100


async def test_list_remainders_excludes_zero_quantity(
    stock_item_repo,
    product1,
    product2,
    warehouse1,
    db_session,
):
    stock1 = StockItem(product=product1.id, warehouse=warehouse1.id, quantity=100)
    stock2 = StockItem(product=product2.id, warehouse=warehouse1.id, quantity=0)
    
    db_session.add_all([stock1, stock2])
    await db_session.commit()

    remainders = await stock_item_repo.list_remainders()

    assert len(remainders) == 1
    assert remainders[0]["product_id"] == product1.id
    assert remainders[0]["quantity"] == 100


async def test_list_remainders_supports_pagination(
    stock_item_repo,
    product1,
    product2,
    warehouse1,
    warehouse2,
    db_session,
):
    stock1 = StockItem(product=product1.id, warehouse=warehouse1.id, quantity=100)
    stock2 = StockItem(product=product2.id, warehouse=warehouse1.id, quantity=50)
    stock3 = StockItem(product=product1.id, warehouse=warehouse2.id, quantity=75)
    
    db_session.add_all([stock1, stock2, stock3])
    await db_session.commit()

    page1 = await stock_item_repo.list_remainders(offset=0, limit=2)
    assert len(page1) == 2

    page2 = await stock_item_repo.list_remainders(offset=2, limit=2)
    assert len(page2) == 1

    all_ids = [r["id"] for r in page1] + [r["id"] for r in page2]
    assert len(set(all_ids)) == 3


async def test_list_remainders_returns_empty_list_when_no_stock(
    stock_item_repo,
    product1,
    warehouse1,
    db_session,
):
    remainders = await stock_item_repo.list_remainders()
    assert remainders == []
