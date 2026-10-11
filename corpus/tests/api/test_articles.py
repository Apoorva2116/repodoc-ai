from realworld.api.core.auth import generate_jwt


#
# Article Tests
#
def test_get_articles(client, add_user, add_article):
    user = add_user()
    articles = [add_article(author_user_id=user["id"]) for _ in range(3)]

    resp = client.get("/api/articles")
    assert resp.status_code == 200
    assert resp.json["articlesCount"] == len(articles)
    assert len(resp.json["articles"]) == len(articles)

    # Ensure the articles are in most recent order
    for idx, article in enumerate(reversed(articles)):
        assert resp.json["articles"][idx] == {
            "slug": article["slug"],
            "title": article["title"],
            "description": article["description"],
            "body": article["body"],
            "tagList": article["tags"],
            "createdAt": article["created_date"],
            "updatedAt": article["updated_date"],
            "favorited": False,
            "favoritesCount": 0,
            "author": {
                "username": user["username"],
                "bio": user["bio"],
                "image": user["image"],
                "following": False,
            },
        }


def test_get_feed(client, add_user, add_article, add_user_follow):
    # setup
    user = add_user()
    folliwng_user, other_user = add_user(), add_user()
    add_user_follow(user_id=user["id"], following_user_id=folliwng_user["id"])

    # should not appear in feed
    add_article(author_user_id=user["id"])
    add_article(author_user_id=other_user["id"])

    # should appear in feed
    expected = [add_article(author_user_id=folliwng_user["id"]) for _ in range(3)]

    resp = client.get(
        "/api/articles/feed",
        headers={"Authorization": f"Token {generate_jwt(user['id'])}"},
    )
    assert resp.status_code == 200
    assert resp.json["articlesCount"] == len(expected)
    assert len(resp.json["articles"]) == len(expected)

    # Ensure the articles are in most recent order
    for idx, article in enumerate(reversed(expected)):
        assert resp.json["articles"][idx] == {
            "slug": article["slug"],
            "title": article["title"],
            "description": article["description"],
            "body": article["body"],
            "tagList": article["tags"],
            "createdAt": article["created_date"],
            "updatedAt": article["updated_date"],
            "favorited": False,
            "favoritesCount": 0,
            "author": {
                "username": folliwng_user["username"],
                "bio": folliwng_user["bio"],
                "image": folliwng_user["image"],
                "following": True,
            },
        }


def test_get_article(client, add_article):
    article = add_article()
    resp = client.get(f"/api/articles/{article['slug']}")
    assert resp.status_code == 200
    assert resp.json["article"]["slug"] == article["slug"]


def test_create_article_unauthenticated(client):
    payload = {
        "article": {
            "title": "How to Article",
            "description": "A test article.",
            "body": "This is just a test!",
            "tagList": ["test", "article"],
        }
    }
    resp = client.post("/api/articles", json=payload)
    assert resp.status_code == 401


def test_create_article(client, add_user):
    user = add_user()
    payload = {
        "article": {
            "title": "How to Article",
            "description": "A test article.",
            "body": "This is just a test!",
            "tagList": ["test", "article"],
        }
    }
    resp = client.post(
        "/api/articles",
        json=payload,
        headers={"Authorization": f"Token {generate_jwt(user['id'])}"},
    )
    assert resp.status_code == 200
    assert resp.json["article"]["title"] == payload["article"]["title"]


def test_update_article_unauthenticated(client, add_article):
    article = add_article()
    payload = {"article": {"title": "Updated Article"}}
    resp = client.put(f"/api/articles/{article['slug']}", json=payload)
    assert resp.status_code == 401


def test_update_article(client, add_user, add_article):
    user = add_user()
    article = add_article(author_user_id=user["id"])
    payload = {"article": {"title": "Updated Article"}}
    resp = client.put(
        f"/api/articles/{article['slug']}",
        json=payload,
        headers={"Authorization": f"Token {generate_jwt(user['id'])}"},
    )
    assert resp.status_code == 200
    assert resp.json["article"]["title"] == payload["article"]["title"]


def test_delete_article_unauthenticated(client, add_article):
    article = add_article()
    resp = client.delete(f"/api/articles/{article['slug']}")
    assert resp.status_code == 401


def test_delete_article(client, add_user, add_article):
    user = add_user()
    article = add_article(author_user_id=user["id"])
    resp = client.delete(
        f"/api/articles/{article['slug']}",
        headers={"Authorization": f"Token {generate_jwt(user['id'])}"},
    )
    assert resp.status_code == 200
    assert resp.json["message"] == "Article deleted"


#
# Article Favorties Tests
#
def test_favorite_article(client, add_user, add_article):
    user = add_user()
    article = add_article()
    resp = client.post(
        f"/api/articles/{article['slug']}/favorite",
        headers={"Authorization": f"Token {generate_jwt(user['id'])}"},
    )
    assert resp.status_code == 200
    assert resp.json["article"]["favorited"] is True


def test_unfavorite_article(client, add_user, add_article, add_article_favorite):
    user = add_user()
    article = add_article()
    add_article_favorite(article_id=article["id"], user_id=user["id"])
    resp = client.delete(
        f"/api/articles/{article['slug']}/favorite",
        headers={"Authorization": f"Token {generate_jwt(user['id'])}"},
    )
    assert resp.status_code == 200
    assert resp.json["article"]["favorited"] is False


#
# Article Comments Tests
#
def test_get_comments(client, add_user, add_article, add_article_comment):
    user1, user_2 = add_user(), add_user()
    article = add_article()
    comments = [
        add_article_comment(article_id=article["id"], commenter_user_id=user1["id"]),
        add_article_comment(article_id=article["id"], commenter_user_id=user_2["id"]),
    ]

    resp = client.get(f"/api/articles/{article['slug']}/comments")
    assert resp.status_code == 200
    assert resp.json["comments"] == [
        {
            "id": comment["id"],
            "createdAt": comment["created_date"],
            "updatedAt": comment["updated_date"],
            "body": comment["body"],
            "author": {
                "username": usr["username"],
                "bio": usr["bio"],
                "image": usr["image"],
                "following": False,
            },
        }
        for usr, comment in zip([user1, user_2], comments)
    ]


def test_create_comment(client, add_user, add_article):
    user = add_user()
    article = add_article()
    payload = {"comment": {"body": "A test comment."}}
    resp = client.post(
        f"/api/articles/{article['slug']}/comments",
        json=payload,
        headers={"Authorization": f"Token {generate_jwt(user['id'])}"},
    )
    assert resp.status_code == 200
    assert resp.json["comment"]["body"] == payload["comment"]["body"]


def test_delete_comment(client, add_user, add_article, add_article_comment):
    user = add_user()
    article = add_article()
    comment = add_article_comment(
        article_id=article["id"], commenter_user_id=user["id"]
    )
    resp = client.delete(
        f"/api/articles/{article['slug']}/comments/{comment['id']}",
        headers={"Authorization": f"Token {generate_jwt(user['id'])}"},
    )
    assert resp.status_code == 200
    assert resp.json["message"] == "Comment deleted"


#
# Article Comments Tests
#
def test_get_tags(client, add_article):
    add_article(tags=["mock"])
    add_article(tags=["test", "article"])

    resp = client.get("/api/tags")
    assert resp.status_code == 200
    assert resp.json["tags"] == [
        "mock",
        "test",
        "article",
    ]
