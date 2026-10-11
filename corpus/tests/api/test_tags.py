def test_get_tags(client):
    resp = client.get("/api/tags")
    assert resp.status_code == 200
