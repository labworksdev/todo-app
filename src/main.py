#!/usr/bin/env python3
"""
todo-app script entrypoint
"""

import argparse

from todo_app import __version__, config


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        prog="todo_app",
        description="An application for managing TODOs",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args()

    log = config.setup_logging()
    log.debug("Logging initialized with level: %s", log.level)

    raise NotImplementedError()


if __name__ == "__main__":
    main()
