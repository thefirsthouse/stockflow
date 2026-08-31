async def test_product_crud(client):
    assert (await client.get("/products")).json() == []

    create_response = await client.post(
        "/products",
        json={"sku": "SKU-001", "description": "Test product"},
    )
    assert create_response.status_code == 201
    product = create_response.json()
    product_id = product["id"]
    assert product["sku"] == "SKU-001"

    duplicate_response = await client.post(
        "/products",
        json={"sku": "SKU-001", "description": "Duplicate"},
    )
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "Product with this SKU already exists"

    get_response = await client.get(f"/products/{product_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == product_id

    update_response = await client.patch(
        f"/products/{product_id}",
        json={"sku": "SKU-002", "description": "Updated product"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["sku"] == "SKU-002"
    assert update_response.json()["description"] == "Updated product"

    list_response = await client.get("/products", params={"offset": 0, "limit": 1})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    delete_response = await client.delete(f"/products/{product_id}")
    assert delete_response.status_code == 204

    missing_response = await client.get(f"/products/{product_id}")
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Product not found"


async def test_product_api_validation_errors(client):
    invalid_body_response = await client.post(
        "/products",
        json={"sku": "", "description": "Invalid product"},
    )
    invalid_query_response = await client.get(
        "/products",
        params={"offset": 0, "limit": 0},
    )

    assert invalid_body_response.status_code == 422
    assert invalid_query_response.status_code == 422


async def test_product_update_duplicate_sku_returns_409(client):
    first = await client.post(
        "/products",
        json={"sku": "SKU-001", "description": "First"},
    )
    await client.post(
        "/products",
        json={"sku": "SKU-002", "description": "Second"},
    )

    response = await client.patch(
        f"/products/{first.json()['id']}",
        json={"sku": "SKU-002"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Product with this SKU already exists"


async def test_warehouse_crud(client):
    assert (await client.get("/warehouses")).json() == []

    create_response = await client.post(
        "/warehouses",
        json={"name": "Main", "location": "Moscow"},
    )
    assert create_response.status_code == 201
    warehouse = create_response.json()
    warehouse_id = warehouse["id"]
    assert warehouse["name"] == "Main"

    duplicate_response = await client.post(
        "/warehouses",
        json={"name": "Main", "location": "Saint Petersburg"},
    )
    assert duplicate_response.status_code == 409
    assert (
        duplicate_response.json()["detail"]
        == "Warehouse with this name already exists"
    )

    get_response = await client.get(f"/warehouses/{warehouse_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == warehouse_id

    update_response = await client.patch(
        f"/warehouses/{warehouse_id}",
        json={"name": "North", "location": "Saint Petersburg"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "North"
    assert update_response.json()["location"] == "Saint Petersburg"

    list_response = await client.get("/warehouses", params={"offset": 0, "limit": 1})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    delete_response = await client.delete(f"/warehouses/{warehouse_id}")
    assert delete_response.status_code == 204

    missing_response = await client.get(f"/warehouses/{warehouse_id}")
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Warehouse not found"


async def test_warehouse_api_validation_errors(client):
    invalid_body_response = await client.post(
        "/warehouses",
        json={"name": "", "location": ""},
    )
    invalid_query_response = await client.get(
        "/warehouses",
        params={"offset": 0, "limit": 0},
    )

    assert invalid_body_response.status_code == 422
    assert invalid_query_response.status_code == 422


async def test_warehouse_update_duplicate_name_returns_409(client):
    first = await client.post(
        "/warehouses",
        json={"name": "Main", "location": "Moscow"},
    )
    await client.post(
        "/warehouses",
        json={"name": "North", "location": "Saint Petersburg"},
    )

    response = await client.patch(
        f"/warehouses/{first.json()['id']}",
        json={"name": "North"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Warehouse with this name already exists"
