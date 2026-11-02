"""SQLite connection lifecycle and explicit database initialization."""

import sqlite3
from pathlib import Path

import click
from flask import current_app, g

SEED_ARTICLES = (
    ("Connect to campus Wi-Fi", "wifi", "Check your campus credentials, reconnect, and contact IT if access still fails."),
    ("Report a classroom computer issue", "hardware", "Record the lab or room number and describe the problem in a new ticket."),
    ("Software installation request", "software", "Provide the software name and device or laboratory location."),
    ("Reset your university account", "account", "Use the approved university recovery process or contact the IT desk."),
)

def get_db():
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db

def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()

def init_db():
    """Create missing tables and seed articles without erasing saved tickets."""
    connection = get_db()
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    connection.executescript(schema)
    for title, category, body in SEED_ARTICLES:
        existing = connection.execute(
            "SELECT 1 FROM knowledge_articles WHERE title = ?", (title,)
        ).fetchone()
        if existing is None:
            connection.execute(
                "INSERT INTO knowledge_articles (title, category, body) VALUES (?, ?, ?)",
                (title, category, body),
            )
    connection.commit()

@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("Database initialized (existing tickets preserved).")

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
