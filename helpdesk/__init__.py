"""Campus IT Helpdesk starter: public knowledge base and ticket submission."""

import re
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from .db import get_db, init_app

CATEGORIES = {"wifi", "hardware", "software", "account"}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=str(Path(app.instance_path) / "helpdesk.sqlite3"),
        JSON_SORT_KEYS=False,
    )
    if test_config is not None:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    init_app(app)

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/articles")
    def list_articles():
        search = request.args.get("q", "").strip().lower()
        category = request.args.get("category", "").strip().lower()
        if len(search) > 100:
            return jsonify({"error": "Search query is too long."}), 400
        if category and category not in CATEGORIES:
            return jsonify({"error": "Unknown article category."}), 400
        pattern = "%" + search + "%"
        rows = get_db().execute(
            """SELECT id, title, category, body FROM knowledge_articles
               WHERE (? = '' OR lower(title) LIKE ? OR lower(body) LIKE ?)
                 AND (? = '' OR category = ?)
               ORDER BY title""",
            (search, pattern, pattern, category, category),
        ).fetchall()
        return jsonify({"articles": [dict(row) for row in rows]})

    @app.post("/api/tickets")
    def create_ticket():
        if not request.is_json:
            return jsonify({"error": "Expected a JSON request body."}), 415
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Invalid JSON object."}), 400
        fields = ("title", "description", "category", "contact_email")
        if any(not isinstance(payload.get(field), str) for field in fields):
            return jsonify({"error": "All ticket fields must be text."}), 400
        title = payload["title"].strip()
        description = payload["description"].strip()
        category = payload["category"].strip().lower()
        email = payload["contact_email"].strip()
        if not 5 <= len(title) <= 120:
            return jsonify({"error": "Title must contain 5–120 characters."}), 400
        if not 10 <= len(description) <= 2000:
            return jsonify({"error": "Description must contain 10–2000 characters."}), 400
        if category not in CATEGORIES:
            return jsonify({"error": "Unknown ticket category."}), 400
        if len(email) > 254 or EMAIL_PATTERN.fullmatch(email) is None:
            return jsonify({"error": "Provide a valid contact email."}), 400
        db = get_db()
        cursor = db.execute(
            """INSERT INTO tickets (title, description, category, contact_email)
               VALUES (?, ?, ?, ?)""",
            (title, description, category, email),
        )
        db.commit()
        return jsonify({"ticket": {"id": cursor.lastrowid, "status": "OPEN"}}), 201

    return app
