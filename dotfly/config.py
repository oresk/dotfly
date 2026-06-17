"""
config.py — TOML loading and profile resolution with inheritance.

A profile can inherit from another profile using the `inherit` key.
When inheriting, the child gets all tools and files from the parent.
Child tools are appended; child files with the same `dest` override the parent's.
"""

import tomllib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Tool:
    name: str
    package: str
    method: str = "apt"

    @classmethod
    def from_dict(cls, d: dict) -> "Tool":
        return cls(
            name=d["name"],
            package=d.get("package", d["name"]),
            method=d.get("method", "apt"),
        )


@dataclass
class FileMapping:
    source: str          # relative to repo root, e.g. "dotfiles/.bashrc"
    dest: str            # on the target filesystem, may contain {{ home }}

    @classmethod
    def from_dict(cls, d: dict) -> "FileMapping":
        return cls(source=d["source"], dest=d["dest"])


@dataclass
class ResolvedProfile:
    name: str
    description: str = ""
    tools: list[Tool] = field(default_factory=list)
    files: list[FileMapping] = field(default_factory=list)


def load_config(path: str | Path) -> dict:
    """Load a TOML config file and return the raw dict."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "rb") as f:
        return tomllib.load(f)


def resolve_profile(
    raw_config: dict,
    profile_name: str,
    seen: Optional[set[str]] = None,
) -> ResolvedProfile:
    """Resolve a profile by merging inherited profiles.

    Circular inheritance will raise a ValueError.
    """
    if seen is None:
        seen = set()

    if profile_name in seen:
        raise ValueError(f"Circular inheritance detected for profile '{profile_name}'")
    seen.add(profile_name)

    # Get raw profile data
    raw_profiles = raw_config.get("profile", {})
    raw = raw_profiles.get(profile_name)
    if raw is None:
        raise KeyError(f"Profile '{profile_name}' not found in config")

    # Start with an empty profile
    result = ResolvedProfile(name=profile_name, description=raw.get("description", ""))

    # If inheriting, resolve the parent first
    inherit = raw.get("inherit")
    if inherit:
        parent = resolve_profile(raw_config, inherit, seen)
        result.tools = list(parent.tools)
        # Build a map of parent files by dest for override logic
        parent_files_by_dest: dict[str, FileMapping] = {}
        for f in parent.files:
            parent_files_by_dest[f.dest] = f
        result.files = list(parent.files)

    # Merge child's own tools and files
    child_tools = raw.get("tools", [])
    for t in child_tools:
        result.tools.append(Tool.from_dict(t))

    child_files = raw.get("files", [])
    for f in child_files:
        fm = FileMapping.from_dict(f)
        # Override parent file with same dest
        idx = None
        for i, existing in enumerate(result.files):
            if existing.dest == fm.dest:
                idx = i
                break
        if idx is not None:
            result.files[idx] = fm
        else:
            result.files.append(fm)

    return result


def expand_vars(text: str, home: str) -> str:
    """Replace {{ home }} and other template variables in a string."""
    return text.replace("{{ home }}", home)
