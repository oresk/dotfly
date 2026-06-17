#!/usr/bin/env python3
"""
dotfly — Provision machines from a TOML config.

Usage:
  dotfly --profile <name>                         # local provisioning
  dotfly --profile <name> --host <host>           # remote provisioning
  dotfly --profile <name> --host <host> --user <u> --port <p>
  dotfly --profile <name> --dry-run               # dry run (no changes)
"""

import argparse
import os
import sys
from dataclasses import replace
from pathlib import Path

from .config import load_config, resolve_profile, expand_vars
from .provisioner import provision_locally
from .remote import RemoteProvisioner


def find_repo_root() -> Path:
    """Find the repo root by looking for dotfly.toml in parent directories."""
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / "dotfly.toml").exists():
            return parent
    # Fallback: assume CWD is the repo root
    return cwd


def resolve_home(user: str) -> str:
    """Get the home directory for a given username."""
    import pwd
    try:
        return pwd.getpwnam(user).pw_dir
    except KeyError:
        return f"/home/{user}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="dotfly — provision machines from a TOML config",
    )
    parser.add_argument(
        "-p", "--profile",
        required=True,
        help="Profile name to use (e.g. 'base', 'desktop', 'server')",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Remote hostname or IP (omit for local provisioning)",
    )
    parser.add_argument(
        "-u", "--user",
        default=None,
        help="SSH user (default: root if omitted, or from ~/.ssh/config host block).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=22,
        help="SSH port (default: 22, or from ~/.ssh/config host block)",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to dotfly.toml (default: auto-discovered in repo root)",
    )

    args = parser.parse_args()
    profile_name = args.profile
    is_remote = args.host is not None

    # Find config
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = find_repo_root() / "dotfly.toml"

    if not config_path.exists():
        print(f"Error: config file not found: {config_path}")
        sys.exit(1)

    repo_root = config_path.parent

    print(f"dotfly — config: {config_path}")
    print(f"         profile: {profile_name}")
    if is_remote:
        # Resolve user for display
        display_user = args.user if args.user is not None else "root"
        user_label = f"{display_user}@" if display_user else ""
        port_label = f":{args.port}" if args.port != 22 else ""
        print(f"         remote: {user_label}{args.host}{port_label}")
    if args.dry_run:
        print("         *** DRY RUN — no changes will be made ***")
    print()

    # Load and resolve profile
    raw_config = load_config(config_path)
    try:
        profile = resolve_profile(raw_config, profile_name)
    except (KeyError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Resolved profile '{profile.name}' ({profile.description})")
    print(f"  Tools: {', '.join(t.name for t in profile.tools)}")
    print(f"  Files: {', '.join(f.source for f in profile.files)}")
    print()

    if is_remote:
        # Remote provisioning
        # --user '' (empty) means "use SSH config's User"
        remote_user = args.user
        if remote_user is None:
            remote_user = "root"
        provisioner = RemoteProvisioner(
            host=args.host,
            user=remote_user,
            port=args.port,
            repo_path=repo_root,
        )
        provisioner.provision(profile_name, dry_run=args.dry_run)
    else:
        # Local provisioning — default to current user
        local_user = args.user or os.environ.get("USER", "root")
        home = resolve_home(local_user)

        # Expand {{ home }} in file destinations
        expanded_files = [
            replace(fm, dest=expand_vars(fm.dest, home))
            for fm in profile.files
        ]

        provision_locally(
            tools=profile.tools,
            files=expanded_files,
            repo_root=repo_root,
            home=home,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
