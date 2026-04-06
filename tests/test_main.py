#!/usr/bin/env python3
"""
Test main.py module
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.unit
def test_main_import():
    """Test that main.py can be imported without executing"""
    import main  # noqa: F401


@pytest.mark.unit
def test_main_function():
    """Test that main() starts gunicorn by default"""
    from main import main

    with patch("sys.argv", ["main"]):
        with patch("subprocess.call", return_value=0) as mock_call:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
            mock_call.assert_called_once()
            # Verify gunicorn is being invoked
            call_args = mock_call.call_args[0][0]
            assert "gunicorn" in call_args[2]


@pytest.mark.unit
def test_main_version():
    """Test that --version prints the version and exits"""
    from main import main

    with patch("sys.argv", ["main", "--version"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


@pytest.mark.unit
def test_main_as_script():
    """Test that main.py starts the server when run as a script"""
    main_path = Path(__file__).parent.parent / "src" / "main.py"

    try:
        result = subprocess.run(
            [sys.executable, str(main_path)],
            capture_output=True,
            text=True,
            timeout=3,
        )
        # If it exited quickly, it should not have crashed with an unhandled exception
        assert result.returncode == 0 or "gunicorn" in result.stderr.lower()
    except subprocess.TimeoutExpired:
        pass  # Expected: server started and is running


@pytest.mark.unit
def test_main_as_script_version():
    """Test that --version works when run as a script"""
    main_path = Path(__file__).parent.parent / "src" / "main.py"

    result = subprocess.run(
        [sys.executable, str(main_path), "--version"],
        capture_output=True,
        text=True,
    )

    from todo_app import __version__

    assert result.returncode == 0
    assert __version__ in result.stdout
