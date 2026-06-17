#!/bin/bash
# Triggered by udev when the dock's USB hub is removed.
# Runs hyprctl reload to re-enable eDP-1.
#
# The Hyprland user is determined dynamically by scanning /run/user/*/hypr/.

HYPR_USER=""
for d in /run/user/*/hypr/; do
    uid=$(echo "$d" | cut -d/ -f4)
    HYPR_USER=$(id -nu "$uid" 2>/dev/null)
    [ -n "$HYPR_USER" ] && break
done

if [ -z "$HYPR_USER" ]; then
    logger -t dock-undock "Could not determine Hyprland user"
    exit 1
fi

XDG_RUNTIME_DIR="/run/user/$(id -u "$HYPR_USER")"
HYPRLAND_INSTANCE_SIGNATURE=$(ls "$XDG_RUNTIME_DIR/hypr/" | head -1)
export XDG_RUNTIME_DIR HYPRLAND_INSTANCE_SIGNATURE

sleep 0.5
su "$HYPR_USER" -c "hyprctl reload" 2>&1 | logger -t dock-undock
