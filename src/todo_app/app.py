"""Flask todo application."""

import hmac
import logging
import os
import sqlite3
import time
from collections import defaultdict
from datetime import date
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from flask import Flask, Response, redirect, render_template, request, url_for

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder=str(Path(__file__).parent.parent / "templates"))
DATABASE = os.environ.get("DATABASE_PATH", "todos.db")
AUTH_USERNAME = os.environ.get("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD")

if not AUTH_PASSWORD:
    raise RuntimeError("AUTH_PASSWORD environment variable must be set to a non-empty value.")

_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX = 10     # max failed attempts per window
_failed_attempts: dict[str, list[float]] = defaultdict(list)


def _is_rate_limited(ip: str) -> bool:
    """Return True if the IP has exceeded the failed login rate limit."""
    now = time.monotonic()
    attempts = [t for t in _failed_attempts[ip] if now - t < _RATE_LIMIT_WINDOW]
    _failed_attempts[ip] = attempts
    return len(attempts) >= _RATE_LIMIT_MAX


def _rate_limit_response() -> Response | None:
    """Return a 429 Response if the current request IP is rate-limited, else None."""
    ip = request.remote_addr or "unknown"
    if _is_rate_limited(ip):
        logger.warning("Rate limit exceeded for IP %s", ip)
        return Response("Too many failed attempts.", 429)
    return None


def _credentials_valid() -> bool:
    """Return True if the current request carries valid Basic Auth credentials."""
    auth = request.authorization
    return (
        auth is not None
        and hmac.compare_digest(auth.username, AUTH_USERNAME)
        and hmac.compare_digest(auth.password, AUTH_PASSWORD)
    )


def require_auth(f: Callable) -> Callable:
    """Require HTTP Basic Auth for a route.

    Note: Deploy behind HTTPS to prevent credentials from being transmitted in plaintext.
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        if (err := _rate_limit_response()):
            return err
        ip = request.remote_addr or "unknown"
        if not _credentials_valid():
            _failed_attempts[ip].append(time.monotonic())
            logger.warning("Failed auth attempt from IP %s", ip)
            return Response(
                "Authentication required.",
                401,
                {"WWW-Authenticate": 'Basic realm="Todo App"'},
            )
        return f(*args, **kwargs)
    return decorated


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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TEXT,
            created_by TEXT NOT NULL DEFAULT ''
        )
    """)
    for column, definition in [("due_date", "TEXT"), ("created_by", "TEXT NOT NULL DEFAULT ''")]:
        try:
            conn.execute(f"ALTER TABLE todos ADD COLUMN {column} {definition}")  # noqa: S608
        except sqlite3.OperationalError:
            pass  # Column already exists
    # Assign legacy todos (created before auth was added) to the current user
    conn.execute(
        "UPDATE todos SET created_by = ? WHERE created_by = ''",
        (AUTH_USERNAME,),
    )
    conn.commit()
    conn.close()


@app.route("/")
@require_auth
def index() -> str:
    """Display all todos."""
    sort = request.args.get("sort", "created_at")
    order_by = "due_date ASC, created_at DESC" if sort == "due_date" else "created_at DESC"
    conn = get_db()
    username = request.authorization.username if request.authorization else AUTH_USERNAME
    todos = conn.execute(  # noqa: S608
        f"SELECT * FROM todos WHERE created_by = ? ORDER BY {order_by}", (username,)
    ).fetchall()
    conn.close()
    return render_template("index.html", todos=todos, today=date.today().isoformat(), sort=sort, username=username)


def _current_user() -> str:
    """Return the authenticated username from the current request.

    Raises RuntimeError if called outside an authenticated request context.
    """
    if not request.authorization:
        raise RuntimeError("_current_user called without an authenticated request")
    return request.authorization.username


def _check_todo_access(conn: sqlite3.Connection, todo_id: int) -> Response | None:
    """Return an error Response if the authenticated user cannot access the todo.

    Must only be called from routes protected by @require_auth, which already
    enforces rate limiting and credential validation before this is reached.

    Returns 404 if the todo does not exist, 403 if it exists but is not owned
    by the authenticated user.
    """
    username = _current_user()
    row = conn.execute("SELECT created_by FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        return Response("Not found", 404)
    if row["created_by"] != username:
        return Response("Forbidden", 403)
    return None


@app.route("/add", methods=["POST"])
@require_auth
def add() -> str:
    """Add a new todo."""
    title = request.form.get("title", "").strip()
    due_date = request.form.get("due_date", "").strip() or None
    if title:
        conn = get_db()
        conn.execute(
            "INSERT INTO todos (title, due_date, created_by) VALUES (?, ?, ?)",
            (title, due_date, _current_user()),
        )
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>")
@require_auth
def toggle(todo_id: int) -> str:
    """Toggle a todo's completed status."""
    conn = get_db()
    if (err := _check_todo_access(conn, todo_id)):
        conn.close()
        return err
    conn.execute("UPDATE todos SET completed = NOT completed WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/edit/<int:todo_id>", methods=["POST"])
@require_auth
def edit(todo_id: int) -> str:
    """Edit a todo's title and due date."""
    title = request.form.get("title", "").strip()
    due_date = request.form.get("due_date", "").strip() or None
    if title:
        conn = get_db()
        if (err := _check_todo_access(conn, todo_id)):
            conn.close()
            return err
        conn.execute(
            "UPDATE todos SET title = ?, due_date = ? WHERE id = ?",
            (title, due_date, todo_id),
        )
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>")
@require_auth
def delete(todo_id: int) -> str:
    """Delete a todo."""
    conn = get_db()
    if (err := _check_todo_access(conn, todo_id)):
        conn.close()
        return err
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# Initialize database on startup
init_db()
