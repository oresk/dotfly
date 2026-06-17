# dotfly

Provision machines from a TOML config: install tools and symlink dotfiles.

```
dotfly --profile desktop --host 192.168.80.x
```

## Quick start

```bash
# Install tools and dotfiles locally
dotfly --profile base

# Or on a remote machine
dotfly --profile desktop --host 192.168.80.50 --user root

# See what would happen without making changes
dotfly --profile base --dry-run
```

## How it works

1. **Reads `dotfly.toml`** which defines profiles with tools and dotfiles.
2. **Resolves the profile** — profiles can inherit from each other.
3. **Local mode** (no `--host`): installs tools via `apt`, symlinks dotfiles.
4. **Remote mode** (with `--host`):
   - SSH into remote, install git + rsync if missing
   - rsync the repo (including `.git`) to the remote
   - Run provisioning on the remote

## Config file (`dotfly.toml`)

Profiles support inheritance via `inherit`. Child profiles add tools/files on top of the parent.

```toml
[profile.base]
description = "Common essentials"

[[profile.base.tools]]
name = "bat"
package = "bat"
method = "apt"

[[profile.base.files]]
source = "dotfiles/.bashrc"
dest = "{{ home }}/.bashrc"

[profile.desktop]
inherit = "base"

[[profile.desktop.tools]]
name = "tmux"
package = "tmux"
method = "apt"

[[profile.desktop.files]]
source = "dotfiles/.bash_aliases"
dest = "{{ home }}/.bash_aliases"
```

### Tool fields

| Field | Description | Required |
|-------|-------------|----------|
| `name` | Display name | Yes |
| `package` | Apt package name (defaults to `name`) | No |
| `method` | Package manager (`apt` only for now) | No |

### File fields

| Field | Description | Required |
|-------|-------------|----------|
| `source` | Path relative to repo root | Yes |
| `dest` | Destination path; `{{ home }}` is expanded | Yes |
| `mode` | `link` (default), `copy`, `append`, or `prepend` | No |

**Modes:**
- `link` — symlink the repo file to the destination (replaces existing)
- `copy` — copy the repo file to the destination (replaces existing)
- `append` — append the source file content to the destination (preserves existing)
- `prepend` — prepend the source file content to the destination (preserves existing)

For `append`/`prepend`, the source file should contain only the snippets you want to add.
The script checks for duplicate content before appending, so running twice is safe.

### Inheritance rules

- Child gets all tools and files from the parent
- Child tools are appended
- Child files with the same `dest` **and** `mode` **override** the parent's
  - A `link` and an `append` to the same dest are treated as separate operations
  - Two `link`s to the same dest: child wins
- `inherit` chains are supported (grandparent → parent → child)
- Circular inheritance raises an error

## CLI

```
usage: dotfly [-h] -p PROFILE [--host HOST] [-u USER] [--port PORT] [-n]

options:
  -p, --profile PROFILE    Profile name (e.g. base, desktop, server)
  --host HOST              Remote hostname/IP (omit for local)
  -u, --user USER          SSH user / home resolver (default: root)
  --port PORT              SSH port (default: 22)
  -n, --dry-run            Show what would be done
```

## Requirements

- Python 3.11+ (uses stdlib `tomllib`)
- Remote machines need SSH access (key-based)
- Currently supports Debian/Ubuntu (apt-based)

## Note on package names vs binary names

On Debian, some packages install binaries with different names:
| Package | Binary |
|---------|--------|
| `bat` | `batcat` |
| `fd-find` | `fdfind` |

The included `dotfiles/.bash_aliases` has aliases for these (`alias cat='batcat'`, `alias fd='fdfind'`).
