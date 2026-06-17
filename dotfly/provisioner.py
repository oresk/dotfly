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


def _apply_file_mode(
    fm: FileMapping,
    src: Path,
    dst: Path,
    *,
    dry_run: bool = False,
) -> None:
    """Apply a single file mapping according to its mode."""
    # link — symlink (works for files and directories)
    if fm.mode == "link":
        kind = "dir" if src.is_dir() else "file"

        if dst.exists() or dst.is_symlink():
            if dst.is_symlink() and os.readlink(dst) == str(src):
                print(f"  Already linked: {dst}")
                return
            print(f"  Backing up existing {kind}: {dst} → {dst}.bak")
            dst.rename(dst.with_suffix(".bak"))

        dst.symlink_to(src)
        print(f"  Linked {kind}: {src} → {dst}")
        return

    # copy — regular file copy
    if fm.mode == "copy":
        if dst.exists():
            if dst.is_symlink():
                dst.unlink()
            else:
                print(f"  Backing up existing: {dst} → {dst}.bak")
                dst.rename(dst.with_suffix(".bak"))
        import shutil
        shutil.copy2(src, dst)
        print(f"  Copied: {src} → {dst}")
        return

    # append — append source content to destination
    if fm.mode == "append":
        content = src.read_text()
        if dst.exists():
            existing = dst.read_text()
            if content in existing:
                print(f"  Already appended: {src} → {dst}")
                return
            with open(dst, "a") as f:
                f.write("\n")
                f.write(content)
        else:
            dst.write_text(content)
        print(f"  Appended: {src} → {dst}")
        return

    # prepend — prepend source content to destination
    if fm.mode == "prepend":
        content = src.read_text()
        if dst.exists():
            existing = dst.read_text()
            if content in existing:
                print(f"  Already prepended: {src} → {dst}")
                return
            with open(dst, "w") as f:
                f.write(content)
                f.write("\n")
                f.write(existing)
        else:
            dst.write_text(content)
        print(f"  Prepended: {src} → {dst}")
        return

    print(f"  WARNING: Unknown mode '{fm.mode}' for {fm.source}, skipping")


def process_files(
    files: list[FileMapping],
    repo_root: Path,
    home: str,
    *,
    dry_run: bool = False,
) -> None:
    """Process dotfiles: link, copy, append, or prepend from repo to destinations.

    For each file mapping:
      source: relative path within the repo (e.g. 'dotfiles/.bashrc')
      dest:   absolute path on the filesystem (e.g. '/home/user/.bashrc')
      mode:   link | copy | append | prepend (default: link)

    Variables like {{ home }} in dest should already be expanded.
    """
    for fm in files:
        src = repo_root / fm.source
        dst = Path(fm.dest)

        if not src.exists():
            print(f"  WARNING: source '{src}' does not exist, skipping")
            continue

        if dry_run:
            action = {
                "link": f"Would symlink {src} → {dst}",
                "copy": f"Would copy {src} → {dst}",
                "append": f"Would append {src} → {dst}",
                "prepend": f"Would prepend {src} → {dst}",
            }.get(fm.mode, f"Would process {src} → {dst} (mode={fm.mode})")
            print(f"  (dry-run) {action}")
            continue

        # Ensure parent directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)

        _apply_file_mode(fm, src, dst, dry_run=dry_run)


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

    print("\n=== Processing dotfiles ===")
    process_files(files, repo_root, home, dry_run=dry_run)

    print("\n=== Done ===")
