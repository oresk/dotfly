"""
remote.py — SSH orchestration for remote provisioning.

Workflow:
  1. Check SSH agent has keys loaded
  2. SSH into remote → install git
  3. rsync the local repo (including .git) to the remote
  4. Execute `dotfly --profile <name>` on the remote (local provisioning mode)

SSH config: dotfly respects ~/.ssh/config. If you don't pass --user or --port,
those will be picked up from your SSH config Host block.
"""

import subprocess
import shlex
from pathlib import Path


def check_ssh_agent() -> None:
    """Check that the SSH agent has identities loaded. Raises RuntimeError if not."""
    result = subprocess.run(
        ["ssh-add", "-l"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 1:
        raise RuntimeError(
            "SSH agent has no identities. "
            "Unlock KeePassXC (or load your SSH keys) and try again."
        )
    if result.returncode == 2:
        raise RuntimeError(
            "SSH agent is not running. "
            "Start ssh-agent and add your keys."
        )


class RemoteProvisioner:
    """Handles the remote side of provisioning.

    Args:
        host: Hostname or SSH alias (required).
        repo_path: Local path to the dotfly repo.
        user: SSH user (None = let ~/.ssh/config decide).
        port: SSH port (22 = let ~/.ssh/config decide).
        remote_dir: Directory on the remote to sync to.
    """

    def __init__(
        self,
        host: str,
        repo_path: Path,
        user: str | None = None,
        port: int = 22,
        remote_dir: str | None = None,
    ):
        self.host = host
        self.user = user
        self.port = port
        self.repo_path = repo_path.resolve()
        self.remote_dir = remote_dir or "~/dotfly"

    def _ssh_base_args(self) -> list[str]:
        """Build the base SSH arguments from config settings.

        Only adds -p and -o options when they differ from defaults,
        so ~/.ssh/config Host blocks take precedence.
        """
        args: list[str] = [
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=10",
        ]
        if self.port != 22:
            args = ["-p", str(self.port)] + args
        return args

    @property
    def ssh_dest(self) -> str:
        """Return the SSH destination string.

        If user is empty or None, omit the user@ prefix so
        ~/.ssh/config can supply the User.
        """
        if self.user:
            return f"{self.user}@{self.host}"
        return self.host

    def ssh(
        self,
        command: str,
        *,
        check: bool = True,
        capture: bool = True,
        tty: bool = False,
    ) -> subprocess.CompletedProcess:
        """Run a command on the remote machine via SSH."""
        ssh_cmd = ["ssh"] + self._ssh_base_args()
        if tty:
            ssh_cmd.append("-t")
        ssh_cmd.extend([self.ssh_dest, command])

        kwargs = {}
        if capture:
            kwargs["capture_output"] = True
            kwargs["text"] = True

        return subprocess.run(ssh_cmd, check=check, **kwargs)

    def _rsync_e_args(self) -> str:
        """Return the -e argument for rsync, respecting SSH config."""
        parts = ["ssh"]
        if self.port != 22:
            parts.extend(["-p", str(self.port)])
        parts.extend(["-o", "StrictHostKeyChecking=accept-new"])
        return " ".join(parts)

    def ensure_prerequisites(self) -> None:
        """Check Python version and install git/rsync on the remote if needed."""
        print("  Checking prerequisites...")

        # Check Python version first
        py_check = self.ssh(
            "python3 -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")'",
            check=False,
        )
        if py_check.returncode == 255:
            raise RuntimeError(
                f"Cannot connect to {self.ssh_dest}. "
                "Check the hostname and your network connection."
            )
        if py_check.returncode != 0:
            raise RuntimeError(
                "Python 3 is not installed on the remote machine. "
                "Please install python3 (>= 3.11) and try again."
            )
        py_version = py_check.stdout.strip()
        major, minor = py_version.split(".")
        if int(major) < 3 or (int(major) == 3 and int(minor) < 11):
            raise RuntimeError(
                f"Remote has Python {py_version}, but Python >= 3.11 is required."
            )
        print(f"    Python {py_version} — OK")

        # Check / install git and rsync
        missing = []
        for cmd in ("git", "rsync"):
            result = self.ssh(f"which {cmd}", check=False)
            if result.returncode != 0:
                missing.append(cmd)

        if not missing:
            print("    git, rsync — already installed")
            return

        print(f"    Installing: {', '.join(missing)}")
        self.ssh(
            "apt-get update -qq && apt-get install -y -qq "
            + " ".join(missing)
        )
        print("    Prerequisites installed")

    def rsync_repo(self) -> None:
        """Rsync the local repo (including .git) to the remote."""
        print(f"  Syncing repo to {self.ssh_dest}:{self.remote_dir} ...")

        # Ensure parent directory exists on remote
        if self.remote_dir.startswith("~"):
            self.ssh(f"mkdir -p {self.remote_dir}", check=False)
        else:
            self.ssh(f"mkdir -p {shlex.quote(self.remote_dir)}", check=False)

        rsync_cmd = [
            "rsync",
            "-avz",
            "--delete",
            "--exclude", "__pycache__",
            "--exclude", "*.pyc",
            "--exclude", ".venv",
            "--exclude", "venv",
            "-e", self._rsync_e_args(),
            f"{self.repo_path}/",
            f"{self.ssh_dest}:{self.remote_dir}/",
        ]
        result = subprocess.run(rsync_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    rsync error:\n{result.stderr}")
            raise RuntimeError(f"rsync failed: {result.stderr}")
        print("    Repo synced")

    def _dotfly_command(self) -> str:
        """Return the command to run dotfly on the remote machine."""
        if self.remote_dir.startswith("~"):
            cd_cmd = f"cd {self.remote_dir}"
        else:
            cd_cmd = f"cd {shlex.quote(self.remote_dir)}"
        return f"{cd_cmd} && python3 -m dotfly"

    def execute_remote(self, profile_name: str, *, dry_run: bool = False) -> None:
        """Execute dotfly provisioning on the remote machine."""
        cmd = self._dotfly_command()
        cmd += f" --profile {shlex.quote(profile_name)}"
        if dry_run:
            cmd += " --dry-run"

        print(f"  Executing on remote: {cmd}")
        result = self.ssh(cmd, capture=False, tty=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Remote execution failed with exit code {result.returncode}"
            )
        print("  Remote provisioning finished")

    def provision(self, profile_name: str, *, dry_run: bool = False) -> None:
        """Full remote provisioning workflow."""
        label = self.ssh_dest if not self.user else f"{self.user}@{self.host}"
        print(f"\n=== Remote provisioning: {label} ===\n")

        if dry_run:
            print("  *** DRY RUN — no SSH commands will be executed ***\n")
            print("  [1/3] Would check Python + install prerequisites (git, rsync)")
            print("  [2/3] Would rsync repo to remote")
            print(f"  [3/3] Would run provisioning with profile '{profile_name}'")
            print(f"        → {self._dotfly_command()} --profile {profile_name}")
            print("\n=== Remote provisioning complete (dry-run) ===")
            return

        check_ssh_agent()

        print("  [1/3] Ensure prerequisites (git, rsync) are installed on remote")
        self.ensure_prerequisites()

        print("  [2/3] Sync repo to remote")
        self.rsync_repo()

        print("  [3/3] Run dotfly provisioning on remote")
        self.execute_remote(profile_name, dry_run=False)

        print("\n=== Remote provisioning complete ===")
