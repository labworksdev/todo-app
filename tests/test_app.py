"""Unit tests for priority feature."""

import sqlite3
from pathlib import Path

import pytest

import todo_app.app as app_module
from todo_app.app import VALID_PRIORITIES, app


@pytest.fixture()
def client(tmp_path: Path):
    """Flask test client with an isolated temporary database."""
    db_path = str(tmp_path / "test_todos.db")
    app.config["TESTING"] = True
    original_db = app_module.DATABASE
    app_module.DATABASE = db_path
    app_module.init_db()

    with app.test_client() as c:
        yield c

    app_module.DATABASE = original_db


# ---------------------------------------------------------------------------
# Basic CRUD with priority
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_index_empty(client) -> None:
    """GET / returns 200 with no-todos message when DB is empty."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"No todos yet" in response.data


@pytest.mark.unit
def test_add_todo_default_priority(client) -> None:
    """POST /add creates a todo with default medium priority."""
    client.post("/add", data={"title": "Buy milk"})
    assert b"Buy milk" in client.get("/").data
    assert b"Medium" in client.get("/").data


@pytest.mark.unit
def test_add_todo_high_priority(client) -> None:
    """POST /add creates a todo with high priority."""
    client.post("/add", data={"title": "Fix bug", "priority": "high"})
    assert b"Fix bug" in client.get("/").data
    assert b"High" in client.get("/").data


@pytest.mark.unit
def test_add_todo_low_priority(client) -> None:
    """POST /add creates a todo with low priority."""
    client.post("/add", data={"title": "Read docs", "priority": "low"})
    assert b"Read docs" in client.get("/").data
    assert b"Low" in client.get("/").data


@pytest.mark.unit
def test_add_todo_invalid_priority_defaults_to_medium(client) -> None:
    """POST /add with an invalid priority falls back to medium."""
    client.post("/add", data={"title": "Test task", "priority": "urgent"})
    assert b"Test task" in client.get("/").data
    assert b"Medium" in client.get("/").data


@pytest.mark.unit
def test_add_todo_empty_title_ignored(client) -> None:
    """POST /add with empty title does not create a todo."""
    client.post("/add", data={"title": "   ", "priority": "high"})
    assert b"No todos yet" in client.get("/").data


@pytest.mark.unit
def test_toggle_todo(client) -> None:
    """GET /toggle/<id> flips the completed status."""
    client.post("/add", data={"title": "Toggle me", "priority": "medium"})
    assert b"Open" in client.get("/").data

    conn = sqlite3.connect(app_module.DATABASE)
    row = conn.execute("SELECT id FROM todos WHERE title = 'Toggle me'").fetchone()
    conn.close()

    client.get(f"/toggle/{row[0]}")
    assert b"Done" in client.get("/").data


@pytest.mark.unit
def test_delete_todo(client) -> None:
    """GET /delete/<id> removes the todo."""
    client.post("/add", data={"title": "Delete me", "priority": "low"})

    conn = sqlite3.connect(app_module.DATABASE)
    row = conn.execute("SELECT id FROM todos WHERE title = 'Delete me'").fetchone()
    conn.close()

    client.get(f"/delete/{row[0]}")
    assert b"Delete me" not in client.get("/").data


# ---------------------------------------------------------------------------
# Priority filtering
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_filter_by_high_priority(client) -> None:
    """GET /?priority=high shows only high-priority todos."""
    client.post("/add", data={"title": "High task", "priority": "high"})
    client.post("/add", data={"title": "Low task", "priority": "low"})

    response = client.get("/?priority=high")
    assert b"High task" in response.data
    assert b"Low task" not in response.data


@pytest.mark.unit
def test_filter_by_medium_priority(client) -> None:
    """GET /?priority=medium shows only medium-priority todos."""
    client.post("/add", data={"title": "Medium task", "priority": "medium"})
    client.post("/add", data={"title": "High task", "priority": "high"})

    response = client.get("/?priority=medium")
    assert b"Medium task" in response.data
    assert b"High task" not in response.data


@pytest.mark.unit
def test_filter_by_low_priority(client) -> None:
    """GET /?priority=low shows only low-priority todos."""
    client.post("/add", data={"title": "Low task", "priority": "low"})
    client.post("/add", data={"title": "High task", "priority": "high"})

    response = client.get("/?priority=low")
    assert b"Low task" in response.data
    assert b"High task" not in response.data


@pytest.mark.unit
def test_filter_invalid_shows_all(client) -> None:
    """GET /?priority=bogus returns all todos."""
    client.post("/add", data={"title": "High task", "priority": "high"})
    client.post("/add", data={"title": "Low task", "priority": "low"})

    response = client.get("/?priority=bogus")
    assert b"High task" in response.data
    assert b"Low task" in response.data


# ---------------------------------------------------------------------------
# Priority sorting
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_sort_by_priority(client) -> None:
    """GET /?sort=priority orders high before medium before low."""
    client.post("/add", data={"title": "Low task", "priority": "low"})
    client.post("/add", data={"title": "High task", "priority": "high"})
    client.post("/add", data={"title": "Medium task", "priority": "medium"})

    html = client.get("/?sort=priority").data.decode()
    assert html.index("High task") < html.index("Medium task") < html.index("Low task")


# ---------------------------------------------------------------------------
# Constants and migration
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_valid_priorities_constant() -> None:
    """VALID_PRIORITIES contains exactly high, medium, low."""
    assert set(VALID_PRIORITIES) == {"high", "medium", "low"}


@pytest.mark.unit
def test_init_db_migration_adds_priority_column(tmp_path: Path) -> None:
    """init_db adds the priority column to an existing todos table without it."""
    db_path = str(tmp_path / "legacy.db")

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    original_db = app_module.DATABASE
    app_module.DATABASE = db_path
    try:
        app_module.init_db()
        conn = sqlite3.connect(db_path)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(todos)")}
        conn.close()
        assert "priority" in columns
    finally:
        app_module.DATABASE = original_db
