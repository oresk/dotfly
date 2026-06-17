# dotfly — Initial Setup

Date: 2026-06-17

## What

dotfly is a Python tool that provisions machines from a TOML config:
installs tools via apt and symlinks dotfiles from a git repo.

## Design decisions

- Profiles support inheritance via `inherit` key; child tools appended,
  child files with same `dest` override parent's.
- No host info in TOML — provided via CLI `--host` flag
- Remote transport: rsync entire repo (including `.git`) so remote
  retains origin URL and can `git pull` later
- Zero external Python deps — uses stdlib only (tomllib for Python 3.11+)
- Source paths in TOML are relative to repo root
- `{{ home }}` template variable expanded to target user's home

## Project structure

```
~/dotfly/
├── dotfly.py              ← entry point (via `python3 -m dotfly`)
├── dotfly/
│   ├── __init__.py
│   ├── config.py          ← TOML loading + profile resolution
│   ├── provisioner.py     ← tool install + file symlink
│   ├── remote.py          ← SSH orchestration
│   └── __main__.py        ← CLI with argparse
├── dotfly.toml            ← configuration (profiles, tools, files)
├── dotfiles/
│   ├── .bashrc
│   ├── .bash_aliases
│   └── .gitconfig
├── pyproject.toml
├── .gitignore
├── notes/
└── README.md
```

## Completed

- ✅ Project skeleton, TOML config, dotfiles
- ✅ Profile resolution with inheritance (`inherit` key)
- ✅ Local provisioning: `apt install` + symlink, sudo detection
- ✅ Remote provisioning: SSH → git/rsync install → rsync repo → execute
- ✅ LXC test container on faas (CT 104, 192.168.80.104, Debian 13)
- ✅ End-to-end test: `base` and `desktop` profiles via remote
- ✅ Python version check on remote (3.11+ required)
- ✅ SSH connection error differentiation
- ✅ Package-by-package install with targeted error messages
- ✅ Dry-run mode (local + remote)

## Still to do

- Push to a public GitHub repo
- Support non-apt package managers (pip, cargo, etc.)
- Test the `server` profile
- Add config validation (duplicate destinations, etc.)
- Possibly add `binary` field to tools for verification
