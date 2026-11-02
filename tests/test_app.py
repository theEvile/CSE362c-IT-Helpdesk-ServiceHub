import sqlite3

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}

def test_articles_can_be_searched(client):
    response = client.get("/api/articles?q=wi-fi")
    assert response.status_code == 200
    assert any("Wi-Fi" in article["title"] for article in response.json["articles"])

def test_articles_category_rejects_unknown_values(client):
    response = client.get("/api/articles?category=unknown")
    assert response.status_code == 400

def test_post_ticket_is_persisted(client, app):
    payload = {
        "title": "Unable to connect to Wi-Fi",
        "description": "Connection fails in the laboratory every morning.",
        "category": "wifi",
        "contact_email": "student@msa.edu.eg",
    }
    response = client.post("/api/tickets", json=payload)
    assert response.status_code == 201
    ticket_id = response.json["ticket"]["id"]
    assert response.json["ticket"]["status"] == "OPEN"
    with sqlite3.connect(app.config["DATABASE"]) as connection:
        saved = connection.execute("SELECT title, status FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    assert saved == (payload["title"], "OPEN")

def test_invalid_ticket_does_not_create_row(client, app):
    response = client.post("/api/tickets", json={
        "title": "x", "description": "short", "category": "wifi",
        "contact_email": "not-an-email",
    })
    assert response.status_code == 400
    with sqlite3.connect(app.config["DATABASE"]) as connection:
        count = connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        assert count == 0

def test_missing_content_type_is_rejected(client):
    response = client.post("/api/tickets", data="not-json")
    assert response.status_code == 415
