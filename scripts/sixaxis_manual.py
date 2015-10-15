# Simple manual drive, left hand analogue stick controls translation relative to the
# robot's axis, right hand X axis controls rotation around the centre of the robot.

import triangula.chassis
import triangula.arduino
import triangula.input
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

# Get a joystick, this will fail unless the SixAxis controller is paired and active
with triangula.input.SixAxisResource(bind_defaults=True) as joystick:
    while 1:
        # Get a vector from the left hand analogue stick and scale it up to our
        # maximum translation speed, this will mean we go as fast directly forwards
        # as possible when the stick is pushed fully forwards
        translate = Vector2(
            joystick.axes[0].corrected_value(),
            joystick.axes[1].corrected_value()) * max_trn

        # Get the rotation in radians per second from the right hand stick's X axis,
        # scaling it to our maximum rotational speed. When standing still this means
        # that full right on the right hand stick corresponds to maximum speed
        # clockwise rotation.
        rotate = joystick.axes[2].corrected_value() * max_rot

        # Given the translation vector and rotation, use the chassis object to calculate
        # the speeds required in revolutions per second for each wheel. As we set the
        # maximum wheel speeds to 1.0, all speeds will range from -1.0 to 1.0
        wheel_speeds = chassis.get_wheel_speeds(
            translation=translate,
            rotation=rotate,
            origin=Point2(0, 0))

        # Print speeds and any scaling applied to the console (the chassis object will
        # scale output speeds to ensure that no wheel is driven faster than possible,
        # it returns the scaling applied - most of the time this will be 1.0 but if e.g.
        # we're attempting to move as fast as possible and rotate we'll probably be
        # pulling the overal speeds back to allow for the requested motion)
        speeds = wheel_speeds.speeds
        scaling = wheel_speeds.scaling
        print (scaling, speeds)

        # Send desired motor speed values over the I2C bus to the Arduino, which will
        # then send the appropriate messages to the Syren10 controllers over its serial
        # line as well as lighting up a neopixel ring to provide additional feedback
        # and bling.
        arduino.set_motor_power(speeds[0], speeds[1], speeds[2])
