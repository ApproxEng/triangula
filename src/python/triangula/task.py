import math
import time
from abc import ABCMeta, abstractmethod

import triangula.chassis
import triangula.imu
from euclid import Vector2
from triangula.chassis import Motion
from triangula.input import SixAxis
from triangula.util import get_ip_address


class TaskManager:
    """
    Manages the task loop
    """

    def __init__(self, arduino, lcd, chassis, joystick):
        self.arduino = arduino
        self.lcd = lcd
        self.chassis = chassis
        self.joystick = joystick

    def _build_context(self, include_bearing):
        bearing = None
        imu_data = None
        if include_bearing:
            imu_data = triangula.imu.read()
            bearing = imu_data[2]
        return TaskContext(arduino=self.arduino,
                           lcd=self.lcd,
                           bearing=bearing,
                           imu_data=imu_data,
                           chassis=self.chassis,
                           joystick=self.joystick,
                           buttons_pressed=self.joystick.get_and_clear_button_press_history())

    def run(self, initial_task):
        """
        Start the task loop. Handles task switching and initialisation as well as any exceptions thrown within tasks.

        :param initial_task:
            An instance of :class:`triangula.task.Task` to use as the first task. Typically this is a menu or startup
            task of some kind.
        """
        active_task = initial_task
        task_initialised = False
        tick = 0

        while 1:
            try:
                context = self._build_context(active_task.requires_compass)
                if context.button_pressed(SixAxis.BUTTON_SELECT):
                    active_task = ClearStateTask(MenuTask())
                    task_initialised = False
                    tick = 0
                if task_initialised:
                    new_task = active_task.poll_task(context=context, tick=tick)
                    if new_task is None:
                        tick += 1
                    else:
                        active_task = new_task
                        task_initialised = False
                        tick = 0
                else:
                    active_task.init_task(context=context)
                    task_initialised = True
            except Exception as e:
                active_task = ClearStateTask(ErrorTask(e))
                task_initialised = False


class TaskContext:
    """
    Contains the resources a task might need to perform its function

    :ivar timestamp:
        The time, in seconds since the epoch, that this context was created. In effect this is also the task creation
        time as they're created at the same time.

    """

    def __init__(self, arduino, lcd, bearing, imu_data, chassis, joystick, buttons_pressed):
        """
        Create a new task context

        :param arduino:
            Instance of :class:`triangula.arduino.Arduino` that can be used to manipulate the motors and lights, and
            which can poll the encoders attached to the motors.
        :param lcd:
            Instance of :class:`triangula.lcd.LCD` that can be used to display messages.
        :param bearing:
            If the task has indicated that a bearing is required, this is float value from the compass on the IMU.
        :param imu_data:
            If the task has indicated that a bearing is required, contains the entire IMU data block.
        :param chassis:
            An instance of :class:`triangula.chassis.HoloChassis` defining the motion dynamics for the robot.
        :param joystick:
            An instance of :class:`triangula.input.SixAxis` which can be used to get the joystick axes.
        :param buttons_pressed:
            A bitfield where bits are set to 1 if the corresponding SixAxis button was pressed since the start of the
            previous task poll. Use this in preference to handler registration as it simplifies threading and cleanup
        """
        self.arduino = arduino
        self.lcd = lcd
        self.bearing = bearing
        self.chassis = chassis
        self.joystick = joystick
        self.buttons_pressed = buttons_pressed
        self.timestamp = time.time()
        self.imu_data = imu_data

    def button_pressed(self, button_code):
        """
        Helper method, equivalent to 'self.buttons_pressed & 1 << button_code

        :param button_code:
            A button index from :class:`triangula.input.SixAxis` i.e. SixAxis.BUTTON_SQUARE
        :return:
            0 if the button wasn't pressed at the time the context was created, non-zero otherwise
        """
        return self.buttons_pressed & 1 << button_code


class Task:
    """
    Base class for tasks. Tasks are single-minded activities which are run, one at a time, on Triangula's
    processor. The service script is responsible for polling the active task, providing it with an appropriate
    set of objects and properties such that it can interact with its environment.
    """

    __metaclass__ = ABCMeta

    def __init__(self, task_name='New Task', requires_compass=False):
        """
        Create a new task with the specified name

        :param task_name:
            Name for this task, used in debug mostly. Defaults to 'New Task'
        :param requires_compass:
            Set to True to require that the task is provided with the current compass bearing when polled. This defaults
            to False because I2C transactions are expensive and we don't want to make more of them than we have to.
        """
        self.task_name = task_name
        self.requires_compass = requires_compass

    def __str__(self):
        return 'Task[ task_name={} ]'.format(self.task_name)

    @abstractmethod
    def init_task(self, context):
        """
        Called exactly once, the first time a new task is activated. Use this to set up any properties which weren't
        available during construction.

        :param context:
            An instance of :class:`triangula.task.TaskContext` containing objects and properties which allow the task
            to comprehend and act on its environment.
        """
        return None

    @abstractmethod
    def poll_task(self, context, tick):
        """
        Polled to perform the task's action, you shouldn't hang around too long in this method but there's no explicit
        requirement for timely processing.

        :param context:
            An instance of :class:`triangula.task.TaskContext` containing objects and properties which allow the task
            to comprehend and act on its environment.
        :param int tick:
            A counter, incremented each time poll is called.
        :return:
            Either None, to continue this task, or a subclass of :class:`triangula.task.Task` to switch to that task.
        """
        return None


class ClearStateTask(Task):
    """
    Task which clears the state, turns the lights off and stops the motors, then immediately passes control to another
    task.
    """

    def __init__(self, following_task):
        """
        Create a new clear state task, this will effectively reset the robot's peripherals and pass control to the
        next task. Use this when switching to ensure we're not leaving the wheels running etc.

        :param following_task:
            Another :class:`triangula.task.Task` which is immediately returned from the first poll operation.
        :return:
        """
        super(ClearStateTask, self).__init__(task_name='Clear state task', requires_compass=False)
        self.following_task = following_task

    def init_task(self, context):
        context.arduino.set_motor_power(0, 0, 0)
        context.lcd.set_text(row1='', row2='')
        context.lcd.set_backlight(0, 0, 0)
        context.arduino.set_lights(0, 0, 0)

    def poll_task(self, context, tick):
        return self.following_task


class NetworkInfoTask(Task):
    """
    Simple task that gets the network address of the wired and wireless interfaces and displays them on the LCD.
    """

    def __init__(self):
        super(NetworkInfoTask, self).__init__(task_name='Network info', requires_compass=False)
        self.interfaces = ['eth0', 'wlan0']
        self.selected_interface = 0

    def init_task(self, context):
        context.lcd.set_backlight(10, 10, 10)

    def _increment_interface(self, delta):
        self.selected_interface += delta
        self.selected_interface %= len(self.interfaces)

    def poll_task(self, context, tick):
        if context.button_pressed(SixAxis.BUTTON_D_LEFT):
            self._increment_interface(-1)
        elif context.button_pressed(SixAxis.BUTTON_D_RIGHT):
            self._increment_interface(1)
        context.lcd.set_text(
            row1='{}: {} of {}'.format(self.interfaces[self.selected_interface],
                                       self.selected_interface + 1,
                                       len(self.interfaces)),
            row2=get_ip_address(ifname=self.interfaces[self.selected_interface]))
        time.sleep(0.1)


class ErrorTask(Task):
    """
    Task used to display an error message
    """

    def __init__(self, exception):
        """
        Create a new error display task

        :param exception:
            An exception which caused this display to be shown
        """
        super(ErrorTask, self).__init__(task_name='Error', requires_compass=False)
        self.exception = exception
        print exception

    def init_task(self, context):
        context.lcd.set_backlight(red=10, green=0, blue=0)

    def poll_task(self, context, tick):
        context.lcd.set_text(row1='ERROR!', row2=((' ' * 16) + str(self.exception) + (' ' * 16))[
                                                 tick % (len(str(self.exception)) + 16):])
        time.sleep(0.2)


class MenuTask(Task):
    """
    Top level menu class
    """

    def __init__(self):
        super(MenuTask, self).__init__(task_name='Menu', requires_compass=False)
        self.tasks = [ManualMotionTask(), NetworkInfoTask(), CompassTestTask()]
        self.selected_task_index = 0

    def init_task(self, context):
        time.sleep(0.05)
        context.lcd.set_backlight(10, 10, 10)
        time.sleep(0.05)
        context.arduino.set_lights(170, 255, 60)

    def _increment_index(self, delta):
        self.selected_task_index += delta
        self.selected_task_index %= len(self.tasks)

    def poll_task(self, context, tick):
        if context.button_pressed(SixAxis.BUTTON_D_LEFT):
            self._increment_index(-1)
        elif context.button_pressed(SixAxis.BUTTON_D_RIGHT):
            self._increment_index(1)
        elif context.button_pressed(SixAxis.BUTTON_CROSS):
            return ClearStateTask(following_task=self.tasks[self.selected_task_index])
        context.lcd.set_text(row1='Task {} of {}'.format(self.selected_task_index + 1, len(self.tasks)),
                             row2=self.tasks[self.selected_task_index].task_name)
        time.sleep(0.1)


class CompassTestTask(Task):
    """
    Display the current compass bearing
    """

    def __init__(self):
        super(CompassTestTask, self).__init__(task_name='Compass test', requires_compass=True)

    def init_task(self, context):
        pass

    def poll_task(self, context, tick):
        context.lcd.set_text(row1='Compass test', row2=str(math.degrees(context.bearing)))
        time.sleep(0.1)


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

    def _set_absolute_motion(self, context):
        """
        Lock motion to be compass relative, zero point (forwards) is the current bearing
        """
        time.sleep(0.05)
        context.lcd.set_backlight(0, 10, 0)
        time.sleep(0.05)
        context.lcd.set_text(row1='Manual Control', row2='Absolute Motion')
        time.sleep(0.05)
        self.bearing_zero = self.last_bearing

    def _set_relative_motion(self, context):
        """
        Set motion to be relative to the robot's reference frame
        """
        time.sleep(0.05)
        context.lcd.set_backlight(10, 0, 0)
        time.sleep(0.05)
        context.lcd.set_text(row1='Manual Control', row2='Relative Motion')
        time.sleep(0.05)
        self.bearing_zero = None

    def init_task(self, context):
        # Maximum translation speed in mm/s
        self.max_trn = context.chassis.get_max_translation_speed()
        # Maximum rotation speed in radians/2
        self.max_rot = context.chassis.get_max_rotation_speed()
        self._set_relative_motion(context)

    def poll_task(self, context, tick):
        if context.bearing is not None:
            self.last_bearing = context.bearing

        if context.button_pressed(SixAxis.BUTTON_TRIANGLE):
            self._set_relative_motion(context)
        elif context.button_pressed(SixAxis.BUTTON_SQUARE):
            self._set_absolute_motion(context)

        # Get a vector from the left hand analogue stick and scale it up to our
        # maximum translation speed, this will mean we go as fast directly forward
        # as possible when the stick is pushed fully forwards
        translate = Vector2(
            context.joystick.axes[0].corrected_value(),
            context.joystick.axes[1].corrected_value()) * self.max_trn

        # If we're in absolute mode, rotate the translation vector appropriately
        if self.bearing_zero is not None:
            translate = triangula.chassis.rotate_vector(translate,
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
