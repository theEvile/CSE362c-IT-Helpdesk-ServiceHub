"""J3: locally provisioned administrator, authorization, CSRF and ticket CRUD."""
import hmac
import secrets
import sqlite3
from functools import wraps

import click
from flask import Blueprint, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("admin", __name__)
STATES = ("OPEN", "IN_PROGRESS", "RESOLVED")
ALLOWED = {
    "OPEN": {"OPEN", "IN_PROGRESS", "RESOLVED"},
    "IN_PROGRESS": {"IN_PROGRESS", "RESOLVED"},
    "RESOLVED": {"RESOLVED"},
}

def add_admin(username, password):
    username = username.strip()
    if not 3 <= len(username) <= 80:
        raise ValueError("Username must contain 3-80 characters.")
    if not 12 <= len(password) <= 128:
        raise ValueError("Password must contain 12-128 characters.")
    db = get_db()
    result = db.execute(
        "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
        (username, generate_password_hash(password)),
    )
    db.commit()
    return result.lastrowid

@click.command("create-admin")
@click.option("--username", prompt=True)
def create_admin_command(username):
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
    try:
        add_admin(username, password)
    except sqlite3.IntegrityError as exc:
        raise click.ClickException("Administrator username already exists") from exc
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo("Administrator created.")

def current_admin():
    admin_id = session.get("admin_id")
    if not isinstance(admin_id, int):
        return None
    return get_db().execute(
        "SELECT id, username FROM admins WHERE id = ?", (admin_id,)
    ).fetchone()

def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]

def valid_csrf():
    expected = session.get("csrf_token")
    supplied = request.headers.get("X-CSRF-Token", "")
    return isinstance(expected, str) and hmac.compare_digest(expected, supplied)

def admin_only(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        if current_admin() is None:
            return jsonify({"error": "Administrator authentication required."}), 401
        return handler(*args, **kwargs)
    return wrapped

def csrf_required(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        if not valid_csrf():
            return jsonify({"error": "Invalid or missing CSRF token."}), 403
        return handler(*args, **kwargs)
    return wrapped

@bp.get("/admin")
def admin_page():
    return render_template("admin.html")

@bp.get("/api/admin/session")
def admin_session():
    admin = current_admin()
    return jsonify({
        "authenticated": admin is not None,
        "username": admin["username"] if admin else None,
        "csrf_token": csrf_token(),
    })

@bp.post("/api/admin/login")
@csrf_required
def login():
    if not request.is_json:
        return jsonify({"error": "Expected JSON."}), 415
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Invalid JSON."}), 400
    username, password = body.get("username"), body.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Username and password are required."}), 400
    if len(username) > 80 or len(password) > 1024:
        return jsonify({"error": "Invalid credentials."}), 401
    admin = get_db().execute(
        "SELECT id, username, password_hash FROM admins WHERE username = ?",
        (username.strip(),),
    ).fetchone()
    if admin is None or not check_password_hash(admin["password_hash"], password):
        return jsonify({"error": "Invalid credentials."}), 401
    session.clear()
    session["admin_id"] = admin["id"]
    return jsonify({
        "authenticated": True,
        "username": admin["username"],
        "csrf_token": csrf_token(),
    })

@bp.post("/api/admin/logout")
@admin_only
@csrf_required
def logout():
    session.clear()
    return jsonify({"authenticated": False})

@bp.get("/api/tickets")
@admin_only
def list_tickets():
    status = request.args.get("status", "")
    if status and status not in STATES:
        return jsonify({"error": "Invalid status filter."}), 400
    rows = get_db().execute(
        """SELECT id, title, description, category, contact_email,
                  status, created_at, updated_at
           FROM tickets WHERE (? = '' OR status = ?) ORDER BY id DESC""",
        (status, status),
    ).fetchall()
    return jsonify({"tickets": [dict(row) for row in rows]})

@bp.get("/api/tickets/<int:ticket_id>")
@admin_only
def read_ticket(ticket_id):
    item = get_db().execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if item is None:
        return jsonify({"error": "Ticket not found."}), 404
    return jsonify({"ticket": dict(item)})

@bp.patch("/api/tickets/<int:ticket_id>")
@admin_only
@csrf_required
def update_ticket(ticket_id):
    if not request.is_json:
        return jsonify({"error": "Expected JSON."}), 415
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {"status"} or not isinstance(data["status"], str):
        return jsonify({"error": "Provide only a valid status."}), 400
    new_status = data["status"]
    if new_status not in STATES:
        return jsonify({"error": "Unknown ticket status."}), 400
    db = get_db()
    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if ticket is None:
        return jsonify({"error": "Ticket not found."}), 404
    if new_status not in ALLOWED[ticket["status"]]:
        return jsonify({"error": "Status cannot move backwards or reopen resolved tickets."}), 409
    if new_status != ticket["status"]:
        db.execute(
            """UPDATE tickets SET status = ?,
               updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?""",
            (new_status, ticket_id),
        )
        db.commit()
    updated = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return jsonify({"ticket": dict(updated)})

@bp.delete("/api/tickets/<int:ticket_id>")
@admin_only
@csrf_required
def delete_ticket(ticket_id):
    db = get_db()
    ticket = db.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if ticket is None:
        return jsonify({"error": "Ticket not found."}), 404
    if ticket["status"] != "RESOLVED":
        return jsonify({"error": "Only resolved tickets may be deleted."}), 409
    db.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    db.commit()
    return "", 204
