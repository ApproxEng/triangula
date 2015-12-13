from time import sleep

from triangula.input import SixAxis
from triangula.task import Task
from triangula.util import get_ip_address


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
        sleep(0.1)
