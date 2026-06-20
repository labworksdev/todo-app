# todo-app Development Notes

## Environmental setup

Prerequisites: `docker` (daemon running), `git`, `uv`

```bash
task init
```

## Common tasks

| Task | Command |
|------|---------|
| Lint | `task lint` |
| Update dependencies | `task update` |

## Security guidelines

- **Do not log sensitive values** (passwords, tokens, secrets) in clear text. Log outcomes only (e.g., `"Password hashed successfully"`).
- **Do not fall back to ephemeral secret keys in production.** If `SECRET_KEY` is unset, log a warning and refuse to start in production. Ephemeral fallbacks are only acceptable in dev/test environments.
- **Do not define enum constants inline.** Source all enum values (e.g., membership types, purchase types) from the centralized constants file.
- **Authorization logic must be fully implemented.** Never stub, skip, or comment out auth checks.

## Creating a release

Releases are created automatically by python-semantic-release via the release GitHub Action. Version bump rules:

- `fix:` → patch (0.0.x)
- `feat:` → minor (0.x.0)
- `BREAKING CHANGE:` in commit body → major (x.0.0)

Example commit messages:

```
fix: resolve user login issue
feat: add user profile page
feat!: redesign authentication system

BREAKING CHANGE: The login API now requires a different payload format
```
