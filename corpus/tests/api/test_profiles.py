from pytest import mark
from realworld.api.core.auth import generate_jwt


#
# Profile Tests
#
def test_get_profile_dne_returns_404(client):
    usr = "mock-user"
    resp = client.get(f"/api/profiles/{usr}")
    assert resp.status_code == 404


@mark.parametrize("is_authenticated", [True, False])
@mark.parametrize("is_following", [True, False])
def test_get_profile(is_following, is_authenticated, client, add_user, add_user_follow):
    user1 = add_user(username="mock-user")
    user2 = add_user(username="mock-profile-user")

    if is_following:
        add_user_follow(user_id=user1["id"], following_user_id=user2["id"])

    headers = {}
    if is_authenticated:
        headers["Authorization"] = f"Token {generate_jwt(user1['id'])}"

    resp = client.get(f"/api/profiles/{user2['username']}", headers=headers)

    assert resp.status_code == 200
    assert resp.json["profile"] == {
        "username": user2["username"],
        "bio": user2["bio"],
        "image": user2["image"],
        "following": (is_following and is_authenticated),
    }


def test_follow_profile(client, add_user):
    user1 = add_user(username="mock-user")
    user2 = add_user(username="mock-profile-user")

    resp = client.post(
        f"/api/profiles/{user2['username']}/follow",
        headers={"Authorization": f"Token {generate_jwt(user1['id'])}"},
    )

    assert resp.status_code == 200
    assert resp.json["profile"] == {
        "username": user2["username"],
        "bio": user2["bio"],
        "image": user2["image"],
        "following": True,
    }


def test_unfollow_profile(client, add_user, add_user_follow):
    user1 = add_user(username="mock-user")
    user2 = add_user(username="mock-profile-user")
    add_user_follow(user_id=user1["id"], following_user_id=user2["id"])

    resp = client.delete(
        f"/api/profiles/{user2['username']}/follow",
        headers={"Authorization": f"Token {generate_jwt(user1['id'])}"},
    )

    assert resp.status_code == 200
    assert resp.json["profile"] == {
        "username": user2["username"],
        "bio": user2["bio"],
        "image": user2["image"],
        "following": False,
    }
