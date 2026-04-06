#!/usr/bin/env python3
"""
todo-app script entrypoint
"""

import os
import subprocess
import sys

from todo_app import config


def main():
    """Main entry point for the application."""
    parser = config.create_arg_parser()
    parser.prog = "todo_app"
    parser.description = "An application for managing TODOs"
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run Flask development server instead of gunicorn",
    )
    args = parser.parse_args()

    log = config.setup_logging(vars(args))
    log.debug("Logging initialized with level: %s", log.level)

    port = int(os.environ.get("PORT", "8000"))

    if args.dev:
        from todo_app.app import app

        app.run(host="0.0.0.0", port=port, debug=args.dev)
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
