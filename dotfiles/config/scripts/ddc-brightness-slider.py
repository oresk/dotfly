#!/usr/bin/env python3
"""
Debounced DDC brightness setter for slider/rapid-call use.

Wraps ddc-brightness.py so that bursts of calls collapse into at most one
ddcutil transaction in-flight at a time. The last value always wins.

Usage: ddc-brightness-slider.py <percent>   (1-100)
"""

import fcntl
import subprocess
import sys
import time
from pathlib import Path

PENDING_FILE = Path("/tmp/ddc-brightness-pending")
LOCK_FILE    = Path("/tmp/ddc-brightness.lock")
DEBOUNCE_S   = 0.15

SCRIPT = Path(__file__).parent / "ddc-brightness.py"


def main():
    if len(sys.argv) != 2:
        print("Usage: ddc-brightness-slider.py <percent>", file=sys.stderr)
        sys.exit(1)

    try:
        pct = max(1, min(100, int(sys.argv[1])))
    except ValueError:
        print(f"Error: not a number: '{sys.argv[1]}'", file=sys.stderr)
        sys.exit(1)

    # Write desired value — latest call always wins
    PENDING_FILE.write_text(str(pct))

    # Try to become the process that actually fires ddcutil
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        # Another process holds the lock; it will read the latest pending value
        lock_fd.close()
        return

    # Drain loop: keep applying until the pending value stops changing.
    # This guarantees the final slider position is always sent even if
    # the slider moved while a ddcutil call was in-flight.
    try:
        while True:
            time.sleep(DEBOUNCE_S)
            value = PENDING_FILE.read_text().strip()
            subprocess.run(
                [sys.executable, str(SCRIPT), value],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if PENDING_FILE.read_text().strip() == value:
                break
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


if __name__ == "__main__":
    main()
