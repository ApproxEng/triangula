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
import triangula.util
from euclid import Vector2, Point2

# Construct a HoloChassis object to perform drive calculations, using the convenience
# method to build one with regular triangular geometry and identical wheels. The exact
# number of maximum rotations per second doesn't actually matter, as we're going to
# scale the output of the joystick such that we hit whatever this value is when at the
# extreme ranges of the stick.
chassis = triangula.chassis.get_regular_triangular_chassis(
    wheel_distance=200,
    wheel_radius=60,
    max_rotations_per_second=1.0)

# Maximum translation speed in mm/s
max_trn = chassis.get_max_translation_speed()
# Maximum rotation speed in radians/2
max_rot = chassis.get_max_rotation_speed()
# Show max speeds
print (max_trn, max_rot)

# Connect to the Arduino Nano over I2C, motors and lights are attached to the nano
arduino = triangula.arduino.Arduino()
arduino.set_lights(200, 255, 100)

# Hold whether we're navigating in relative or absolute terms, and what our correction is
state = {'bearing_zero': None,
         'last_bearing': 0.0}

# Start up the display, show the IP address
lcd = triangula.lcd.LCD()
lcd.cursor_off()
lcd.set_text(row1='Triangula', row2=triangula.util.get_ip_address())


def signal_handler_sigint(signum, frame):
    arduino.set_motor_power(0, 0, 0)
    arduino.set_lights(200, 255, 40)
    lcd.set_text(row1='Service shutdown', row2='SIGINT received')
    sys.exit(0)


def signal_handler_sigterm(signum, frame):
    arduino.set_motor_power(0, 0, 0)
    arduino.set_lights(200, 255, 40)
    lcd.set_text(row1='Service shutdown', row2='SIGTERM received')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler_sigint)
signal.signal(signal.SIGTERM, signal_handler_sigterm)


def set_absolute_motion(button=None):
    """
    Lock motion to be compass relative, zero point (forwards) is the current bearing
    """
    lcd.set_backlight(0, 10, 0)
    sleep(0.05)
    lcd.set_text(row1='Manual Control', row2='Absolute Motion')
    sleep(0.05)
    state['bearing_zero'] = state['last_bearing']


def set_relative_motion(button=None):
    """
    Set motion to be relative to the robot's reference frame
    """
    lcd.set_backlight(10, 0, 0)
    sleep(0.05)
    lcd.set_text(row1='Manual Control', row2='Relative Motion')
    sleep(0.05)
    state['bearing_zero'] = None


def show_encoder_values(button=None):
    """
    Show encoder values
    """
    lcd.set_backlight(red=8, green=4, blue=4)
    sleep(0.05)
    (a, b, c) = arduino.get_encoder_values()
    lcd.set_text(row1='p={} y={}'.format(str(a).ljust(6), b), row2='g={} Enc.'.format(str(c).ljust(6)))
    sleep(0.05)


while 1:
    try:
        with triangula.input.SixAxisResource(bind_defaults=True) as joystick:

            lcd.set_text(row1='Triangula', row2='Controller found')
            arduino.set_lights(100, 255, 100)

            # Bind motion mode buttons
            joystick.register_button_handler(set_absolute_motion, triangula.input.SixAxis.BUTTON_SQUARE)
            joystick.register_button_handler(set_relative_motion, triangula.input.SixAxis.BUTTON_TRIANGLE)
            joystick.register_button_handler(show_encoder_values, triangula.input.SixAxis.BUTTON_CIRCLE)

            set_relative_motion()

            while 1:
                # Read the current fusion pose from the IMU, getting the bearing
                bearing = triangula.imu.read()['fusionPose'][2]
                if bearing is not None:
                    state['last_bearing'] = bearing

                # Get a vector from the left hand analogue stick and scale it up to our
                # maximum translation speed, this will mean we go as fast directly forwards
                # as possible when the stick is pushed fully forwards
                translate = Vector2(
                    joystick.axes[0].corrected_value(),
                    joystick.axes[1].corrected_value()) * max_trn

                # If we're in absolute mode, rotate the translation vector appropriately
                if state['bearing_zero'] is not None:
                    translate = triangula.chassis.rotate_vector(translate,
                                                                state['last_bearing'] - state['bearing_zero'])

                # Get the rotation in radians per second from the right hand stick's X axis,
                # scaling it to our maximum rotational speed. When standing still this means
                # that full right on the right hand stick corresponds to maximum speed
                # clockwise rotation.
                rotate = joystick.axes[2].corrected_value() * max_rot

                # Given the translation vector and rotation, use the chassis object to calculate
                # the speeds required in revolutions per second for each wheel. As we set the
                # maximum wheel speeds to 1.0, all speeds will range from -1.0 to 1.0.
                # This is a :class:`triangula.chassis.WheelSpeeds` containing the speeds and any
                # scaling applied to bring the requested velocity within the range the chassis can
                # actually perform.
                wheel_speeds = chassis.get_wheel_speeds(
                    translation=translate,
                    rotation=rotate,
                    origin=Point2(0, 0))
                speeds = wheel_speeds.speeds

                # Send desired motor speed values over the I2C bus to the Arduino, which will
                # then send the appropriate messages to the Syren10 controllers over its serial
                # line as well as lighting up a neopixel ring to provide additional feedback
                # and bling.
                arduino.set_motor_power(speeds[0], speeds[1], speeds[2])
    except IOError:
        lcd.set_text(row1='Waiting for ps3', row2='controller...')
