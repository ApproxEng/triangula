import time

import triangula.chassis
import triangula.imu
from abc import ABCMeta, abstractmethod
from triangula.input import SixAxis


class TaskManager:
    """
    Manages the task loop
    """

    def __init__(self, arduino, lcd, chassis, joystick):
        self.arduino = arduino
        self.lcd = lcd
        self.chassis = chassis
        self.joystick = joystick
        self.home_task = None

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

        if self.home_task is None:
            self.home_task = initial_task

        while 1:
            try:
                context = self._build_context(active_task.requires_compass)
                if context.button_pressed(SixAxis.BUTTON_SELECT):
                    active_task = ClearStateTask(self.home_task)
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
