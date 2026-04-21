# todo-app Development Notes

## Environmental setup

Prerequisites: `docker` (daemon running), `git`, `uv`

```bash
task init
```

## Common tasks

| Task | Command |
|---|---|
| Lint | `task lint` |
| Update dependencies | `task update` |

## Security guidelines

- **Never log passwords, tokens, or secrets** — log outcomes only (e.g., "Password hashed successfully"), not values.
- **SECRET_KEY must be set via environment variable in production.** If absent in production, the app must log an error and refuse to start — do NOT silently fall back to an ephemeral random value.
- **Authorization logic must be fully implemented** — do not stub or skip auth checks.
- **Enum/constant values** must be sourced from the centralized constants file; do not define or duplicate them inline.

## Creating a release

Releases are created automatically by python-semantic-release via the release GitHub Action. Commit message convention:

| Prefix | Version bump | Example |
|---|---|---|
| `fix:` | patch (0.0.x) | `fix: resolve user login issue` |
| `feat:` | minor (0.x.0) | `feat: add user profile page` |
| `feat!:` + `BREAKING CHANGE:` | major (x.0.0) | see below |

```bash
git commit -m "feat!: redesign authentication system

BREAKING CHANGE: The login API now requires a different payload format"
```
