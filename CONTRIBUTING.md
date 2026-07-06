# todo-app Development Notes

## Environmental setup

Prerequisites: `docker` (daemon running), `git`, `uv`

```bash
task init
```

## Linting locally

```bash
task lint
```

## Updating the dependencies

```bash
task update
```

## Running tests

```bash
task test
```

## Security guidelines

- **Never log sensitive values** (passwords, secrets, tokens) in clear text — log outcomes only.
- **Never fall back to ephemeral secret keys** in production. If `SECRET_KEY` is unset in a production environment, log an error and refuse to start.
- **Authorization logic must be fully implemented** before merging — do not merge stubs or TODOs in auth paths.
- **Source all enum/constant values** from the centralized constants file; do not define or duplicate them inline.

## Creating a release

Releases are created automatically by python-semantic-release based on conventional commits. Trigger the release via the **Release** GitHub Action.

Version bump rules:
- `fix:` → patch (0.0.x)
- `feat:` → minor (0.x.0)
- `BREAKING CHANGE:` in commit body → major (x.0.0)

Example commit messages:

```bash
# Patch
git commit -m "fix: resolve user login issue"

# Minor
git commit -m "feat: add user profile page"

# Major
git commit -m "feat!: redesign authentication system

BREAKING CHANGE: The login API now requires a different payload format"
```
