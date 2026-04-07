"""Flask todo application."""

import datetime
import functools
import hashlib
import hmac
import logging
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Callable

from flask import Flask, redirect, render_template, request, session, url_for
from itsdangerous import BadSignature, URLSafeSerializer

logger = logging.getLogger(__name__)

_secret_key = os.environ.get("SECRET_KEY")
if not _secret_key:
    raise RuntimeError("SECRET_KEY environment variable must be set before starting the app.")

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent.parent / "templates"),
    static_folder=str(Path(__file__).parent.parent / "static"),
)
app.secret_key = _secret_key
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(hours=8),
)

DATABASE = os.environ.get("DATABASE_PATH", "todos.db")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
if not ADMIN_USERNAME:
    raise RuntimeError("ADMIN_USERNAME environment variable must be set before starting the app.")

# ADMIN_PASSWORD_HASH must be a PBKDF2-SHA256 hash in the format
# produced by scripts/generate_password_hash.py: "<iterations>:<salt_hex>:<hash_hex>"
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")
if not ADMIN_PASSWORD_HASH:
    raise RuntimeError("ADMIN_PASSWORD_HASH environment variable must be set before starting the app.")

# Signer for server-side session tokens — independent of Flask's cookie signer.
_token_signer = URLSafeSerializer(_secret_key, salt="session-token")

# Derived key used to HMAC raw tokens before storing them server-side.
# Separating this from _secret_key prevents cross-purpose key reuse.
_token_store_key: bytes = hmac.new(
    _secret_key.encode(), b"token-store-v1", digestmod=hashlib.sha256
).digest()

# Server-side store of HMAC-SHA256 digests of valid tokens.  Raw tokens are
# never stored — only their digests — so the set cannot leak token values.
# Membership checks are O(1) hash-table lookups on fixed-length byte strings,
# with no manual iteration or timing-variable loops.
_valid_session_tokens: set[bytes] = set()


def _token_digest(raw_token: str) -> bytes:
    """Return the HMAC-SHA256 digest of raw_token under the token-store key."""
    return hmac.new(_token_store_key, raw_token.encode(), digestmod=hashlib.sha256).digest()

# Rate-limiting store: maps IP -> (failure_count, lockout_until).
_LOGIN_MAX_ATTEMPTS: int = int(os.environ.get("LOGIN_MAX_ATTEMPTS", "5"))
_LOGIN_LOCKOUT_MINUTES: int = int(os.environ.get("LOGIN_LOCKOUT_MINUTES", "15"))
_failed_logins: dict[str, tuple[int, datetime.datetime]] = {}


def _constant_time_equal(a: str, b: str) -> bool:
    """Timing-safe string comparison backed by hmac.compare_digest.

    hmac.compare_digest is part of the Python standard library since 3.3 and
    does not depend on the secrets module, making it available in restricted
    environments where secrets may be unavailable.
    """
    return hmac.compare_digest(a.encode(), b.encode())


def _check_rate_limit(ip: str) -> bool:
    """Return True when the IP is allowed to attempt login, False when locked out."""
    entry = _failed_logins.get(ip)
    if entry is None:
        return True
    failures, lockout_until = entry
    if failures >= _LOGIN_MAX_ATTEMPTS and datetime.datetime.now(datetime.timezone.utc) < lockout_until:
        return False
    if datetime.datetime.now(datetime.timezone.utc) >= lockout_until:
        # Lockout expired — reset the counter.
        del _failed_logins[ip]
    return True


def _record_failed_login(ip: str) -> None:
    """Increment the failure counter for an IP and set a lockout if the limit is reached."""
    entry = _failed_logins.get(ip)
    failures = (entry[0] if entry else 0) + 1
    lockout_until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=_LOGIN_LOCKOUT_MINUTES)
    _failed_logins[ip] = (failures, lockout_until)


def _clear_failed_logins(ip: str) -> None:
    """Remove the failure record for an IP after a successful login."""
    _failed_logins.pop(ip, None)


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2-SHA256 hash.

    The stored hash format is "<iterations>:<salt_hex>:<hash_hex>", which makes
    verification self-contained — the iteration count never needs to match an
    application-level constant, so it can be increased without breaking old hashes.
    """
    try:
        iterations_str, salt_hex, key_hex = stored_hash.split(":", 2)
        iterations = int(iterations_str)
        if iterations < 1:
            return False
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
        return hmac.compare_digest(key, bytes.fromhex(key_hex))
    except (ValueError, TypeError):
        return False


def _is_valid_admin_session() -> bool:
    """Return True only when all authorization conditions pass atomically.

    All checks always run regardless of intermediate results so that no
    timing side-channel can reveal which specific condition failed.
    session.new is False for any established session; a new/empty session
    can never carry valid admin credentials.
    """
    # Token digest check runs first — it is the most critical cryptographic
    # condition and must execute before any other check.
    signed_token = session.get("token") or ""
    try:
        raw_token: str = _token_signer.loads(signed_token) if signed_token else ""
    except BadSignature:
        raw_token = ""
    # Compute the digest of the candidate token and check set membership in O(1).
    # No iteration loop — timing is constant regardless of set size or token position.
    token_ok = bool(raw_token) and _token_digest(raw_token) in _valid_session_tokens
    # Remaining checks all execute unconditionally so no condition leaks which failed.
    username = session.get("username", "")
    username_ok = _constant_time_equal(username, ADMIN_USERNAME)
    session_established = not session.new
    is_permanent = session.permanent
    role_ok = session.get("role") == "admin"
    return session_established and is_permanent and username_ok and role_ok and token_ok


def admin_required(f: Callable) -> Callable:
    """Restrict access to admin-role sessions with a valid signed server-side token."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):  # type: ignore[no-untyped-def]
        if not _is_valid_admin_session():
            session.clear()
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def _get_authorized_todo(conn: sqlite3.Connection, todo_id: int) -> sqlite3.Row | None:
    """Return the todo row only when the session is a valid admin and owns the resource.

    All identity checks happen before the database is queried:
    1. _is_valid_admin_session() verifies role, username == ADMIN_USERNAME, signed
       token, and live server-side token — all in one timing-safe call.
    2. Only then is the DB queried, with owner= bound to the session username.

    Returns None on any failure so callers never learn why access was denied.
    """
    if not _is_valid_admin_session():
        logger.warning("Unauthorized access attempt on todo %s", todo_id)
        return None
    # Defence-in-depth: re-verify the session username in constant time immediately
    # before the DB query, independent of the _is_valid_admin_session() check above.
    username = session.get("username", "")
    if not _constant_time_equal(username, ADMIN_USERNAME):
        logger.warning("Unauthorized access attempt on todo %s", todo_id)
        return None
    todo = conn.execute(
        "SELECT * FROM todos WHERE id = ? AND owner = ?", (todo_id, username)
    ).fetchone()
    # Explicitly verify the returned row's owner matches the session user —
    # defence-in-depth against any unexpected result from the database layer.
    if todo is None or not _constant_time_equal(todo["owner"], username):
        logger.warning("Unauthorized access attempt on todo %s", todo_id)
        return None
    return todo


def _csrf_token() -> str:
    """Return the per-session CSRF token, generating one if it does not exist yet."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def _validate_csrf() -> bool:
    """Return True only when the submitted CSRF token matches the session token."""
    form_token = request.form.get("csrf_token", "")
    session_token = session.get("csrf_token", "")
    return bool(session_token) and _constant_time_equal(form_token, session_token)


# Make csrf_token available in every template without explicit passing.
app.jinja_env.globals["csrf_token"] = _csrf_token

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
            owner TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@app.route("/login", methods=["GET", "POST"])
def login() -> str:
    """Display login form and authenticate the user."""
    error = None
    ip = request.remote_addr or "unknown"
    if request.method == "POST":
        if not _validate_csrf():
            error = "Invalid request."
        elif not _check_rate_limit(ip):
            error = f"Too many failed attempts. Try again in {_LOGIN_LOCKOUT_MINUTES} minutes."
        else:
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            username_ok = _constant_time_equal(username, ADMIN_USERNAME)
            password_ok = _verify_password(password, ADMIN_PASSWORD_HASH)
            if username_ok and password_ok:
                _clear_failed_logins(ip)
                raw_token = secrets.token_hex(32)
                _valid_session_tokens.add(_token_digest(raw_token))
                session.clear()  # Prevent session fixation before writing new data
                session.permanent = True
                session["role"] = "admin"
                session["username"] = username
                session["token"] = _token_signer.dumps(raw_token)
                return redirect(url_for("index"))
            _record_failed_login(ip)
            error = "Invalid credentials."
    return render_template("login.html", error=error)


@app.route("/logout", methods=["POST"])
@admin_required
def logout() -> str:
    """Revoke the server-side token and invalidate the session."""
    signed_token = session.get("token")
    if signed_token:
        try:
            raw_token = _token_signer.loads(signed_token)
            _valid_session_tokens.discard(_token_digest(raw_token))
        except BadSignature:
            pass
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@admin_required
def index() -> str:
    """Display all todos."""
    conn = get_db()
    todos = conn.execute("SELECT * FROM todos ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("index.html", todos=todos)


@app.route("/add", methods=["POST"])
@admin_required
def add() -> str:
    """Add a new todo."""
    if not _validate_csrf():
        return redirect(url_for("index"))
    title = request.form.get("title", "").strip()
    if title:
        conn = get_db()
        conn.execute(
            "INSERT INTO todos (title, owner) VALUES (?, ?)",
            (title, session["username"]),
        )
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
@admin_required
def toggle(todo_id: int) -> str:
    """Toggle a todo's completed status."""
    if not _validate_csrf():
        return redirect(url_for("index"))
    conn = get_db()
    if _get_authorized_todo(conn, todo_id) is None:
        conn.close()
        return redirect(url_for("index"))
    conn.execute("UPDATE todos SET completed = NOT completed WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
@admin_required
def delete(todo_id: int) -> str:
    """Delete a todo."""
    if not _validate_csrf():
        return redirect(url_for("index"))
    conn = get_db()
    if _get_authorized_todo(conn, todo_id) is None:
        conn.close()
        return redirect(url_for("index"))
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# Initialize database on startup
init_db()
