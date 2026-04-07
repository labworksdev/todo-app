"""Flask todo application."""

import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__, template_folder=str(Path(__file__).parent.parent / "templates"))
DATABASE = os.environ.get("DATABASE_PATH", "todos.db")


def get_db() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index() -> str:
    """Display all todos."""
    conn = get_db()
    todos = conn.execute("SELECT * FROM todos ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("index.html", todos=todos)


@app.route("/add", methods=["POST"])
def add() -> str:
    """Add a new todo."""
    title = request.form.get("title", "").strip()
    if title:
        conn = get_db()
        conn.execute("INSERT INTO todos (title) VALUES (?)", (title,))
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


@app.route("/edit/<int:todo_id>", methods=["PATCH"])
def edit(todo_id: int) -> str:
    """Edit a todo's title."""
    title = request.form.get("title", "").strip()
    if not title:
        return jsonify({"error": "Title cannot be empty"}), 400
    conn = get_db()
    conn.execute("UPDATE todos SET title = ? WHERE id = ?", (title, todo_id))
    conn.commit()
    conn.close()
    return jsonify({"title": title})


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
