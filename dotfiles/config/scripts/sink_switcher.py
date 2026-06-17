#!/usr/bin/env python3
import pulsectl
from pprint import pprint

def cycle_to_next_sink():
    with pulsectl.Pulse('cycle-sink') as pulse:
        sinks = pulse.sink_list()
        for sink in sinks:
            pprint(f"Sinks available: {sink}")
        default_sink_name = pulse.server_info().default_sink_name
        
        # Find the index of the current default sink
        current_index = next((i for i, sink in enumerate(sinks) if sink.name == default_sink_name), None)

        if current_index is None:
            print("Current default sink not found.")
            return

        # Calculate the next sink index (cycling)
        next_index = (current_index + 1) % len(sinks)
        next_sink = sinks[next_index]

        # Set the new default sink
        pulse.sink_default_set(next_sink)

        # Move all active audio streams to the new default sink
        for input_sink in pulse.sink_input_list():
            pulse.sink_input_move(input_sink.index, next_sink.index)

        print(f"Switched default sink to: {next_sink.description}")

if __name__ == "__main__":
    cycle_to_next_sink()

