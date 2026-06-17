#!/usr/bin/env python3
import argparse
import subprocess
import sys
import re


TAILSCALE_SUBNETS = [
    "192.168.80.0/24",
    "192.168.50.0/24",
]


def run(cmd, check=True):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)


def get_local_subnets():
    """Return subnets directly connected via physical interfaces (not tailscale0)."""
    result = run("ip route show table main")
    local = []
    for line in result.stdout.splitlines():
        # Skip tailscale and loopback
        if "tailscale0" in line or "lo" in line:
            continue
        # Match connected subnets (proto kernel scope link)
        m = re.search(r"(\d+\.\d+\.\d+\.\d+/\d+)", line)
        if m and "scope link" in line:
            local.append(m.group(1))
    return local


def tailscale_up():
    print("Starting Tailscale with --accept-routes...")
    run("tailscale up --accept-routes")

    local_subnets = get_local_subnets()
    print(f"Detected local subnets: {local_subnets}")

    for subnet in TAILSCALE_SUBNETS:
        if subnet in local_subnets:
            print(f"Removing conflicting route {subnet} from table 52...")
            result = run(f"ip route del {subnet} dev tailscale0 table 52", check=False)
            if result.returncode == 0:
                print(f"  Removed {subnet}")
            else:
                print(f"  Could not remove {subnet}: {result.stderr.strip()}")

    print("Done.")


def tailscale_down():
    print("Stopping Tailscale...")
    run("tailscale down")
    print("Done.")


def list_routes():
    main = run("ip route show table main")
    ts = run("ip route show table 52", check=False)

    local_subnets = get_local_subnets()

    print("=== Local subnets (physical) ===")
    for s in local_subnets:
        print(f"  {s}")

    print("\n=== Tailscale routes (table 52) ===")
    for line in ts.stdout.splitlines():
        m = re.search(r"(\d+\.\d+\.\d+\.\d+(?:/\d+)?)", line)
        if not m:
            continue
        subnet = m.group(1)
        conflict = " ⚠ conflicts with local" if subnet in local_subnets else ""
        print(f"  {subnet}{conflict}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tailscale manager with subnet conflict handling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("up", help="Start Tailscale and remove conflicting local routes")
    subparsers.add_parser("down", help="Stop Tailscale")
    subparsers.add_parser("list", help="List local and Tailscale routes")

    args = parser.parse_args()

    if args.command == "up":
        tailscale_up()
    elif args.command == "down":
        tailscale_down()
    elif args.command == "list":
        list_routes()
