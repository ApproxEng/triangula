from time import sleep

from triangula.input import SixAxis
from triangula.task import ClearStateTask, Task
from triangula.tasks.compass_test import CompassTestTask
from triangula.tasks.manual_control import ManualMotionTask
from triangula.tasks.network_info import NetworkInfoTask
from triangula.tasks.patrol import SimplePatrolExample


class MenuTask(Task):
    """
    Top level menu class
    """

    def __init__(self):
        super(MenuTask, self).__init__(task_name='Menu', requires_compass=False)
        self.tasks = [ManualMotionTask(), NetworkInfoTask(), CompassTestTask(), SimplePatrolExample()]
        self.selected_task_index = 0

    def init_task(self, context):
        context.lcd.set_backlight(10, 10, 10)
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
        sleep(0.1)
