
from sense_hat import SenseHat
import time

sense = SenseHat()

red = (255, 0, 0)
green = (0, 255, 0)

# State Machine
class ToggleStateMachine:
    def __init__(self, sense):
        self.sense = sense
        self.state = 'charger unconnected'
        
    def toggle(self):
        if self.state == 'charger unconnected':
            self.state = 'charger connected'
            self.sense.clear(green)
            # send message of new state (on)
        else:
            self.state = 'charger unconnected'
            self.sense.clear(red)
            # send message of new state (off)


state_machine = ToggleStateMachine(sense)

try:
    while True:
        for event in sense.stick.get_events():
            if event.action == 'pressed':
                state_machine.toggle()
                print(state_machine.state)
        time.sleep(0.1)  # Sleep a little to prevent bouncing
except KeyboardInterrupt:
    sense.clear()  # Turn off all LEDs
