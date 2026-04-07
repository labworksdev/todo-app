"""Flask todo application."""

import logging
import os
import re
import secrets
import sqlite3
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, url_for

logger = logging.getLogger(__name__)

# Expected format for session owner IDs: 32 lowercase hex characters (secrets.token_hex(16))
_OWNER_ID_RE = re.compile(r"^[0-9a-f]{32}$")

app = Flask(__name__, template_folder=str(Path(__file__).parent.parent / "templates"))

# Session cookies are HMAC-signed by Flask (itsdangerous), so session data
# cannot be tampered with without knowing the secret key.
# SECRET_KEY must be a long random value set via environment variable in production.
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# Harden session cookie attributes to resist hijacking and CSRF
app.config["SESSION_COOKIE_HTTPONLY"] = True   # block JS access to the cookie
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # block cross-site POST requests
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("HTTPS", "false").lower() == "true"

DATABASE = os.environ.get("DATABASE_PATH", "todos.db")

PREDEFINED_TAGS = [
    {"name": "Work", "color": "#3B82F6"},
    {"name": "Personal", "color": "#22C55E"},
    {"name": "Shopping", "color": "#F97316"},
    {"name": "Health", "color": "#EF4444"},
]


def get_db() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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
            owner_id TEXT NOT NULL DEFAULT ''
        )
    """)
    # Add owner_id to existing databases that predate this column
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(todos)").fetchall()}
    if "owner_id" not in existing_columns:
        conn.execute("ALTER TABLE todos ADD COLUMN owner_id TEXT NOT NULL DEFAULT ''")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL DEFAULT '#6B7280'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todo_tags (
            todo_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (todo_id, tag_id),
            FOREIGN KEY (todo_id) REFERENCES todos(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)
    conn.commit()

    for tag in PREDEFINED_TAGS:
        conn.execute(
            "INSERT OR IGNORE INTO tags (name, color) VALUES (?, ?)",
            (tag["name"], tag["color"]),
        )
    conn.commit()
    conn.close()


def get_todos_with_tags(owner_id: str, filter_tag_id: int | None = None) -> list[dict]:
    """Fetch todos belonging to owner_id, optionally filtered by tag.

    Args:
        owner_id: Session owner identifier — only their todos are returned.
        filter_tag_id: If provided, only return todos that have this tag.

    Returns:
        List of todo dicts each containing a 'tags' key with associated tag dicts.
    """
    conn = get_db()
    if filter_tag_id is not None:
        todos = conn.execute(
            """
            SELECT t.* FROM todos t
            JOIN todo_tags tt ON t.id = tt.todo_id
            WHERE tt.tag_id = ? AND t.owner_id = ?
            ORDER BY t.created_at DESC
            """,
            (filter_tag_id, owner_id),
        ).fetchall()
    else:
        todos = conn.execute(
            "SELECT * FROM todos WHERE owner_id = ? ORDER BY created_at DESC",
            (owner_id,),
        ).fetchall()

    result = []
    for todo in todos:
        tags = conn.execute(
            """
            SELECT tg.* FROM tags tg
            JOIN todo_tags tt ON tg.id = tt.tag_id
            WHERE tt.todo_id = ?
            ORDER BY tg.name
            """,
            (todo["id"],),
        ).fetchall()
        todo_dict = dict(todo)
        todo_dict["tags"] = [dict(t) for t in tags]
        result.append(todo_dict)

    conn.close()
    return result


def get_csrf_token() -> str:
    """Return the session CSRF token, creating one if absent.

    Returns:
        The CSRF token string for the current session.
    """
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf() -> None:
    """Validate the CSRF token from the submitted form.

    Skipped when the app is running in testing mode.

    Raises:
        werkzeug.exceptions.HTTPException: 403 if the token is missing or invalid.
    """
    if app.config.get("TESTING"):
        return
    token = request.form.get("csrf_token", "")
    if not token or not secrets.compare_digest(token, session.get("csrf_token", "")):
        abort(403)


def get_session_owner() -> str:
    """Return a validated owner ID for the current session, creating one if absent or invalid.

    The stored value is checked against the expected 32-hex-char format produced by
    secrets.token_hex(16). An invalid or missing value is replaced with a fresh token
    so that malformed session data never propagates into authorization checks.

    Returns:
        A 32-character lowercase hex string identifying the current session owner.
    """
    owner_id = session.get("owner_id", "")
    if not _OWNER_ID_RE.match(owner_id):
        owner_id = secrets.token_hex(16)
        session["owner_id"] = owner_id
    return owner_id


# Role-based permission map: defines which actions each role may perform on todos.
_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "user": {"toggle", "delete"},
}


def get_session_role() -> str:
    """Return the role for the current session, validated against known roles.

    Falls back to 'user' if the session role is absent or not a recognised role,
    preventing privilege escalation via a tampered session value. Unexpected values
    are logged as warnings to aid detection of misconfigurations or attacks.

    Returns:
        A validated role string that exists in _ROLE_PERMISSIONS.
    """
    role = session.get("role", "user")
    if role not in _ROLE_PERMISSIONS:
        logger.warning("Unrecognised session role %r — falling back to 'user'", role)
        return "user"
    return role


def authorize_todo(todo_id: int, conn: sqlite3.Connection, action: str) -> None:
    """Verify a todo exists, belongs to the session owner, and the session role permits the action.

    Owner identity is read directly from the session so it cannot be overridden
    by the caller. Does not close the connection — the caller is responsible for
    closing it in all code paths (including when this function aborts).

    Args:
        todo_id: The ID of the todo to authorize.
        conn: An open database connection (caller manages lifecycle).
        action: The action being requested ('toggle' or 'delete').

    Raises:
        werkzeug.exceptions.HTTPException: 403 if the role does not permit the action,
            the todo is missing, or it is not owned by the session owner.
    """
    role = get_session_role()
    if action not in _ROLE_PERMISSIONS.get(role, set()):
        abort(403)
    owner_id = get_session_owner()
    # Validate owner_id format as a defence-in-depth measure before hitting the DB
    if not _OWNER_ID_RE.match(owner_id):
        abort(403)
    todo = conn.execute("SELECT owner_id FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if todo is None:
        abort(403)
    # Validate the stored owner_id format as a defence-in-depth measure
    if not _OWNER_ID_RE.match(todo["owner_id"]):
        abort(403)
    if todo["owner_id"] != owner_id:
        abort(403)


app.jinja_env.globals["csrf_token"] = get_csrf_token


@app.route("/")
def index() -> str:
    """Display all todos owned by the current session, optionally filtered by tag."""
    owner_id = get_session_owner()
    conn = get_db()
    all_tags = conn.execute("SELECT * FROM tags ORDER BY name").fetchall()

    # Validate the tag filter against known system tags so only legitimate IDs are used
    filter_tag_id: int | None = None
    filter_tag_id_str = request.args.get("tag")
    if filter_tag_id_str and filter_tag_id_str.isdigit():
        candidate = int(filter_tag_id_str)
        if conn.execute("SELECT id FROM tags WHERE id = ?", (candidate,)).fetchone():
            filter_tag_id = candidate

    conn.close()
    todos = get_todos_with_tags(owner_id, filter_tag_id)
    # Resolve authorization server-side so the template never compares raw IDs
    for todo in todos:
        todo["is_owner"] = _OWNER_ID_RE.match(todo["owner_id"]) is not None and todo["owner_id"] == owner_id
    return render_template("index.html", todos=todos, all_tags=all_tags, active_tag=filter_tag_id)


@app.route("/add", methods=["POST"])
def add() -> str:
    """Add a new todo owned by the current session with optional tags.

    Tags are system-wide predefined categories (Work, Personal, Shopping, Health)
    accessible to all sessions. Each submitted tag ID is validated to exist in the
    tags table before being associated with the new todo.
    """
    validate_csrf()
    owner_id = get_session_owner()
    # owner_id is derived from the HMAC-signed session cookie — it cannot be
    # externally injected — but we guard against an empty value defensively.
    if not owner_id:
        abort(403)
    title = request.form.get("title", "").strip()
    tag_ids = request.form.getlist("tags")
    if title:
        conn = get_db()
        cursor = conn.execute(
            "INSERT INTO todos (title, owner_id) VALUES (?, ?)",
            (title, owner_id),
        )
        todo_id = cursor.lastrowid
        for tag_id in tag_ids:
            if not tag_id.isdigit():
                continue
            # Validate the tag exists in the system tags table before associating
            valid = conn.execute("SELECT id FROM tags WHERE id = ?", (int(tag_id),)).fetchone()
            if valid:
                conn.execute(
                    "INSERT OR IGNORE INTO todo_tags (todo_id, tag_id) VALUES (?, ?)",
                    (todo_id, int(tag_id)),
                )
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
def toggle(todo_id: int) -> str:
    """Toggle a todo's completed status after verifying session ownership."""
    validate_csrf()
    conn = get_db()
    try:
        authorize_todo(todo_id, conn, action="toggle")
        conn.execute("UPDATE todos SET completed = NOT completed WHERE id = ?", (todo_id,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id: int) -> str:
    """Delete a todo after verifying session ownership."""
    validate_csrf()
    conn = get_db()
    try:
        authorize_todo(todo_id, conn, action="delete")
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("index"))


# Initialize database on startup
init_db()
