from tests.conftest import register_and_login


def test_register_success(client):
    resp = client.post("/auth/register", json={"email": "a@example.com", "password": "password123"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "a@example.com"
    assert "id" in body
    assert "hashed_password" not in body  # never leak the hash


def test_register_duplicate_email_rejected(client):
    client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    resp = client.post("/auth/register", json={"email": "dup@example.com", "password": "different123"})
    assert resp.status_code == 409


def test_register_invalid_email_rejected(client):
    resp = client.post("/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert resp.status_code == 422


def test_register_short_password_rejected(client):
    resp = client.post("/auth/register", json={"email": "short@example.com", "password": "short"})
    assert resp.status_code == 422


def test_login_success(client):
    client.post("/auth/register", json={"email": "b@example.com", "password": "password123"})
    resp = client.post("/auth/login", data={"username": "b@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "c@example.com", "password": "password123"})
    resp = client.post("/auth/login", data={"username": "c@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_nonexistent_user_rejected(client):
    resp = client.post("/auth/login", data={"username": "ghost@example.com", "password": "whatever123"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/jobs")
    assert resp.status_code == 401


def test_protected_route_rejects_garbage_token(client):
    resp = client.get("/jobs", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_me_endpoint_returns_current_user(client):
    headers = register_and_login(client, "me@example.com")
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"
