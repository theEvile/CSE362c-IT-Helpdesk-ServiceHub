"""J3 integration, negative, persistence, and security contract tests."""
import sqlite3
from helpdesk.admin import add_admin

PASSWORD = "CorrectHorseBattery2026!"
TICKET = {
    "title": "Laptop cannot connect to Wi-Fi",
    "description": "Wi-Fi disconnects every morning in the campus lab.",
    "category": "wifi",
    "contact_email": "student@msa.edu.eg",
}

def ticket(client):
    response = client.post("/api/tickets", json=TICKET)
    assert response.status_code == 201
    return response.json["ticket"]["id"]

def provision(app):
    with app.app_context():
        add_admin("itadmin", PASSWORD)

def login(client):
    csrf = client.get("/api/admin/session").json["csrf_token"]
    response = client.post(
        "/api/admin/login",
        json={"username": "itadmin", "password": PASSWORD},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    assert response.json["authenticated"]
    return response.json["csrf_token"]

def test_student_cannot_review_or_change_private_tickets(client):
    number = ticket(client)
    route = "/api/tickets/" + str(number)
    assert client.get("/api/tickets").status_code == 401
    assert client.get(route).status_code == 401
    assert client.patch(route, json={"status": "RESOLVED"}).status_code == 401
    assert client.delete(route).status_code == 401

def test_admin_password_is_hashed(client, app):
    provision(app)
    with sqlite3.connect(app.config["DATABASE"]) as db:
        stored = db.execute("SELECT password_hash FROM admins").fetchone()[0]
    assert stored != PASSWORD and PASSWORD not in stored
    csrf = login(client)
    assert csrf
    assert client.get("/api/admin/session").json["authenticated"]

def test_login_rejects_missing_csrf_and_wrong_password(client, app):
    provision(app)
    payload = {"username": "itadmin", "password": PASSWORD}
    assert client.post("/api/admin/login", json=payload).status_code == 403
    token = client.get("/api/admin/session").json["csrf_token"]
    assert client.post("/api/admin/login", json={
        "username": "itadmin", "password": "incorrect"
    }, headers={"X-CSRF-Token": token}).status_code == 401
    assert client.get("/api/admin/session").json["authenticated"] is False

def test_admin_can_read_and_progress_ticket_and_state_is_persistent(client, app):
    provision(app)
    number = ticket(client)
    csrf = login(client)
    route = "/api/tickets/" + str(number)
    assert client.get(route).json["ticket"]["status"] == "OPEN"
    assert client.patch(route, json={"status": "IN_PROGRESS"}, headers={"X-CSRF-Token": csrf}).status_code == 200
    assert client.patch(route, json={"status": "RESOLVED"}, headers={"X-CSRF-Token": csrf}).status_code == 200
    assert client.patch(route, json={"status": "OPEN"}, headers={"X-CSRF-Token": csrf}).status_code == 409
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT status FROM tickets WHERE id=?", (number,)).fetchone()[0] == "RESOLVED"
    assert client.get("/api/tickets?status=RESOLVED").json["tickets"][0]["id"] == number

def test_missing_csrf_rejects_patch_delete_logout(client, app):
    provision(app)
    number = ticket(client)
    login(client)
    route = "/api/tickets/" + str(number)
    assert client.patch(route, json={"status": "RESOLVED"}).status_code == 403
    assert client.delete(route).status_code == 403
    assert client.post("/api/admin/logout").status_code == 403

def test_invalid_status_and_json_are_rejected(client, app):
    provision(app)
    number = ticket(client)
    csrf = login(client)
    route = "/api/tickets/" + str(number)
    headers = {"X-CSRF-Token": csrf}
    assert client.patch(route, json={"status": "PENDING"}, headers=headers).status_code == 400
    assert client.patch(route, json={"status": 123}, headers=headers).status_code == 400
    assert client.patch(route, json={"status": "OPEN", "role": "admin"}, headers=headers).status_code == 400
    assert client.patch(route, data="invalid", headers=headers).status_code == 415
    assert client.get("/api/tickets?status=bad").status_code == 400

def test_only_resolved_tickets_can_be_deleted(client, app):
    provision(app)
    number = ticket(client)
    csrf = login(client)
    route = "/api/tickets/" + str(number)
    headers = {"X-CSRF-Token": csrf}
    assert client.delete(route, headers=headers).status_code == 409
    assert client.patch(route, json={"status": "RESOLVED"}, headers=headers).status_code == 200
    assert client.delete(route, headers=headers).status_code == 204
    assert client.get(route).status_code == 404
    with sqlite3.connect(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM tickets WHERE id=?", (number,)).fetchone()[0] == 0

def test_logout_revokes_current_browser_session(client, app):
    provision(app)
    ticket(client)
    csrf = login(client)
    assert client.post("/api/admin/logout", headers={"X-CSRF-Token": csrf}).status_code == 200
    assert client.get("/api/tickets").status_code == 401

def test_private_ticket_not_exposed_to_anonymous_user(client):
    number = ticket(client)
    response = client.get("/api/tickets/" + str(number))
    assert response.status_code == 401
    assert TICKET["contact_email"].encode("utf-8") not in response.data

def test_protected_endpoint_headers(client):
    response = client.get("/api/admin/session")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]

def test_resolved_ticket_cannot_regress_to_in_progress(client, app):
    provision(app)
    number = ticket(client)
    token = login(client)
    url = "/api/tickets/" + str(number)
    headers = {"X-CSRF-Token": token}
    client.patch(url, json={"status": "RESOLVED"}, headers=headers)
    assert client.patch(url, json={"status": "IN_PROGRESS"}, headers=headers).status_code == 409
