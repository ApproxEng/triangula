from math import degrees

from euclid import Vector2
from triangula.chassis import rotate_vector, Motion, DeadReckoning
from triangula.dynamics import RateLimit, MotionLimit
from triangula.input import SixAxis
from triangula.task import Task
from triangula.util import IntervalCheck


class ManualMotionTask(Task):
    """
    Class enabling manual control of the robot from the joystick. Uses dead-reckoning for bearing lock, we don't
    use the IMU at all in this version of the class, it was proving problematic in real-world conditions and the
    dead-reckoning logic is surprisingly accurate and stable.
    """

    ACCEL_TIME = 1.0
    'Time to reach full speed from a standing start'

    def __init__(self):
        super(ManualMotionTask, self).__init__(task_name='Manual motion', requires_compass=False)
        self.bearing_zero = None
        self.max_trn = 0
        self.max_rot = 0
        self.dead_reckoning = None
        self.pose_display_interval = IntervalCheck(interval=0.2)
        self.pose_update_interval = IntervalCheck(interval=0.1)
        self.rate_limit = None
        ':type : triangula.dynamics.RateLimit'
        self.motion_limit = None
        ':type : triangula.dynamics.MotionLimit'
        self.limit_mode = 0

    def init_task(self, context):
        # Maximum translation speed in mm/s
        self.max_trn = context.chassis.get_max_translation_speed()
        # Maximum rotation speed in radians/2
        self.max_rot = context.chassis.get_max_rotation_speed()
        self._set_relative_motion(context)
        self.dead_reckoning = DeadReckoning(chassis=context.chassis, counts_per_revolution=3310)
        self.motion_limit = MotionLimit(
                linear_acceleration_limit=context.chassis.get_max_translation_speed / ManualMotionTask.ACCEL_TIME,
                angular_acceleration_limit=context.chassis.get_max_rotation_speed / ManualMotionTask.ACCEL_TIME)
        self.rate_limit = RateLimit(limit_function=RateLimit.fixed_rate_limit_function(1 / ManualMotionTask.ACCEL_TIME))
        self.limit_mode = 0

    def _set_absolute_motion(self, context):
        """
        Lock motion to be compass relative, zero point (forwards) is the current bearing
        """
        context.lcd.set_backlight(3, 10, 0)
        self.bearing_zero = self.dead_reckoning.pose.orientation

    def _set_relative_motion(self, context):
        """
        Set motion to be relative to the robot's reference frame
        """
        context.lcd.set_backlight(10, 3, 9)
        self.bearing_zero = None

    def poll_task(self, context, tick):

        # Check joystick buttons to see if we need to change mode or reset anything
        if context.button_pressed(SixAxis.BUTTON_TRIANGLE):
            self._set_relative_motion(context)
        elif context.button_pressed(SixAxis.BUTTON_SQUARE):
            self._set_absolute_motion(context)
        elif context.button_pressed(SixAxis.BUTTON_CIRCLE):
            self.dead_reckoning.reset()
        elif context.button_pressed(SixAxis.BUTTON_CROSS):
            self.limit_mode = (self.limit_mode + 1) % 3

        # Check to see whether the minimum interval between dead reckoning updates has passed
        if self.pose_update_interval.should_run():
            self.dead_reckoning.update_from_counts(context.arduino.get_encoder_values())

        # Update the display if appropriate
        if self.pose_display_interval.should_run():
            pose = self.dead_reckoning.pose
            mode_string = 'ABS'
            if self.bearing_zero is None:
                mode_string = 'REL'
            if self.limit_mode == 1:
                mode_string += '*'
            elif self.limit_mode == 2:
                mode_string += '+'
            context.lcd.set_text(row1='x:{:7.0f}, b:{:3.0f}'.format(pose.position.x, degrees(pose.orientation)),
                                 row2='y:{:7.0f}, {}'.format(pose.position.y, mode_string))

        # Get a vector from the left hand analogue stick and scale it up to our
        # maximum translation speed, this will mean we go as fast directly forward
        # as possible when the stick is pushed fully forwards

        translate = Vector2(
                context.joystick.axes[0].corrected_value(),
                context.joystick.axes[1].corrected_value()) * self.max_trn
        ':type : euclid.Vector2'

        # If we're in absolute mode, rotate the translation vector appropriately
        if self.bearing_zero is not None:
            translate = rotate_vector(translate,
                                      self.bearing_zero - self.dead_reckoning.pose.orientation)

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
        motion = Motion(translation=translate, rotation=rotate)
        if self.limit_mode == 2:
            motion = self.motion_limit.limit_and_return(motion)
        wheel_speeds = context.chassis.get_wheel_speeds(motion=motion)
        speeds = wheel_speeds.speeds

        # Send desired motor speed values over the I2C bus to the Arduino, which will
        # then send the appropriate messages to the Syren10 controllers over its serial
        # line as well as lighting up a neopixel ring to provide additional feedback
        # and bling.
        power = [speeds[i] / context.chassis.wheels[i].max_speed for i in range(0, 3)]
        if self.limit_mode == 1:
            power = self.rate_limit.limit_and_return(power)
        context.arduino.set_motor_power(power[0], power[1], power[2])
