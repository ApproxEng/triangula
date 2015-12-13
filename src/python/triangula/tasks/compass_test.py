from math import degrees
from time import sleep

from triangula.task import Task


class CompassTestTask(Task):
    """
    Display the current compass bearing
    """

    def __init__(self):
        super(CompassTestTask, self).__init__(task_name='Compass test', requires_compass=True)

    def init_task(self, context):
        pass

    def poll_task(self, context, tick):
        context.lcd.set_text(row1='Compass test', row2=str(degrees(context.bearing)))
        sleep(0.1)
