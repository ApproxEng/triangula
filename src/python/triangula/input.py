__author__ = 'tom'

from asyncore import file_dispatcher, loop

from evdev import InputDevice, list_devices
from threading import Thread


class SixAxis():
    """
    Class to handle the PS3 SixAxis controller

    This class will process events from the pygame event queue and calculate positions for each of the analogue axes on
    the SixAxis controller (excluding the motion sensor which appears not to work for some reason). It will also extract
    button press events and call any handler functions bound to those buttons.

    Events are only processed when the handle_events method is called, this must be called reasonably frequently as the
    pygame event queue will discard events once full and the joystick hardware is sufficiently twitchy that it's
    generating events pretty much constantly.

    Consuming code can get the current position of any of the sticks from this class through the `axes` instance
    property. This contains a list of :class:`triangula.input.SixAxis.Axis` objects, one for each distinct axis on the
    controller. The list of axes is, in order: left x, left y, right x, right y.
    """

    BUTTON_SELECT = 0  #: The Select button
    BUTTON_LEFT_STICK = 1  #: Left stick click button
    BUTTON_RIGHT_STICK = 2  #: Right stick click button
    BUTTON_START = 3  #: Start button
    BUTTON_D_UP = 4  #: D-pad up
    BUTTON_D_RIGHT = 5  #: D-pad right
    BUTTON_D_DOWN = 6  #: D-pad down
    BUTTON_D_LEFT = 7  #: D-pad left
    BUTTON_L2 = 8  #: L2 lower shoulder trigger
    BUTTON_R2 = 9  #: R2 lower shoulder trigger
    BUTTON_L1 = 10  #: L1 upper shoulder trigger
    BUTTON_R1 = 11  #: R1 upper shoulder trigger
    BUTTON_TRIANGLE = 12  #: Triangle
    BUTTON_CIRCLE = 13  #: Circle
    BUTTON_CROSS = 14  #: Cross
    BUTTON_SQUARE = 15  #: Square
    BUTTON_PS = 16  #: PS button

    def __init__(self, dead_zone=0.2, hot_zone=0.05, init_pygame=True):
        """
        Discover and initialise a PS3 SixAxis controller connected to this computer

        :param float dead_zone:
            Creates a dead zone centred on the centre position of the axis (which may or may not be zero depending on
            calibration). The axis values range from 0 to 1.0, but will be locked to 0.0 when the measured value less
            centre offset is lower in magnitude than this supplied value. Defaults to 0.2, which makes the PS3 analogue
            sticks easy to centre but still responsive to motion. The deadzone is applies to each axis independently, so
            e.g. moving the stick far right won't affect the deadzone for that sticks Y axis.
        :param float hot_zone:
            Creates a zone of maximum value, any readings from the sensor which are within this value of the max or min
            values will be mapped to 1.0 and -1.0 respectively. This can be useful because, while the PS3 controllers
            sticks have independent axes, they are constrained to move within a circle, so it's impossible to have e.g.
            1.0,1.0 for both x and y axes. Setting this value to non-zero in effect partially squares the circle,
            allowing for controls which require full range control. Setting this value to 1/sqrt(2) will create a square
            zone of variability within the circular range of motion of the controller, with any stick motions outside
            this square mapping to the maximum value for the respective axis. The value is actually scaled by the max
            and min magnitude for upper and lower ranges respectively, so e.g. setting 0.5 will create a hot-zone at
            above half the maximum value and below half the minimum value, and not at +0.5 and -0.5 (unless max and
            min are 1.0 and -1.0 respectively). As with the dead zone, these are applied separately to each axis, so in
            the case where the hot zone is set to 1/sqrt(2), a circular motion of the stick will map to x and y values
            which trace the outline of a square of unit size, allowing for all values to be emitted from the stick.
        :param boolean init_pygame:
            Defaults to True; if set then pygame will be initialised with the appropriate properties to run headless, if
            false then no pygame initialisation will be performed. If you pass False to this method you must have
            already initialised pygame (there's no requirement to initialise the joystick subsystem, this is always
            performed in this method, it's safe to run multiple times anyway)
        :return: an initialised link to an attached PS3 SixAxis controller
        """

        self.stop_function = None
        self.axes = [SixAxis.Axis('left_x', dead_zone=dead_zone, hot_zone=hot_zone),
                     SixAxis.Axis('left_y', dead_zone=dead_zone, hot_zone=hot_zone, invert=True),
                     SixAxis.Axis('right_x', dead_zone=dead_zone, hot_zone=hot_zone),
                     SixAxis.Axis('right_y', dead_zone=dead_zone, hot_zone=hot_zone, invert=True)]
        self.button_handlers = []
        self.connect()

    def connect(self):
        if self.stop_function:
            return
        for device in [InputDevice(fn) for fn in list_devices()]:
            if device.name == 'PLAYSTATION(R)3 Controller':
                self.sixaxis = device
                parent = self

                class InputDeviceDispatcher(file_dispatcher):
                    def __init__(self):
                        self.device = device
                        file_dispatcher.__init__(self, device)

                    def recv(self, ign=None):
                        return self.device.read()

                    def handle_read(self):
                        for event in self.recv():
                            parent.handle_event(event)

                InputDeviceDispatcher()

                class AsyncLoop(Thread):
                    def __init__(self):
                        Thread.__init__(self, name='InputDispatchThread')

                    def run(self):
                        loop()

                self.stop_function = AsyncLoop()
                self.stop_function.start()

    def __str__(self):
        return 'x1={}, y1={}, x2={}, y2={}'.format(
            self.axes[0].corrected_value(), self.axes[1].corrected_value(),
            self.axes[2].corrected_value(), self.axes[3].corrected_value())

    def set_axis_centres(self, *args):
        """
        Sets the centre points for each axis to the current value for that axis. This centre value is used when
        computing the value for the axis and is subtracted before applying any scaling.
        """
        for axis in self.axes:
            axis.centre = axis.value

    def reset_axis_calibration(self, *args):
        """
        Resets any previously defined axis calibration to 0.0 for all axes
        """
        for axis in self.axes:
            axis._reset()

    def register_button_handler(self, handler, buttons):
        """
        Register a handler function which will be called when a button is pressed

        :param handler: a function which will be called when any of the specified buttons are pressed. The function is
            called with the integer code for the button as the sole argument.
        :param [int] buttons: a list or one or more buttons which should trigger the handler when pressed. Buttons are
            specified as ints, for convenience the PS3 button assignments are mapped to names in SixAxis, i.e.
            SixAxis.BUTTON_CIRCLE. This includes the buttons in each of the analogue sticks. A bare int value is also
            accepted here and will be treated as if a single element list was supplied.
        :return: a no-arg function which can be used to remove this registration
        """
        mask = 0
        if isinstance(buttons, list):
            for button in buttons:
                mask += 1 << button
        else:
            mask += 1 << buttons
        h = {'handler': handler,
             'mask': mask}
        self.button_handlers.append(h)

        def remove():
            self.button_handlers.remove(h)

        return remove

    def handle_event(self, event):
        print event
        if event.type == 3:
            value = (event.value - 128.0) / 128.0
            if event.code == 0:
                # Left stick, X axis
                self.axes[0]._set(value)
            elif event.code == 1:
                # Left stick, Y axis
                self.axes[1]._set(value)
            elif event.code == 2:
                # Right stick, X axis
                self.axes[2]._set(value)
            elif event.code == 5:
                # Right stick, Y axis (yes, 5...)
                self.axes[3]._set(value)
        """
        for event in pg_event.get():
            if event.type == JOYAXISMOTION and event.joy == self.active_index:
                if event.axis < len(self.axes):
                    self.axes[event.axis]._set(event.value)
            elif event.type == JOYBUTTONDOWN and event.joy == self.active_index:
                for handler in self.button_handlers:
                    if handler['mask'] & (1 << event.button) != 0:
                        handler['handler'](event.button)
        """

    class Axis():
        """A single analogue axis on the SixAxis controller"""

        def __init__(self, name, invert=False, dead_zone=0.0, hot_zone=0.0):
            self.name = name
            self.centre = 0.0
            self.max = 0.9
            self.min = -0.9
            self.value = 0.0
            self.invert = invert
            self.dead_zone = dead_zone
            self.hot_zone = hot_zone

        def corrected_value(self):
            """
            Get a centre-compensated, scaled, value for the axis, taking any dead-zone into account. The value will
            scale from 0.0 at the edge of the dead-zone to 1.0 (positive) or -1.0 (negative) at the extreme position of
            the controller or the edge of the hot zone, if defined as other than 1.0. The axis will auto-calibrate for
            maximum value, initially it will behave as if the highest possible value from the hardware is 0.9 in each
            direction, and will expand this as higher values are observed. This is scaled by this function and should
            always return 1.0 or -1.0 at the extreme ends of the axis.

            :return: a float value, negative to the left or down and ranging from -1.0 to 1.0
            """

            centred = self.value - self.centre

            if abs(centred) <= self.dead_zone:
                return 0.0
            elif centred > 0 and self.value > self.max - (self.hot_zone * self.max):
                if not self.invert:
                    return 1.0
                else:
                    return -1.0
            elif centred < 0 and self.value < self.min - (self.hot_zone * self.min):
                if not self.invert:
                    return -1.0
                else:
                    return 1.0

            if centred > 0:
                top_range = self.max - (self.hot_zone * self.max + self.dead_zone)
                result = centred / top_range
            else:
                bottom_range = self.dead_zone - (self.min - self.hot_zone * self.min)
                result = centred / bottom_range

            if self.invert:
                result = -result

            return result

        def _reset(self):
            """
            Reset calibration (max, min and centre values) for this axis specifically. Not generally needed, you can just
            call the reset method on the SixAxis instance.

            :internal:
            """
            self.centre = 0.0
            self.max = 1.0
            self.min = -1.0

        def _set(self, new_value):
            """
            Set a new value, called from within the SixAxis class when parsing the event queue.

            :param new_value: the raw value from the joystick hardware
            :internal:
            """
            self.value = new_value
            if new_value > self.max:
                self.max = new_value
            elif new_value < self.min:
                self.min = new_value


if __name__ == '__main__':
    from input import SixAxis
    import time

    controller = SixAxis(dead_zone=0.2, hot_zone=0.1, init_pygame=True)


    def handler(button):
        print 'Button! {}'.format(button)


    controller.register_button_handler(handler, SixAxis.BUTTON_CIRCLE)
    controller.register_button_handler(controller.reset_axis_calibration, SixAxis.BUTTON_START)
    controller.register_button_handler(controller.set_axis_centres, SixAxis.BUTTON_SELECT)

    current_milli_time = lambda: int(round(time.time() * 1000))
    last_time = current_milli_time()
    while 1:
        controller.handle_events()
        now = current_milli_time()
        if now > (last_time + 100):
            last_time = now
            print controller
