"""Flask todo application."""

import os
import sqlite3
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__, template_folder=str(Path(__file__).parent.parent / "templates"))
DATABASE = os.environ.get("DATABASE_PATH", "todos.db")

VALID_PRIORITIES = ("high", "medium", "low")


def get_db() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database schema and apply migrations."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(todos)")}
    if "priority" not in columns:
        conn.execute("ALTER TABLE todos ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")
    conn.commit()
    conn.close()


@app.route("/")
def index() -> str:
    """Display all todos with optional filtering and sorting."""
    filter_priority = request.args.get("priority", "")
    sort_by = request.args.get("sort", "created_at")

    if sort_by == "priority":
        order_clause = "CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 WHEN 'low' THEN 2 END ASC, created_at DESC"
    else:
        order_clause = "created_at DESC"

    conn = get_db()
    if filter_priority in VALID_PRIORITIES:
        todos = conn.execute(
            f"SELECT * FROM todos WHERE priority = ? ORDER BY {order_clause}",  # noqa: S608
            (filter_priority,),
        ).fetchall()
    else:
        todos = conn.execute(f"SELECT * FROM todos ORDER BY {order_clause}").fetchall()  # noqa: S608
    conn.close()

    return render_template(
        "index.html",
        todos=todos,
        filter_priority=filter_priority,
        sort_by=sort_by,
    )


@app.route("/add", methods=["POST"])
def add() -> str:
    """Add a new todo."""
    title = request.form.get("title", "").strip()
    priority = request.form.get("priority", "medium")
    if priority not in VALID_PRIORITIES:
        priority = "medium"
    if title:
        conn = get_db()
        conn.execute("INSERT INTO todos (title, priority) VALUES (?, ?)", (title, priority))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>")
def toggle(todo_id: int) -> str:
    """Toggle a todo's completed status."""
    conn = get_db()
    conn.execute("UPDATE todos SET completed = NOT completed WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>")
def delete(todo_id: int) -> str:
    """Delete a todo."""
    conn = get_db()
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# Initialize database on startup
init_db()
