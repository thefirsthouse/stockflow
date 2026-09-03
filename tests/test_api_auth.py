async def test_register_user(client):
    response = await client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "Example",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    assert response.json() == {"msg": "User created"}


async def test_register_duplicate_username_returns_400(client):
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Example",
        "password": "password123",
    }

    assert (await client.post("/auth/register", json=payload)).status_code == 201

    duplicate_response = await client.post(
        "/auth/register",
        json={**payload, "email": "alice.duplicate@example.com"},
    )

    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Username already registered"


async def test_login_returns_access_token(client):
    await client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "Example",
            "password": "password123",
        },
    )

    response = await client.post(
        "/auth/token",
        data={"username": "alice", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


async def test_login_with_wrong_password_returns_401(client):
    await client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "Example",
            "password": "password123",
        },
    )

    response = await client.post(
        "/auth/token",
        data={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
