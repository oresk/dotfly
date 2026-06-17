#!/bin/bash

if hyprctl monitors | grep -q "Monitor eDP-1"; then
    hyprctl keyword monitor "eDP-1, disable"
    echo "eDP-1 disabled."
else
    hyprctl keyword monitor "eDP-1, preferred, auto, 1"
    echo "eDP-1 enabled."
fi

