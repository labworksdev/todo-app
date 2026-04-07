"""Tests for the Flask todo application routes."""

import pytest


@pytest.mark.unit
def test_index_empty(client):
    """Test index page with no todos."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"No todos yet." in response.data


@pytest.mark.unit
def test_add_todo(client):
    """Test adding a todo."""
    response = client.post("/add", data={"title": "Buy milk"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Buy milk" in response.data


@pytest.mark.unit
def test_add_todo_empty_title(client):
    """Test that adding a todo with empty title is ignored."""
    response = client.post("/add", data={"title": "   "}, follow_redirects=True)
    assert response.status_code == 200
    assert b"No todos yet." in response.data


@pytest.mark.unit
def test_toggle_todo(client):
    """Test toggling a todo's completion status."""
    client.post("/add", data={"title": "Test task"})
    response = client.get("/toggle/1", follow_redirects=True)
    assert response.status_code == 200
    assert b"Done" in response.data


@pytest.mark.unit
def test_delete_todo(client):
    """Test deleting a todo."""
    client.post("/add", data={"title": "To delete"})
    response = client.get("/delete/1", follow_redirects=True)
    assert response.status_code == 200
    assert b"No todos yet." in response.data


@pytest.mark.unit
def test_edit_todo(client):
    """Test editing a todo title."""
    client.post("/add", data={"title": "Original title"})
    response = client.patch("/edit/1", data={"title": "Updated title"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Updated title"


@pytest.mark.unit
def test_edit_todo_empty_title(client):
    """Test that editing with an empty title returns 400."""
    client.post("/add", data={"title": "Original title"})
    response = client.patch("/edit/1", data={"title": "   "})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


@pytest.mark.unit
def test_edit_todo_persists(client):
    """Test that editing a todo persists the new title."""
    client.post("/add", data={"title": "Old title"})
    client.patch("/edit/1", data={"title": "New title"})
    response = client.get("/")
    assert b"New title" in response.data
    assert b"Old title" not in response.data
