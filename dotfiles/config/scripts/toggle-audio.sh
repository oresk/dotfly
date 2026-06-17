#!/usr/bin/env bash

HDMI_SINK="alsa_output.pci-0000_07_00.1.HiFi__HDMI1__sink"
PCM_SINK="alsa_output.usb-Burr-Brown_from_TI_USB_Audio_DAC-00.analog-stereo"

current=$(pactl get-default-sink)

if [[ "$current" == "$HDMI_SINK" ]]; then
    pactl set-default-sink "$PCM_SINK"
    notify-send -i /usr/share/icons/Papirus/48x48/devices/audio-headphones.svg "Audio Output" "Switched to PCM2706 (USB DAC)"
else
    pactl set-default-sink "$HDMI_SINK"
    notify-send -i /usr/share/icons/Papirus/48x48/devices/video-display.svg "Audio Output" "Switched to HDMI1"
fi

# Move all active streams to the new default sink
new_default=$(pactl get-default-sink)
pactl list sink-inputs short | awk '{print $1}' | while read -r input; do
    pactl move-sink-input "$input" "$new_default"
done
