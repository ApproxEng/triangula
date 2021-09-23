from time import sleep

from approxeng.chassis.util import get_regular_triangular_chassis
from approxeng.input.selectbinder import ControllerResource
from approxeng.task import register_task, register_resource, TaskStop, run, task
from approxeng.task.menu import register_menu_tasks_from_yaml

from triangula.hardware import Arduino, P017LCD, MPU9150
from triangula.manual_motion import ManualMotionTask
from triangula.menu import TriangulaMenuClass

# Register resources to be used by tasks
register_resource('arduino', Arduino())
register_resource('mpu', MPU9150())
display = P017LCD()
register_resource('display', display)
register_resource('chassis', get_regular_triangular_chassis(wheel_distance=290,
                                                            wheel_radius=60,
                                                            max_rotations_per_second=1.0))

register_task(name='manual_motion', value=ManualMotionTask())
register_menu_tasks_from_yaml(filename='menu_definition.yaml',
                              menu_task_class=TriangulaMenuClass,
                              resources=['joystick', 'display'])


@task(name='stop')
def stop_task(arduino: Arduino, display:P017LCD):
    """
    Shut down motors and bounce back to the main menu
    """
    arduino.stop()
    sleep(0.1)
    arduino.led0 = 'teal'
    display.led0 = 'teal'
    sleep(0.1)
    return 'main_menu'


# Loop forever until a task exits for a reason other than disconnection
while True:
    try:
        with ControllerResource() as joystick:

            # Tell the task system about the joystick
            register_resource('joystick', joystick)


            def check_joystick():
                """
                Called before every tick, sets up button presses, checks for joystick
                disconnection, and bounces back to the home menu via a motor shutdown
                task if the home button is pressed.
                """
                if not joystick.connected:
                    return TaskStop('disconnection')
                joystick.check_presses()
                if 'home' in joystick.presses:
                    return 'stop'


            # Run the task loop
            exit_reason = run(root_task='stop',
                              error_task='stop',
                              check_tasks=[check_joystick])

            # If we disconnected then wait for reconnection, otherwise break out
            # and exit the script.
            if exit_reason != 'disconnection':
                break

    except IOError:
        # Raised if there's no available controller, display this information
        display.text = ['Triangula', 'No Controller']
        sleep(1)
