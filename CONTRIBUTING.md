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

- **Never** hardcode secrets, passwords, or tokens in code or logs.
- **Never** use a silent ephemeral fallback for `SECRET_KEY` in production. If `SECRET_KEY` is unset in production, log an error and refuse to start.
- **Never** log sensitive values (passwords, secrets, tokens) in clear text.
- Authorization logic must be fully implemented before merging — do not stub or skip auth checks.
- All constant enum values (e.g. membership types, purchase types) must be defined in the centralized constants file, not inline.

## Creating a release

Releases are created automatically by python-semantic-release via the release GitHub Action. Commit message convention:

| Prefix | Version bump |
|---|---|
| `fix:` | patch (0.0.x) |
| `feat:` | minor (0.x.0) |
| `BREAKING CHANGE:` in body | major (x.0.0) |

Examples:
```
fix: resolve user login issue
feat: add user profile page
feat!: redesign authentication system

BREAKING CHANGE: The login API now requires a different payload format
```
