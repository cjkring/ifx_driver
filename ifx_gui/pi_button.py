from gpiozero import Button
from time import sleep

def button_on(button):
    print(f'Pressed {button}')
    
def button_held(button): 
    print(f'Held {button}')

def button_off(button):
    print(f'Released {button}')

from numpy import arange
for gpio in [27,23,22,18]:
    try:
        button = Button(int(gpio), hold_time = 0.25, hold_repeat=True)
        button.when_activated = button_on
        button.when_held = button_held
        button.when_deactivated = button_off
    except Exception as e:
        print(f'GPIO {gpio}: {e}')

while True:
    #if button.is_pressed:
    #    print("Pressed")
    #else:
    #    print("Released")
    sleep(1)