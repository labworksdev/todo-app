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
- **Do not fall back to ephemeral secret keys in production.** If `SECRET_KEY` is missing in production, log an error and refuse to start. Ephemeral fallbacks are only acceptable in dev with an explicit warning.
- **Authorization logic must be fully implemented.** Never stub or skip auth checks.
- **Use the centralized constants file** for all enum values (e.g., membership types, purchase types). Do not define or duplicate enums inline.

## Creating a release

Releases are created automatically by python-semantic-release via the release GitHub Action. Commit message format determines version bump:

| Prefix | Bump | Example |
|--------|------|---------|
| `fix:` | patch (0.0.x) | `fix: resolve user login issue` |
| `feat:` | minor (0.x.0) | `feat: add user profile page` |
| `BREAKING CHANGE:` in body | major (x.0.0) | see below |

```bash
# Major release example
git commit -m "feat!: redesign authentication system

BREAKING CHANGE: The login API now requires a different payload format"
```
