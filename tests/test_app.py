#!/usr/bin/env python3
"""
Unit tests for todo_app/app.py - tag and category functionality.
"""

import os
import tempfile

import pytest

TEST_OWNER = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"  # valid 32-char hex for owner_id format


@pytest.fixture()
def app_client():
    """Create a test Flask client with an isolated SQLite database and a seeded session owner."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.environ["DATABASE_PATH"] = db_path

    import importlib

    import todo_app.app as app_module

    importlib.reload(app_module)

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        # Seed a stable owner_id so all requests in this test share the same session identity
        with client.session_transaction() as sess:
            sess["owner_id"] = TEST_OWNER
        yield client, app_module

    os.close(db_fd)
    os.unlink(db_path)
    del os.environ["DATABASE_PATH"]


@pytest.mark.unit
def test_index_returns_200(app_client):
    """Test that the index page loads successfully."""
    client, _ = app_client
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.unit
def test_predefined_tags_seeded(app_client):
    """Test that the four predefined tags are seeded on init."""
    client, app_module = app_client
    conn = app_module.get_db()
    tags = conn.execute("SELECT name FROM tags ORDER BY name").fetchall()
    conn.close()
    names = [t["name"] for t in tags]
    assert set(names) == {"Health", "Personal", "Shopping", "Work"}


@pytest.mark.unit
def test_add_todo_no_tags(app_client):
    """Test adding a todo without any tags."""
    client, app_module = app_client
    response = client.post("/add", data={"title": "Buy milk"}, follow_redirects=True)
    assert response.status_code == 200

    conn = app_module.get_db()
    todos = conn.execute("SELECT * FROM todos").fetchall()
    conn.close()
    assert len(todos) == 1
    assert todos[0]["title"] == "Buy milk"
    assert todos[0]["owner_id"] == TEST_OWNER


@pytest.mark.unit
def test_add_todo_with_tags(app_client):
    """Test adding a todo with tags assigns the tags correctly."""
    client, app_module = app_client

    conn = app_module.get_db()
    tag = conn.execute("SELECT id FROM tags WHERE name = 'Work'").fetchone()
    conn.close()

    client.post("/add", data={"title": "Write report", "tags": [str(tag["id"])]}, follow_redirects=True)

    todos = app_module.get_todos_with_tags(TEST_OWNER)
    assert len(todos) == 1
    assert len(todos[0]["tags"]) == 1
    assert todos[0]["tags"][0]["name"] == "Work"


@pytest.mark.unit
def test_add_todo_with_multiple_tags(app_client):
    """Test adding a todo with multiple tags."""
    client, app_module = app_client

    conn = app_module.get_db()
    work_tag = conn.execute("SELECT id FROM tags WHERE name = 'Work'").fetchone()
    health_tag = conn.execute("SELECT id FROM tags WHERE name = 'Health'").fetchone()
    conn.close()

    client.post(
        "/add",
        data={"title": "Walk to work", "tags": [str(work_tag["id"]), str(health_tag["id"])]},
        follow_redirects=True,
    )

    todos = app_module.get_todos_with_tags(TEST_OWNER)
    assert len(todos) == 1
    tag_names = {t["name"] for t in todos[0]["tags"]}
    assert tag_names == {"Work", "Health"}


@pytest.mark.unit
def test_filter_by_tag(app_client):
    """Test that filtering by tag returns only matching todos for the owner."""
    client, app_module = app_client

    conn = app_module.get_db()
    work_id = conn.execute("SELECT id FROM tags WHERE name = 'Work'").fetchone()["id"]
    personal_id = conn.execute("SELECT id FROM tags WHERE name = 'Personal'").fetchone()["id"]
    conn.close()

    client.post("/add", data={"title": "Work task", "tags": [str(work_id)]})
    client.post("/add", data={"title": "Personal task", "tags": [str(personal_id)]})
    client.post("/add", data={"title": "Untagged task"})

    work_todos = app_module.get_todos_with_tags(TEST_OWNER, filter_tag_id=work_id)
    assert len(work_todos) == 1
    assert work_todos[0]["title"] == "Work task"

    all_todos = app_module.get_todos_with_tags(TEST_OWNER)
    assert len(all_todos) == 3


@pytest.mark.unit
def test_filter_route_by_tag(app_client):
    """Test that the index route filters correctly via query param."""
    client, app_module = app_client

    conn = app_module.get_db()
    work_id = conn.execute("SELECT id FROM tags WHERE name = 'Work'").fetchone()["id"]
    conn.close()

    client.post("/add", data={"title": "Work task", "tags": [str(work_id)]})
    client.post("/add", data={"title": "Personal task"})

    response = client.get(f"/?tag={work_id}")
    assert response.status_code == 200
    assert b"Work task" in response.data
    assert b"Personal task" not in response.data


@pytest.mark.unit
def test_todos_isolated_by_owner(app_client):
    """Test that todos created by one session are not visible to another."""
    client, app_module = app_client
    client.post("/add", data={"title": "My task"})

    other_todos = app_module.get_todos_with_tags("b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5")
    assert len(other_todos) == 0

    my_todos = app_module.get_todos_with_tags(TEST_OWNER)
    assert len(my_todos) == 1


@pytest.mark.unit
def test_index_route_only_shows_owner_todos(app_client):
    """Test that the index route only returns todos owned by the requesting session."""
    client, app_module = app_client
    client.post("/add", data={"title": "Owner task"})

    # Switch to a different session owner and add their own todo
    with client.session_transaction() as sess:
        sess["owner_id"] = "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5"
    client.post("/add", data={"title": "Other task"})

    # The current session (other-session-owner) should only see their own todo
    response = client.get("/")
    assert response.status_code == 200
    assert b"Other task" in response.data
    assert b"Owner task" not in response.data

    # Switch back and verify original owner only sees their todo
    with client.session_transaction() as sess:
        sess["owner_id"] = TEST_OWNER
    response = client.get("/")
    assert b"Owner task" in response.data
    assert b"Other task" not in response.data


@pytest.mark.unit
def test_add_ignores_invalid_tag_ids(app_client):
    """Test that invalid or non-existent tag IDs are silently ignored."""
    client, app_module = app_client
    client.post("/add", data={"title": "Task", "tags": ["99999", "abc", "-1"]})

    todos = app_module.get_todos_with_tags(TEST_OWNER)
    assert len(todos) == 1
    assert len(todos[0]["tags"]) == 0


@pytest.mark.unit
def test_toggle_todo(app_client):
    """Test toggling a todo's completed status."""
    client, app_module = app_client
    client.post("/add", data={"title": "Task"})

    conn = app_module.get_db()
    todo = conn.execute("SELECT * FROM todos").fetchone()
    conn.close()
    assert todo["completed"] == 0

    client.post(f"/toggle/{todo['id']}")

    conn = app_module.get_db()
    todo = conn.execute("SELECT * FROM todos WHERE id = ?", (todo["id"],)).fetchone()
    conn.close()
    assert todo["completed"] == 1


@pytest.mark.unit
def test_toggle_forbidden_for_non_owner(app_client):
    """Test that toggling another session's todo returns 403."""
    client, app_module = app_client
    client.post("/add", data={"title": "My task"})

    conn = app_module.get_db()
    todo = conn.execute("SELECT * FROM todos").fetchone()
    conn.close()

    # Switch session to a different owner
    with client.session_transaction() as sess:
        sess["owner_id"] = "different-owner"

    response = client.post(f"/toggle/{todo['id']}")
    assert response.status_code == 403


@pytest.mark.unit
def test_delete_todo_removes_tag_associations(app_client):
    """Test that deleting a todo also removes its tag associations."""
    client, app_module = app_client

    conn = app_module.get_db()
    work_id = conn.execute("SELECT id FROM tags WHERE name = 'Work'").fetchone()["id"]
    conn.close()

    client.post("/add", data={"title": "Work task", "tags": [str(work_id)]})

    conn = app_module.get_db()
    todo = conn.execute("SELECT * FROM todos").fetchone()
    conn.close()

    client.post(f"/delete/{todo['id']}")

    conn = app_module.get_db()
    remaining = conn.execute("SELECT * FROM todos").fetchall()
    associations = conn.execute("SELECT * FROM todo_tags").fetchall()
    conn.close()

    assert len(remaining) == 0
    assert len(associations) == 0


@pytest.mark.unit
def test_delete_forbidden_for_non_owner(app_client):
    """Test that deleting another session's todo returns 403."""
    client, app_module = app_client
    client.post("/add", data={"title": "My task"})

    conn = app_module.get_db()
    todo = conn.execute("SELECT * FROM todos").fetchone()
    conn.close()

    with client.session_transaction() as sess:
        sess["owner_id"] = "different-owner"

    response = client.post(f"/delete/{todo['id']}")
    assert response.status_code == 403


@pytest.mark.unit
def test_csrf_rejects_missing_token(app_client):
    """Test that mutating endpoints return 403 when CSRF token is absent (non-test mode)."""
    client, app_module = app_client
    app_module.app.config["TESTING"] = False
    try:
        response = client.post("/add", data={"title": "No CSRF"})
        assert response.status_code == 403
    finally:
        app_module.app.config["TESTING"] = True
