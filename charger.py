from sense_hat import SenseHat
import time

# Create an instance of the SenseHat class
sense = SenseHat()

# Colors
red = (255, 0, 0)
green = (0, 255, 0)

# Initially set to red
current_color = red

def toggle_color():
    global current_color
    if current_color == red:
        current_color = green
    else:
        current_color = red
    sense.clear(current_color)  # Update the display with the new color

# Main loop
try:
    while True:
        for event in sense.stick.get_events():
            if event.action == 'pressed':
                toggle_color()
        time.sleep(0.1)  # Sleep a little to prevent bouncing

except KeyboardInterrupt:
    sense.clear()  # Turn off all LEDs
