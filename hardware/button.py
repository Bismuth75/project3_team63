from gpiozero import Button
import constants as c

class Switch:
    def __init__(self):
        self.button = Button(c.BUTTON_PORT, pull_up=False, bounce_time=0.05)
        self.on = False
        self.button.when_pressed = self.toggle

    def toggle(self):
        self.on = not self.on

    def get_button(self):
        return self.button.is_pressed

if __name__ == "__main__":
    switch = Switch()
    try:
        while True:
            print(switch.get_button())
    except KeyboardInterrupt:
        print("terminated")