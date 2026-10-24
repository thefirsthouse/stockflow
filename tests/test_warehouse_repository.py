from warehouse.repository import ProductRepository, WarehouseRepository
from warehouse.schemas import (
    ProductCreateSchema,
    ProductUpdateSchema,
    WarehouseCreateSchema,
    WarehouseUpdateSchema,
)


async def test_product_repository_crud(db_session):
    repository = ProductRepository(db_session)

    product = await repository.create(
        ProductCreateSchema(brand="TestBrand", model="Model1", description="Test product"),
        sku="TESTBRAND-MODEL1-1234"
    )

    assert product.id is not None
    assert product.sku == "TESTBRAND-MODEL1-1234"
    assert await repository.get(product.id) == product
    assert await repository.get_by_sku("TESTBRAND-MODEL1-1234") == product
    assert await repository.list() == [product]

    updated_product = await repository.update(
        product,
        ProductUpdateSchema(description="Updated product"),
    )

    assert updated_product.description == "Updated product"

    await repository.delete(updated_product)

    assert await repository.get(product.id) is None
    assert await repository.list() == []


async def test_product_repository_supports_pagination(db_session):
    repository = ProductRepository(db_session)
    await repository.create(
        ProductCreateSchema(brand="Brand1", model="Model1", description=None),
        sku="BRAND1-MODEL1-1234"
    )
    second_product = await repository.create(
        ProductCreateSchema(brand="Brand2", model="Model2", description=None),
        sku="BRAND2-MODEL2-5678"
    )

    assert await repository.list(offset=1, limit=1) == [second_product]


async def test_warehouse_repository_crud(db_session):
    repository = WarehouseRepository(db_session)

    warehouse = await repository.create(
        WarehouseCreateSchema(name="Main", location="Moscow")
    )

    assert warehouse.id is not None
    assert warehouse.name == "Main"
    assert await repository.get(warehouse.id) == warehouse
    assert await repository.get_by_name("Main") == warehouse
    assert await repository.list() == [warehouse]

    updated_warehouse = await repository.update(
        warehouse,
        WarehouseUpdateSchema(name="North", location="Saint Petersburg"),
    )

    assert updated_warehouse.name == "North"
    assert updated_warehouse.location == "Saint Petersburg"
    assert await repository.get_by_name("Main") is None

    await repository.delete(updated_warehouse)

    assert await repository.get(warehouse.id) is None
    assert await repository.list() == []


async def test_warehouse_repository_supports_pagination(db_session):
    repository = WarehouseRepository(db_session)
    await repository.create(WarehouseCreateSchema(name="Main", location="Moscow"))
    second_warehouse = await repository.create(
        WarehouseCreateSchema(name="North", location="Saint Petersburg")
    )

    assert await repository.list(offset=1, limit=1) == [second_warehouse]
