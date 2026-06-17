#!/bin/bash

# Hyprland 0.55 regression: keyword monitor cannot re-enable a disabled
# monitor when it's the only monitor (see github.com/hyprwm/Hyprland/discussions/14496).
# Workaround: use DPMS off/on instead of disable/enable.

SOCKET="/run/user/$(id -u)/hypr/$(ls /run/user/$(id -u)/hypr/)/.socket2.sock"
LOGFILE="/tmp/auto-monitor.log"

echo "$(date): auto-monitor started, socket=$SOCKET" >> "$LOGFILE"

socat -U - UNIX-CONNECT:"$SOCKET" | \
while read -r event; do
    echo "$(date): EVENT: $event" >> "$LOGFILE"
    if [[ "$event" == "monitoradded>>"* || "$event" == "monitorremoved>>"* ]]; then
        echo "$(date): monitor event detected, sleeping..." >> "$LOGFILE"
        sleep 0.5
        if hyprctl monitors | grep -q "LG HDR 4K"; then
            echo "$(date): LG HDR 4K found → disabling eDP-1" >> "$LOGFILE"
            hyprctl keyword monitor "eDP-1, disable" >> "$LOGFILE" 2>&1
        else
            echo "$(date): LG HDR 4K not found → reloading to enable eDP-1" >> "$LOGFILE"
            hyprctl reload >> "$LOGFILE" 2>&1
        fi
    fi
done
