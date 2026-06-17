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
class FileMapping:
    source: str          # relative to repo root, e.g. "dotfiles/.bashrc"
    dest: str            # on the target filesystem, may contain {{ home }}
    mode: str = "link"   # link | copy | append | prepend

    @classmethod
    def from_dict(cls, d: dict) -> "FileMapping":
        return cls(
            source=d["source"],
            dest=d["dest"],
            mode=d.get("mode", "link"),
        )


@dataclass
class Tool:
    name: str
    package: str
    method: str = "apt"
    config_source: str = ""
    config_dest: str = ""
    config_mode: str = "link"
    optional: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "Tool":
        return cls(
            name=d["name"],
            package=d.get("package", d["name"]),
            method=d.get("method", "apt"),
            config_source=d.get("config_source", ""),
            config_dest=d.get("config_dest", ""),
            config_mode=d.get("config_mode", "link"),
            optional=d.get("optional", False),
        )

    def has_config(self) -> bool:
        """Whether this tool has an associated config file to deploy."""
        return bool(self.config_source and self.config_dest)

    def to_file_mapping(self) -> FileMapping:
        """Convert the tool's config into a FileMapping."""
        if not self.has_config():
            raise ValueError(f"Tool '{self.name}' has no config")
        return FileMapping(
            source=self.config_source,
            dest=self.config_dest,
            mode=self.config_mode,
        )


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
        result.files = list(parent.files)

    # Merge child's own tools and files
    child_tools = raw.get("tools", [])
    for t in child_tools:
        tool = Tool.from_dict(t)
        result.tools.append(tool)
        # If the tool has config, generate a FileMapping and add/override it
        if tool.has_config():
            fm = tool.to_file_mapping()
            _override_or_append(result.files, fm)

    child_files = raw.get("files", [])
    for f in child_files:
        fm = FileMapping.from_dict(f)
        _override_or_append(result.files, fm)

    return result


def _override_or_append(files: list[FileMapping], fm: FileMapping) -> None:
    """Helper: override existing file with same dest+mode, or append."""
    for i, existing in enumerate(files):
        if existing.dest == fm.dest and existing.mode == fm.mode:
            files[i] = fm
            return
    files.append(fm)


def expand_vars(text: str, home: str) -> str:
    """Replace {{ home }} and other template variables in a string."""
    return text.replace("{{ home }}", home)
