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

## Next steps

1. Create LXC on faas for testing
2. Test local provisioning
3. Test remote provisioning
4. Push to GitHub
5. Iterate on tools/files as needed
