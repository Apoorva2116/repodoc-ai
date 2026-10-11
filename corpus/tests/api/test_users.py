#
# User Tests
#
def test_create_user(client):
    payload = {
        "user": {
            "username": "mock-user",
            "email": "mock-user@realworld.io",
            "password": "password",
        }
    }
    resp = client.post("/api/users", json=payload)
    assert resp.status_code == 200


def test_create_duplicate_user_returns_400(client, add_user):
    payload = {
        "user": {
            "username": "mock-user",
            "email": "mock-user@realworld.io",
            "password": "password",
        }
    }

    add_user(username="mock-user")

    resp = client.post("/api/users", json=payload)
    assert resp.status_code == 409
    assert resp.json["error"] == "A user with this username already exists."


def test_authenticate_user(client, add_user):
    user = add_user()
    resp = client.post(
        "/api/users/login",
        json={"user": {"email": user["email"], "password": user["password"]}},
    )

    assert resp.status_code == 200
    assert resp.json["user"]["email"] == user["email"]
    assert resp.json["user"]["username"] == user["username"]
    assert resp.json["user"]["bio"] == user["bio"]
    assert resp.json["user"]["image"] == user["image"]
    assert resp.json["user"]["token"] is not None


def test_get_current_user(client, add_user):
    user = add_user()
    resp = client.post(
        "/api/users/login",
        json={"user": {"email": user["email"], "password": "password"}},
    )
    jwt = resp.json["user"]["token"]

    resp = client.get(
        "/api/user",
        headers={"Authorization": f"Token {jwt}"},
    )
    assert resp.status_code == 200
    assert resp.json == {
        "user": {
            "email": user["email"],
            "username": user["username"],
            "bio": user["bio"],
            "image": user["image"],
        }
    }


def test_update_user(client, add_user):
    user = add_user(username="will-update", password="password")
    resp = client.post(
        "/api/users/login",
        json={"user": {"email": user["email"], "password": "password"}},
    )
    jwt = resp.json["user"]["token"]

    resp = client.put(
        "/api/user",
        headers={"Authorization": f"Token {jwt}"},
        json={
            "user": {
                "email": "updated@realworld.io",
                "bio": "updated bio",
                "image": "updated image",
            }
        },
    )

    assert resp.status_code == 200
    assert resp.json == {
        "user": {
            "username": user["username"],
            "email": "updated@realworld.io",
            "bio": "updated bio",
            "image": "updated image",
        }
    }
