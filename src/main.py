#!/usr/bin/env python3
"""
todo-app script entrypoint
"""

import argparse
import os
import subprocess
import sys

from todo_app import __version__, config


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        prog="todo_app",
        description="An application for managing TODOs",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run Flask development server instead of gunicorn",
    )
    args = parser.parse_args()

    log = config.setup_logging()
    log.debug("Logging initialized with level: %s", log.level)

    port = int(os.environ.get("PORT", "8000"))

    if args.dev:
        from todo_app.app import app

        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        sys.exit(
            subprocess.call(
                [
                    sys.executable,
                    "-m",
                    "gunicorn",
                    "--bind",
                    f"0.0.0.0:{port}",
                    "todo_app.app:app",
                ]
            )
        )


if __name__ == "__main__":
    main()
