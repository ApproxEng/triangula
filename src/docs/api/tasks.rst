triangula.tasks.*: Task Implementations
=======================================

This package contains modules with implementations of :class:`triangula.task.Task`. These are typically divided into
separate files for each task, each of which is then relatively short and easy to manage.

triangula.tasks.main_menu: Main Menu
------------------------------------

Main menu class, shows other tasks and allows the user to select one to run. This is used as the root task by default,
so pressing SELECT will always jump back to this task.

.. autoclass:: triangula.tasks.main_menu.MenuTask
    :members:

triangula.tasks.manual_control: Manual Control
----------------------------------------------

Reads from the joystick analogue axes and allows you to drive the robot around. Buttons can switch between relative
control (where the robot drives forwards when you push the left stick forwards, whatever direction its facing) and
absolute (where the robot will drive in a specific direction, typically the direction it was facing when this mode was
selected, irrespective of its current orientation). The display is used to show the current estimate of position and
bearing from the dead reckoning algorithm.

.. autoclass:: triangula.tasks.manual_control.ManualMotionTask
    :members:

triangula.tasks.network_info: Network Info
------------------------------------------

Displays the IP address, if any, for the ``eth0`` and ``wlan0`` interfaces, handy when your robot has picked up an
address with DHCP and you've no idea what it is.

.. autoclass:: triangula.tasks.network_info.NetworkInfoTask
    :members:

triangula.tasks.compass_test: Compass Test
------------------------------------------

Test class, used to attempt to debug issues with the IMU

.. autoclass:: triangula.tasks.compass_test.CompassTestTask
    :members:

