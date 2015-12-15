from math import degrees

from euclid import Vector2
from triangula.chassis import rotate_vector, Motion, DeadReckoning
from triangula.input import SixAxis
from triangula.task import Task


class ManualMotionTask(Task):
    """
    Class enabling manual control of the robot from the joystick. Uses the IMU for bearing lock without any
    form of dead-reckoning.
    """

    def __init__(self):
        super(ManualMotionTask, self).__init__(task_name='Manual motion', requires_compass=True)
        self.bearing_zero = None
        self.last_bearing = 0
        self.max_trn = 0
        self.max_rot = 0
        self.dead_reckoning = None

    def _set_absolute_motion(self, context):
        """
        Lock motion to be compass relative, zero point (forwards) is the current bearing
        """
        context.lcd.set_backlight(0, 10, 0)
        context.lcd.set_text(row1='Manual Control', row2='Absolute Motion')
        self.bearing_zero = self.last_bearing

    def _set_relative_motion(self, context):
        """
        Set motion to be relative to the robot's reference frame
        """
        context.lcd.set_backlight(10, 0, 0)
        context.lcd.set_text(row1='Manual Control', row2='Relative Motion')
        self.bearing_zero = None

    def init_task(self, context):
        # Maximum translation speed in mm/s
        self.max_trn = context.chassis.get_max_translation_speed()
        # Maximum rotation speed in radians/2
        self.max_rot = context.chassis.get_max_rotation_speed()
        self._set_relative_motion(context)
        self.dead_reckoning = DeadReckoning(chassis=context.chassis)

    def poll_task(self, context, tick):
        if context.bearing is not None:
            self.last_bearing = context.bearing

        if context.button_pressed(SixAxis.BUTTON_TRIANGLE):
            self._set_relative_motion(context)
        elif context.button_pressed(SixAxis.BUTTON_SQUARE):
            self._set_absolute_motion(context)
        elif context.button_pressed(SixAxis.BUTTON_CIRCLE):
            self.dead_reckoning.reset()
        elif context.button_pressed(SixAxis.BUTTON_CROSS):
            pose = self.dead_reckoning.pose
            context.lcd.set_text(row1='x: {:5.0f} y: {:5.0f}'.format(pose.position.x, pose.position.y),
                                 row2='r: {0:03d}'.format(degrees(pose.orientation)))

        # Get the encoder counts and update the dead reckoning logic
        self.dead_reckoning.update_from_counts(context.arduino.get_encoder_values())

        # Get a vector from the left hand analogue stick and scale it up to our
        # maximum translation speed, this will mean we go as fast directly forward
        # as possible when the stick is pushed fully forwards
        translate = Vector2(
            context.joystick.axes[0].corrected_value(),
            context.joystick.axes[1].corrected_value()) * self.max_trn

        # If we're in absolute mode, rotate the translation vector appropriately
        if self.bearing_zero is not None:
            translate = rotate_vector(translate,
                                      self.last_bearing - self.bearing_zero)

        # Get the rotation in radians per second from the right hand stick's X axis,
        # scaling it to our maximum rotational speed. When standing still this means
        # that full right on the right hand stick corresponds to maximum speed
        # clockwise rotation.
        rotate = context.joystick.axes[2].corrected_value() * self.max_rot

        # Given the translation vector and rotation, use the chassis object to calculate
        # the speeds required in revolutions per second for each wheel. We'll scale these by the
        # wheel maximum speeds to get a range of -1.0 to 1.0
        # This is a :class:`triangula.chassis.WheelSpeeds` containing the speeds and any
        # scaling applied to bring the requested velocity within the range the chassis can
        # actually perform.
        wheel_speeds = context.chassis.get_wheel_speeds(motion=Motion(translation=translate, rotation=rotate))
        speeds = wheel_speeds.speeds

        # Send desired motor speed values over the I2C bus to the Arduino, which will
        # then send the appropriate messages to the Syren10 controllers over its serial
        # line as well as lighting up a neopixel ring to provide additional feedback
        # and bling.
        power = [speeds[i] / context.chassis.wheels[i].max_speed for i in range(0, 3)]
        context.arduino.set_motor_power(power[0], power[1], power[2])
