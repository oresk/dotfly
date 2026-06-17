# dotfly — Initial Setup

Date: 2026-06-17

## What

dotfly is a Python tool that provisions machines from a TOML config:
installs tools via apt and processes dotfiles from a git repo.

## Design decisions

- Profiles support inheritance via `inherit` key; child tools appended,
  child files with same `dest`+`mode` override parent's.
- No host info in TOML — provided via CLI `--host` flag
- Remote transport: rsync entire repo (including `.git`) so remote
  retains origin URL and can `git pull` later
- Zero external Python deps — uses stdlib only (tomllib for Python 3.11+)
- Source paths in TOML are relative to repo root
- `{{ home }}` template variable expanded to target user's home
- **File modes**: `link` (symlink, default), `copy`, `append`, `prepend`
- Append/prepend use content-based dedup for idempotency

## Project structure

```
~/dotfly/
├── dotfly.py              ← entry point (via `python3 -m dotfly`)
├── dotfly/
│   ├── __init__.py
│   ├── config.py          ← TOML loading + profile resolution
│   ├── provisioner.py     ← tool install + file processing (link/copy/append/prepend)
│   └── remote.py          ← SSH orchestration
├── dotfly.toml            ← configuration (profiles, tools, files)
├── dotfiles/
│   ├── .gitconfig         ← symlinked (managed entirely by dotfly)
│   ├── bashrc-additions.sh ← appended to ~/.bashrc (preserves existing)
│   └── aliases.sh         ← appended to ~/.bash_aliases
├── pyproject.toml
├── .gitignore
├── notes/
└── README.md
```

## Profiles

| Profile | Inherits | Tools | Files |
|---------|----------|-------|-------|
| `base` | — | bat, ripgrep | bashrc-additions.sh (append), .gitconfig (link) |
| `desktop` | base | +eza, tmux, fzf, zoxide, fd-find | +aliases.sh (append) |
| `server` | base | +tmux | — |

## Test env

LXC CT 104 on faas (192.168.80.104, Debian 13)

## Todo

- Push to GitHub
- Add non-apt package managers
- Add config validation
- Possibly add `binary` field to tools for post-install verification
