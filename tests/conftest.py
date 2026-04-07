"""Shared pytest fixtures."""

import pytest

import todo_app.app as app_module
from todo_app.app import app, init_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Flask test client with a temporary database."""
    monkeypatch.setattr(app_module, "DATABASE", str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    init_db()

    with app.test_client() as test_client:
        yield test_client
