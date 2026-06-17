#!/bin/bash
# Triggered by udev when the dock's USB hub is removed.
# Runs hyprctl reload as user lovro to re-enable eDP-1.

export XDG_RUNTIME_DIR=/run/user/1000
HYPRLAND_INSTANCE_SIGNATURE=$(ls /run/user/1000/hypr/ | head -1)
export HYPRLAND_INSTANCE_SIGNATURE

sleep 0.5
su lovro -c "hyprctl reload" 2>&1 | logger -t dock-undock
