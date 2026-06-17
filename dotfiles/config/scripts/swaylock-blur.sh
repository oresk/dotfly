#!/bin/bash
# Use the current awww wallpaper, blur it, and show in swaylock

TMPDIR="$HOME/.cache/swaylock-blur"
mkdir -p "$TMPDIR"

# Get the current wallpaper from awww (take the first output's image)
CURRENT_WALL=$(awww query 2>/dev/null | grep "image:" | head -1 | sed 's/.*image: //')

if [ -z "$CURRENT_WALL" ] || [ ! -f "$CURRENT_WALL" ]; then
    # Fallback: use a default wallpaper
    CURRENT_WALL="$HOME/.config/wallpapers/crveno.png"
fi

BLURRED="$TMPDIR/blurred_current.png"

# Blur the current wallpaper (sigma 25 = heavy blur)
magick "$CURRENT_WALL" -blur 0x25 "$BLURRED" 2>/dev/null

# Start swaylock with the blurred wallpaper
swaylock \
  --image="$BLURRED" \
  --scaling=center \
  --color=000000 \
  --indicator-radius=60 \
  --indicator-thickness=8 \
  --indicator-idle-visible \
  --ring-color=00000080 \
  --ring-clear-color=00000060 \
  --ring-ver-color=2196F3 \
  --ring-wrong-color=FF5252 \
  --ring-caps-lock-color=FF9800 \
  --inside-color=000000cc \
  --inside-clear-color=000000aa \
  --inside-ver-color=2196F330 \
  --inside-wrong-color=FF525230 \
  --inside-caps-lock-color=FF980030 \
  --line-color=00000000 \
  --line-ver-color=2196F3 \
  --line-wrong-color=FF5252 \
  --line-caps-lock-color=FF9800 \
  --text-color=FFFFFFcc \
  --text-clear-color=FFFFFF90 \
  --text-ver-color=2196F3 \
  --text-wrong-color=FF5252 \
  --text-caps-lock-color=FF9800 \
  --font="JetBrainsMono Nerd Font" \
  --font-size=20 \
  --indicator-caps-lock \
  --disable-caps-lock-text \
  --show-failed-attempts \
  --daemonize
