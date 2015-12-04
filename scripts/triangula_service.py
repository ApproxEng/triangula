#!/home/pi/triangula/env/bin/python
"""
Triangula top level service script
"""

import signal
import sys
from time import sleep

import triangula.arduino
import triangula.chassis
import triangula.imu
import triangula.input
import triangula.lcd
import triangula.task
import triangula.util


def get_shutdown_handler(message=None):
    """
    Build a shutdown handler, called from the signal methods in response to e.g. SIGTERM

    :param message:
        The message to show on the second line of the LCD, if any. Defaults to None
    """

    def handler(signum, frame):
        arduino.set_motor_power(0, 0, 0)
        arduino.set_lights(0, 0, 40)
        lcd.set_backlight(red=5, green=5, blue=5)
        sleep(0.05)
        lcd.set_text(row1='Service shutdown', row2=message)
        sleep(0.05)
        sys.exit(0)

    return handler


signal.signal(signal.SIGINT, get_shutdown_handler('SIGINT received'))
signal.signal(signal.SIGTERM, get_shutdown_handler('SIGTERM received'))

# Start up the display
lcd = triangula.lcd.LCD()

# Construct a HoloChassis object to perform drive calculations, using the convenience
# method to build one with regular triangular geometry and identical wheels.
chassis = triangula.chassis.get_regular_triangular_chassis(
    wheel_distance=290,
    wheel_radius=60,
    max_rotations_per_second=1.0)

# Connect to the Arduino Nano over I2C, motors and lights are attached to the nano
arduino = triangula.arduino.Arduino()

while 1:
    try:
        with triangula.input.SixAxisResource(bind_defaults=True) as joystick:
            lcd.set_text(row1='Triangula', row2='Controller found')
            task_manager = triangula.task.TaskManager(arduino=arduino, lcd=lcd, joystick=joystick, chassis=chassis)
            task_manager.run(initial_task=triangula.task.MenuTask())
    except IOError:
        lcd.set_text(row1='Waiting for PS3', row2='controller...')
