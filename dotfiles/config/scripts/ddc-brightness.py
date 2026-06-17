#!/usr/bin/env python3
"""
Set DDC/CI brightness on all connected external monitors in parallel.

Usage: ddc-brightness.py <percent>   (1-100)
"""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

MONITORS = [
    (12, "DELL P2418D"),
    (13, "LG HDR 4K"),
]


def set_brightness(bus, label, percent):
    result = subprocess.run(
        ["ddcutil", "--bus", str(bus), "setvcp", "0x10", str(percent)],
        capture_output=True, timeout=10,
    )
    return result.returncode == 0


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: ddc-brightness.py <percent>  (1-100)")
        sys.exit(0 if "--help" in sys.argv else 1)

    try:
        pct = int(sys.argv[1])
    except ValueError:
        print(f"Error: not a number: '{sys.argv[1]}'", file=sys.stderr)
        sys.exit(1)

    pct = max(1, min(100, pct))

    print(f"Setting brightness to {pct}%...")
    with ThreadPoolExecutor(max_workers=len(MONITORS)) as pool:
        futures = {
            pool.submit(set_brightness, bus, label, pct): (bus, label)
            for bus, label in MONITORS
        }
        for fut in as_completed(futures):
            bus, label = futures[fut]
            ok = fut.result()
            print(f"  {'✓' if ok else '✗'} bus {bus}: {label}")


if __name__ == "__main__":
    main()
