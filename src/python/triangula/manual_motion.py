from math import degrees

from approxeng.chassis import HoloChassis, DeadReckoning, rotate_vector, Motion
from approxeng.chassis.dynamics import MotionLimit, RateLimit
from approxeng.input import Controller
from approxeng.task import Task
from euclid import Vector2

from triangula.hardware import Arduino, P017LCD
from triangula.util import IntervalCheck


class ManualMotionTask(Task):

    # noinspection PyTypeChecker
    def __init__(self, accel_time=1.0):
        super().__init__(name='manual_motion', resources=['arduino', 'display', 'joystick', 'chassis'])
        self.accel_time = accel_time
        self.bearing_zero = None
        self.max_trn = 0
        self.max_rot = 0
        self.dead_reckoning = None
        ':type : '
        self.pose_display_interval = IntervalCheck(interval=0.2)
        self.pose_update_interval = IntervalCheck(interval=0.1)
        self.rate_limit = None
        ':type : approxeng.chassis.dynamics.RateLimit'
        self.motion_limit = None
        ':type : approxeng.chassis.dynamics.MotionLimit'
        self.limit_mode = 0

    def startup(self):
        # Build task world, this is safe to do as resources are set up before startup(..) is called
        world = Task.World(resources=self.ordered_resources,
                           task_count=self.task_count,
                           global_count=Task.global_count)
        # Cache maximum translation and rotation speeds from chassis calculations
        self.max_trn = world.chassis.get_max_translation_speed()
        self.max_rot = world.chassis.get_max_rotation_speed()
        # Set relative motion
        world.display.led0 = 'red'
        self.bearing_zero = None
        # Initialise dead reckoning
        self.dead_reckoning = DeadReckoning(chassis=world.chassis, counts_per_revolution=3310)
        # Set up motion limits, simulate slower response to avoid damaging
        # tyres and other mechanical bits with overly vigorous acceleration
        self.motion_limit = MotionLimit(
            linear_acceleration_limit=self.max_trn / self.accel_time,
            angular_acceleration_limit=self.max_rot / self.accel_time)
        self.rate_limit = RateLimit(limit_function=RateLimit.fixed_rate_limit_function(1 / self.accel_time))
        self.limit_mode = 0

    def shutdown(self):
        pass

    def tick(self, world):
        self.manual_motion(arduino=world.arduino, display=world.display,
                           joystick=world.joystick, chassis=world.chassis)

    def manual_motion(self, arduino: Arduino, display: P017LCD, joystick: Controller, chassis: HoloChassis):

        # Check for mode changes
        if 'triangle' in joystick.presses:
            # Set relative motion
            display.led0 = 'red'
            self.bearing_zero = None
        elif 'square' in joystick.presses:
            # Set absolute motion
            display.led0 = 'lime'
            self.bearing_zero = self.dead_reckoning.pose.orientation
        elif 'circle' in joystick.presses:
            # Reset dead reckoning orientation
            self.dead_reckoning.reset()
        elif 'cross' in joystick.presses:
            # Cycle through limit modes
            self.limit_mode = (self.limit_mode + 1) % 3

        # Check to see whether the minimum interval between dead reckoning updates has passed
        if self.pose_update_interval.should_run():
            self.dead_reckoning.update_from_counts(arduino.encoder_values)

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
            display.text = ['x:{:7.0f}, b:{:3.0f}'.format(pose.position.x, degrees(pose.orientation)),
                            'y:{:7.0f}, {}'.format(pose.position.y, mode_string)]

        # Get a vector from the left hand analogue stick and scale it up to our
        # maximum translation speed, this will mean we go as fast directly forward
        # as possible when the stick is pushed fully forwards

        translate = Vector2(
            joystick.lx,
            joystick.ly) * self.max_trn
        ':type : euclid.Vector2'

        # If we're in absolute mode, rotate the translation vector appropriately
        if self.bearing_zero is not None:
            translate = rotate_vector(translate,
                                      self.bearing_zero - self.dead_reckoning.pose.orientation)

        # Get the rotation in radians per second from the right hand stick's X axis,
        # scaling it to our maximum rotational speed. When standing still this means
        # that full right on the right hand stick corresponds to maximum speed
        # clockwise rotation.
        rotate = joystick.rx * self.max_rot

        # Given the translation vector and rotation, use the chassis object to calculate
        # the speeds required in revolutions per second for each wheel. We'll scale these by the
        # wheel maximum speeds to get a range of -1.0 to 1.0
        # This is a :class:`triangula.chassis.WheelSpeeds` containing the speeds and any
        # scaling applied to bring the requested velocity within the range the chassis can
        # actually perform.
        motion = Motion(translation=translate, rotation=rotate)
        if self.limit_mode == 2:
            motion = self.motion_limit.limit_and_return(motion)
        wheel_speeds = chassis.get_wheel_speeds(motion=motion)
        speeds = wheel_speeds.speeds

        # Send desired motor speed values over the I2C bus to the Arduino, which will
        # then send the appropriate messages to the Syren10 controllers over its serial
        # line as well as lighting up a neopixel ring to provide additional feedback
        # and bling.
        power = [speeds[i] / chassis.wheels[i].maximum_rotation_per_second for i in range(0, 3)]
        if self.limit_mode == 1:
            power = self.rate_limit.limit_and_return(power)
        arduino.set_motor_power(power[0], power[1], power[2])
