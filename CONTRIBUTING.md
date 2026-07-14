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

- **Do not** log passwords, tokens, or secrets in clear text (use outcome messages only)
- **Do not** fall back to ephemeral/random secret keys in production; fail fast with a clear error if `SECRET_KEY` is unset
- **Do not** define enum constants inline; source all enums from the centralized constants file
- **Do** ensure authorization logic is fully implemented before merging

## Creating a release

Releases are created automatically by python-semantic-release via the release GitHub Action. Commit message convention:

| Prefix | Version bump |
|--------|--------------|
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
