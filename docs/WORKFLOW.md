# Workflow

## Branches

Trunk-based: `main` is the only long-lived branch.

- Do each piece of work on a short-lived branch and merge it back into `main` within a few days.
- Small fixes such as typos can be committed directly to `main`.
- Name branches `<type>/<short-description>`:

| Type | For | Example |
|---|---|---|
| `feat` | New functionality | `feat/webcam-capture` |
| `fix` | Bug fixes | `fix/serial-reconnect` |
| `refactor` | Code changes with no behavior change | `refactor/stream-interface` |
| `docs` | Notes and documentation | `docs/02-syncfield` |
| `chore` | Tooling, config, dependencies | `chore/python-env` |
| `exp` | Part 2 swap experiments | `exp/01-storage-mcap` |

## Commit messages

Lowercase, short, in English. e.g. `add 01-time notes and labs`

## Comparing v1 and v2

Don't keep v1 and v2 on separate branches. Both implementations live on `main` behind the same swap-point interface, and a config value selects one, so they can be compared on the same input in the same commit.

## Tags

Tags are added manually, only when needed.
