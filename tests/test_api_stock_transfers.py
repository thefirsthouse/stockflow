from sqlalchemy import select

from warehouse.models import Product, StockItem, StockMovement, Warehouse


async def seed_transfer_data(db_session, source_quantity, destination_quantity=None):
    product = Product(sku="TRANSFER-TEST-PRODUCT", description="Test product")
    source = Warehouse(name="Transfer Source", location="Moscow")
    destination = Warehouse(name="Transfer Destination", location="Moscow")
    db_session.add_all([product, source, destination])
    await db_session.flush()

    source_stock = StockItem(
        product=product.id,
        warehouse=source.id,
        quantity=source_quantity,
    )
    db_session.add(source_stock)
    if destination_quantity is not None:
        db_session.add(
            StockItem(
                product=product.id,
                warehouse=destination.id,
                quantity=destination_quantity,
            )
        )

    await db_session.commit()
    return product, source, destination


async def test_stock_transfer_updates_stock_and_creates_movement_pair(
    client,
    db_session,
):
    product, source, destination = await seed_transfer_data(
        db_session,
        source_quantity=20,
        destination_quantity=4,
    )

    response = await client.post(
        "/stock/transfers",
        json={
            "product": product.id,
            "source_warehouse": source.id,
            "destination_warehouse": destination.id,
            "quantity": 7,
            "comment": "Restock branch",
        },
    )

    assert response.status_code == 201
    transfer = response.json()
    outgoing = transfer["outgoing_movement"]
    incoming = transfer["incoming_movement"]
    assert outgoing["product"] == product.id
    assert outgoing["warehouse"] == source.id
    assert outgoing["movement_type"] == "OUT"
    assert outgoing["quantity"] == 7
    assert "Transfer to warehouse" in outgoing["comment"]
    assert "Restock branch" in outgoing["comment"]
    assert incoming["product"] == product.id
    assert incoming["warehouse"] == destination.id
    assert incoming["movement_type"] == "IN"
    assert incoming["quantity"] == 7
    assert "Transfer from warehouse" in incoming["comment"]
    assert "Restock branch" in incoming["comment"]

    result = await db_session.execute(
        select(StockItem).where(
            StockItem.product == product.id,
            StockItem.warehouse.in_([source.id, destination.id]),
        )
    )
    quantities = {stock.warehouse: stock.quantity for stock in result.scalars()}
    assert quantities == {source.id: 13, destination.id: 11}

    result = await db_session.execute(
        select(StockMovement).where(StockMovement.product == product.id)
    )
    movements = list(result.scalars())
    assert len(movements) == 2
    assert {movement.movement_type for movement in movements} == {"IN", "OUT"}


async def test_stock_transfer_with_insufficient_stock_changes_nothing(
    client,
    db_session,
):
    product, source, destination = await seed_transfer_data(
        db_session,
        source_quantity=2,
        destination_quantity=5,
    )
    product_id = product.id
    source_id = source.id
    destination_id = destination.id

    response = await client.post(
        "/stock/transfers",
        json={
            "product": product_id,
            "source_warehouse": source_id,
            "destination_warehouse": destination_id,
            "quantity": 3,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient stock"

    result = await db_session.execute(
        select(StockItem).where(
            StockItem.product == product_id,
            StockItem.warehouse.in_([source_id, destination_id]),
        )
    )
    quantities = {stock.warehouse: stock.quantity for stock in result.scalars()}
    assert quantities == {source_id: 2, destination_id: 5}

    result = await db_session.execute(
        select(StockMovement).where(StockMovement.product == product_id)
    )
    assert list(result.scalars()) == []


async def test_stock_transfer_rejects_same_source_and_destination(client, db_session):
    product, source, _ = await seed_transfer_data(
        db_session,
        source_quantity=10,
    )

    response = await client.post(
        "/stock/transfers",
        json={
            "product": product.id,
            "source_warehouse": source.id,
            "destination_warehouse": source.id,
            "quantity": 1,
        },
    )

    assert response.status_code == 422
