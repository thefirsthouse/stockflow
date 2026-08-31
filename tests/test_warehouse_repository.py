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
        ProductCreateSchema(sku="SKU-001", description="Test product")
    )

    assert product.id is not None
    assert product.sku == "SKU-001"
    assert await repository.get(product.id) == product
    assert await repository.get_by_sku("SKU-001") == product
    assert await repository.list() == [product]

    updated_product = await repository.update(
        product,
        ProductUpdateSchema(sku="SKU-002", description="Updated product"),
    )

    assert updated_product.sku == "SKU-002"
    assert updated_product.description == "Updated product"
    assert await repository.get_by_sku("SKU-001") is None

    await repository.delete(updated_product)

    assert await repository.get(product.id) is None
    assert await repository.list() == []


async def test_product_repository_supports_pagination(db_session):
    repository = ProductRepository(db_session)
    await repository.create(ProductCreateSchema(sku="SKU-001", description=None))
    second_product = await repository.create(
        ProductCreateSchema(sku="SKU-002", description=None)
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
