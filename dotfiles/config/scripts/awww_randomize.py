#!/usr/bin/env python3

PID_FILE = "/tmp/awww_randomize.pid"

import argparse
import os
import random
import signal
import subprocess
import time
import atexit
from pathlib import Path
from threading import Event

def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.remove(PID_FILE) if os.path.exists(PID_FILE) else None)

def get_focused_monitor():
    try:
        result = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, check=True)
        import json
        monitors = json.loads(result.stdout)
        for monitor in monitors:
            if monitor.get("focused"):
                return monitor["name"]
    except Exception:
        pass
    # Fallback: return None to apply to all outputs
    return None

def get_all_monitors():
    try:
        result = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, check=True)
        import json
        monitors = json.loads(result.stdout)
        return [m["name"] for m in monitors]
    except Exception:
        return []

def get_current_wallpaper():
    try:
        result = subprocess.run(["awww", "query"], capture_output=True, text=True, check=True)
        return Path(result.stdout.strip().split()[-1])
    except Exception:
        return None

def get_random_wallpaper(wallpaper_dir, current_wall):
    images = list(Path(wallpaper_dir).glob("*.[jp][pn]g")) + list(Path(wallpaper_dir).glob("*.jpeg"))
    if current_wall and current_wall in images:
        images = [img for img in images if img != current_wall]
    if not images:
        raise RuntimeError("No wallpapers found or all excluded.")
    return random.choice(images)

def set_wallpaper(wallpaper_path, monitors):
    """Set wallpaper on one or more monitors. monitors can be a string or list."""
    if isinstance(monitors, str):
        monitors = [monitors]
    outputs = ",".join(monitors)
    subprocess.run([
        "awww", "img", "--no-resize", "--transition-type", "fade",
        "--outputs", outputs, str(wallpaper_path)
    ], check=True)

def main():
    parser = argparse.ArgumentParser(
            description="Cycle wallpapers using awww.",
            epilog=f"You can use SIGUSR1 to advance to next wallpaper without waiting for timeout\nkill -SIGUSR1 '$(cat {PID_FILE})'",
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", required=True, help="Directory containing wallpapers")
    parser.add_argument("--interval", type=int, default=360, help="Interval between wallpapers (seconds)")
    parser.add_argument("--monitors", nargs="+", default=None, help="Specific monitor names (e.g. DP-4 DP-5), or omit to auto-detect")
    args = parser.parse_args()
    write_pid()

    change_now = Event()

    def handle_signal(signum, frame):
        print("Received signal to change wallpaper.")
        change_now.set()

    signal.signal(signal.SIGUSR1, handle_signal)

    while True:
        wallpaper_dir = args.dir

        # Determine which monitors to set wallpaper on
        if args.monitors:
            monitors = args.monitors
        else:
            focused = get_focused_monitor()
            if focused:
                monitors = [focused]
            else:
                all_monitors = get_all_monitors()
                if all_monitors:
                    monitors = all_monitors
                else:
                    print("[WARN] Could not detect monitors, applying to all via awww")
                    monitors = []

        current_wall = get_current_wallpaper()
        next_wall = get_random_wallpaper(wallpaper_dir, current_wall)

        print(f"Setting wallpaper: {next_wall} on monitors: {', '.join(monitors) if monitors else 'all'}")
        set_wallpaper(next_wall, monitors)

        # Wait for either the interval to expire or a signal to be received
        change_now.wait(timeout=args.interval)
        change_now.clear()

if __name__ == "__main__":
    main()
