"""Generate a PBKDF2-SHA256 password hash for use as ADMIN_PASSWORD_HASH.

Usage:
    SETUP_SECRET=<value> python scripts/generate_password_hash.py

The SETUP_SECRET environment variable must match the value set at deploy time
to prevent unauthorized execution of this script.

Required environment variables:
    SETUP_SECRET   Primary authorization secret.
    SETUP_TOKEN    Secondary authorization token — acts as a second factor so
                   knowledge of SETUP_SECRET alone is insufficient to run the script.

Optional environment variables:
    PBKDF2_ITERATIONS      Number of PBKDF2 iterations (default: 600000).
                           The value is embedded in the hash output so
                           verification is self-contained — increase it over
                           time without breaking existing hashes.
    PBKDF2_MIN_ITERATIONS  Minimum acceptable iteration count (default: 200000).
                           Raise this over time as hardware improves.
"""

import getpass
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from pathlib import Path

_DEFAULT_ITERATIONS = 600_000
_FALLBACK_MIN_ITERATIONS = 200_000
_MIN_PASSWORD_LENGTH = 12
_MIN_SECRET_LENGTH = 32  # Minimum length for SETUP_SECRET and SETUP_TOKEN
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 900  # 15 minutes
_ATTEMPT_DELAY_SECONDS = 2  # Slow brute-force after each failure
_ATTEMPT_FILE = Path.home() / ".todo-app-setup-attempts"


def _check_rate_limit() -> None:
    """Enforce a lockout after repeated failed credential attempts. Exits on violation."""
    try:
        if _ATTEMPT_FILE.exists():
            data = json.loads(_ATTEMPT_FILE.read_text())
            failures = data.get("failures", 0)
            locked_until = data.get("locked_until", 0)
            if failures >= _MAX_ATTEMPTS and time.time() < locked_until:
                remaining = int(locked_until - time.time())
                print(f"Error: too many failed attempts. Try again in {remaining}s.", file=sys.stderr)
                sys.exit(1)
    except (OSError, json.JSONDecodeError, KeyError):
        pass  # Corrupt or missing file — allow the attempt.


def _record_failure() -> None:
    """Increment the on-disk failure counter, set a lockout timestamp, and delay to slow brute-force."""
    try:
        data: dict = {}
        if _ATTEMPT_FILE.exists():
            data = json.loads(_ATTEMPT_FILE.read_text())
        failures = data.get("failures", 0) + 1
        locked_until = time.time() + _LOCKOUT_SECONDS if failures >= _MAX_ATTEMPTS else 0
        _ATTEMPT_FILE.write_text(json.dumps({"failures": failures, "locked_until": locked_until}))
    except OSError:
        pass
    # Always delay after a failure to slow down automated attacks.
    time.sleep(_ATTEMPT_DELAY_SECONDS)


def _clear_failures() -> None:
    """Remove the failure record after a successful authentication."""
    try:
        _ATTEMPT_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def _check_password_strength(password: str) -> list[str]:
    """Return a list of unmet password requirements; empty list means the password passes."""
    errors = []
    if len(password) < _MIN_PASSWORD_LENGTH:
        errors.append(f"at least {_MIN_PASSWORD_LENGTH} characters")
    if not any(c.isupper() for c in password):
        errors.append("at least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("at least one digit")
    if not any(not c.isalnum() for c in password):
        errors.append("at least one special character (e.g. !@#$%)")
    return errors


def main() -> None:
    """Verify the setup secret, then prompt for a password and print its hash."""
    _check_rate_limit()

    expected = os.environ.get("SETUP_SECRET")
    if not expected:
        print(
            "Error: SETUP_SECRET environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(expected) < _MIN_SECRET_LENGTH:
        print(
            f"Error: SETUP_SECRET must be at least {_MIN_SECRET_LENGTH} characters.",
            file=sys.stderr,
        )
        sys.exit(1)

    expected_token = os.environ.get("SETUP_TOKEN")
    if not expected_token:
        print("Error: SETUP_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    if len(expected_token) < _MIN_SECRET_LENGTH:
        print(
            f"Error: SETUP_TOKEN must be at least {_MIN_SECRET_LENGTH} characters.",
            file=sys.stderr,
        )
        sys.exit(1)

    provided = getpass.getpass("Setup secret: ")
    provided_token = getpass.getpass("Setup token: ")
    # Both comparisons always run (results stored before the conditional) so
    # neither leaks which credential was wrong via a short-circuit timing difference.
    secret_ok = hmac.compare_digest(provided.encode(), expected.encode())
    token_ok = hmac.compare_digest(provided_token.encode(), expected_token.encode())
    if not (secret_ok and token_ok):
        _record_failure()
        print("Error: incorrect setup credentials.", file=sys.stderr)
        sys.exit(1)

    _clear_failures()

    try:
        min_iterations = int(os.environ.get("PBKDF2_MIN_ITERATIONS", str(_FALLBACK_MIN_ITERATIONS)))
        if min_iterations < 1:
            raise ValueError
    except ValueError:
        print("Error: PBKDF2_MIN_ITERATIONS must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    iterations_env = os.environ.get("PBKDF2_ITERATIONS", str(_DEFAULT_ITERATIONS))
    try:
        iterations = int(iterations_env)
        if iterations < min_iterations:
            raise ValueError
    except ValueError:
        print(
            f"Error: PBKDF2_ITERATIONS must be an integer >= {min_iterations}.",
            file=sys.stderr,
        )
        sys.exit(1)

    password = getpass.getpass("New password: ")
    strength_errors = _check_password_strength(password)
    if strength_errors:
        print("Error: password does not meet requirements:", file=sys.stderr)
        for err in strength_errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Error: passwords do not match.", file=sys.stderr)
        sys.exit(1)

    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    print(f"{iterations}:{salt.hex()}:{key.hex()}")


if __name__ == "__main__":
    main()
