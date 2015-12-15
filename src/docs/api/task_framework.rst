triangula.task: Task Management
===============================

Tasks are single purpose activities that your robot may be doing. Examples include manual control, showing a system
menu, showing an error message (hopefully not too frequently), executing a route plan etc. Basically anything where
you're in an event loop, reading sensor data and other inputs, and acting on it to move or otherwise control the robot.

Because this is where a lot of the fun happens, we want to be able to create new tasks easily, and add them into
Triangula's menu system, select them with the controller, exit them cleanly etc. This package handles all that kind of
stuff.

The core concept is that of a :class:`triangula.task.Task` - this is a super-class which you extend, implementing the
``init_task`` and ``poll_task`` functions. The :class:`triangula.task.TaskManager` is responsible for calling the
appropriate functions in your task, to which it passes populated instances of :class:`triangula.task.TaskContext`. This
``TaskContext`` contains all the resources you might need in your task, such as an object to manage the chassis, one
that can communicate with the sensors, a reference to the joystick, a convenience function to help determine which
buttons have been pressed, basically anything your task will need to interact with the robot. The ``init_task`` is
called exactly once, and then ``poll_task`` is called as often as possible (use the
:class:`triangula.util.IntervalCheck` class to cope with this properly). The ``TaskManager`` will exit back to whatever
task it was started with if the SELECT button is pressed on the controller, but your task can also explicitly yield
control to another task by returning that new task from the ``poll_task`` function (if nothing is returned your current
task continues and will be polled again next time around). So, for example, you might make one task which allows you to
enter a set of waypoints with the controller, then yield from that task to one that can drive the robot through those
waypoints - doing this allows you to uncouple the route planning from the autopilot, so you can use both in other
overall tasks. The :class:`triangula.tasks.main_menu.MenuTask` is an example of this, it shows a menu of other tasks and
yields to whichever task is currently selected when the user hits the CROSS button on the controller.

.. automodule:: triangula.task
    :members:
