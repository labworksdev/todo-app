#!/usr/bin/env python3
"""
Test package metadata and imports
"""

import pytest

from todo_app import (
    __maintainer__,
    __project_name__,
    __version__,
    __copyright__,
)


@pytest.mark.unit
def test_package_metadata():
    """Test that package metadata is accessible."""

    assert __maintainer__ == "Labworks"
    assert __project_name__ == "todo_app"
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert __copyright__.startswith("(c) Labworks")
