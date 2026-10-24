from warehouse.models import Product, StockMovement, Warehouse


async def test_stock_movement_history_lists_events_and_filters(client, db_session):
    product_1 = Product(sku="APPLE-IPHONE", description="iPhone")
    product_2 = Product(sku="SAMSUNG-GALAXY", description="Galaxy")
    warehouse_1 = Warehouse(name="Main", location="Moscow")
    warehouse_2 = Warehouse(name="Reserve", location="Moscow")
    db_session.add_all([product_1, product_2, warehouse_1, warehouse_2])
    await db_session.flush()

    db_session.add_all(
        [
            StockMovement(
                product=product_1.id,
                warehouse=warehouse_1.id,
                movement_type="IN",
                quantity=10,
                comment="IN movement",
            ),
            StockMovement(
                product=product_1.id,
                warehouse=warehouse_1.id,
                movement_type="OUT",
                quantity=3,
                comment="OUT movement",
            ),
            StockMovement(
                product=product_2.id,
                warehouse=warehouse_1.id,
                movement_type="IN",
                quantity=8,
                comment="IN movement",
            ),
            StockMovement(
                product=product_1.id,
                warehouse=warehouse_2.id,
                movement_type="IN",
                quantity=5,
                comment="IN movement",
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/stock/movements")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 4
    assert all(
        {
            "id",
            "product",
            "warehouse",
            "movement_type",
            "quantity",
            "created_at",
            "comment",
        }
        <= movement.keys()
        for movement in history
    )

    by_warehouse = await client.get(
        "/stock/movements", params={"warehouse_id": warehouse_1.id}
    )
    assert by_warehouse.status_code == 200
    assert len(by_warehouse.json()) == 3
    assert all(
        movement["warehouse"] == warehouse_1.id
        for movement in by_warehouse.json()
    )

    by_product = await client.get(
        "/stock/movements", params={"product_id": product_1.id}
    )
    assert by_product.status_code == 200
    assert len(by_product.json()) == 3
    assert all(
        movement["product"] == product_1.id for movement in by_product.json()
    )

    by_type = await client.get(
        "/stock/movements", params={"movement_type": "OUT"}
    )
    assert by_type.status_code == 200
    assert len(by_type.json()) == 1
    assert by_type.json()[0]["movement_type"] == "OUT"

    by_combined_filters = await client.get(
        "/stock/movements",
        params={
            "warehouse_id": warehouse_1.id,
            "product_id": product_1.id,
            "movement_type": "IN",
        },
    )
    assert by_combined_filters.status_code == 200
    combined_history = by_combined_filters.json()
    assert len(combined_history) == 1
    assert combined_history[0]["warehouse"] == warehouse_1.id
    assert combined_history[0]["product"] == product_1.id
    assert combined_history[0]["movement_type"] == "IN"


async def test_stock_movement_history_rejects_invalid_type(client):
    response = await client.get(
        "/stock/movements", params={"movement_type": "TRANSFER"}
    )

    assert response.status_code == 422
