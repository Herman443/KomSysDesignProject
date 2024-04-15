
from sense_hat import SenseHat
import time

# Create an instance of the SenseHat class
sense = SenseHat()

# Colors
red = (255, 0, 0)
green = (0, 255, 0)

# State Machine Definitions
class ToggleStateMachine:
    def __init__(self, sense):
        self.sense = sense
        self.state = 'off'  # Initial state
        
    def toggle(self):
        if self.state == 'off':
            self.state = 'on'
            self.sense.clear(green)
        else:
            self.state = 'off'
            self.sense.clear(red)

# Create state machine instance
state_machine = ToggleStateMachine(sense)

# Main loop
try:
    while True:
        for event in sense.stick.get_events():
            if event.action == 'pressed':
                state_machine.toggle()
        time.sleep(0.1)  # Sleep a little to prevent bouncing
except KeyboardInterrupt:
    sense.clear()  # Turn off all LEDs
