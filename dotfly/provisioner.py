"""
provisioner.py — Installing tools and symlinking dotfiles on the local machine.
"""

import os
import subprocess
import shlex
from pathlib import Path

from .config import Tool, FileMapping


def _sudo_prefix() -> list[str]:
    """Return sudo prefix if not already running as root."""
    if os.geteuid() == 0:
        return []
    return ["sudo"]


def install_tools(tools: list[Tool], *, dry_run: bool = False) -> None:
    """Install a list of tools via the specified package manager."""
    apt_packages = [t.package for t in tools if t.method == "apt"]
    if not apt_packages:
        return

    sudo = _sudo_prefix()
    sudo_str = " ".join(sudo) + " " if sudo else ""

    print(f"Apt packages to install: {', '.join(apt_packages)}")

    if dry_run:
        print(f"  (dry-run) Would run: {sudo_str}apt install -y {' '.join(shlex.quote(p) for p in apt_packages)}")
        return

    # Update apt cache first
    print("  Updating apt cache...")
    subprocess.run(sudo + ["apt", "update", "-qq"], check=False)

    # Install packages one by one for clearer error reporting
    installed = 0
    failed: list[str] = []
    for pkg in apt_packages:
        print(f"  Installing {pkg}...")
        cmd = sudo + ["apt", "install", "-y", pkg]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    FAILED: {result.stderr.strip()}")
            failed.append(pkg)
        else:
            installed += 1

    if failed:
        raise RuntimeError(f"Failed to install packages: {', '.join(failed)}")
    print(f"  Done. ({installed} packages installed)")


def symlink_files(
    files: list[FileMapping],
    repo_root: Path,
    home: str,
    *,
    dry_run: bool = False,
) -> None:
    """Symlink dotfiles from the repo to their destinations.

    For each file mapping:
      source: relative path within the repo (e.g. 'dotfiles/.bashrc')
      dest:   absolute path on the filesystem (e.g. '/home/user/.bashrc')

    Variables like {{ home }} in dest should already be expanded.
    """
    for fm in files:
        src = repo_root / fm.source
        dst = Path(fm.dest)

        if not src.exists():
            print(f"  WARNING: source '{src}' does not exist, skipping")
            continue

        if dry_run:
            print(f"  (dry-run) Would symlink: {src} → {dst}")
            continue

        # Ensure parent directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing file/symlink if present
        if dst.exists() or dst.is_symlink():
            if dst.is_symlink() and os.readlink(dst) == str(src):
                print(f"  Already linked: {dst}")
                continue
            print(f"  Backing up existing: {dst} → {dst}.bak")
            dst.rename(dst.with_suffix(".bak"))

        # Create the symlink
        dst.symlink_to(src)
        print(f"  Linked: {src} → {dst}")


def provision_locally(
    tools: list[Tool],
    files: list[FileMapping],
    repo_root: Path,
    home: str,
    *,
    dry_run: bool = False,
) -> None:
    """Run local provisioning: install tools + symlink files."""
    print("=== Installing tools ===")
    install_tools(tools, dry_run=dry_run)

    print("\n=== Symlinking dotfiles ===")
    symlink_files(files, repo_root, home, dry_run=dry_run)

    print("\n=== Done ===")
