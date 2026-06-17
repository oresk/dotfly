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
- **Tool config grouping**: tools carry `config_source`, `config_dest`, `config_mode`
  inline — no separate `[[files]]` entry needed for single-config tools
- **Optional flag**: tools can be marked `optional = true`; failed installs
  warn instead of aborting (useful for packages not in all repos)

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
│   ├── .gitconfig         ← link (managed entirely by dotfly)
│   ├── bashrc-additions.sh ← append to ~/.bashrc
│   ├── aliases.sh         ← append to ~/.bash_aliases
│   ├── git/
│   │   └── ignore         ← link (global gitignore)
│   └── config/
│       ├── starship.toml  ← link
│       ├── tmux/
│       │   └── tmux.conf  ← link (grouped with tmux tool)
│       ├── alacritty/
│       │   └── alacritty.toml ← link (grouped with alacritty tool)
│       ├── hypr/
│       │   ├── hyprland.conf  ← link dir (grouped with hyprland tool)
│       │   ├── hypridle.conf
│       │   └── hyprlock.conf
│       ├── waybar/
│       │   ├── config         ← link dir (grouped with waybar tool)
│       │   └── style*.css
│       ├── mako/
│       │   └── config     ← link (grouped with mako tool)
│       └── scripts/       ← link dir (13 scripts)
├── pyproject.toml
├── .gitignore
├── notes/
└── README.md
```

## Profiles

| Profile | Inherits | Tools | Files |
|---------|----------|-------|-------|
| `base` | — | neovim, bat, eza, tmux (+config), fzf, zoxide, fd-find, rg | bashrc-additions (append), aliases (append), .gitconfig (link), git/ignore (link) |
| `desktop` | base | +alacritty (+config), waybar (+config dir), mako (+config), hyprland (+config dir, optional) | +hypr dir (link), waybar dir (link), scripts dir (link), starship.toml (link) |
| `server` | — | (empty) | (empty) |

## Test env

LXC CT 104 on faas (192.168.80.104, Debian 13)

## TODO

- Add non-apt package managers (pip, cargo, go, npm)
- Add config validation
- Possibly add `binary` field to tools for post-install verification
