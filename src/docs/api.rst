API Documentation
=================

PlayStation3 Controller Support
-------------------------------

The SixAxis class contains the logic to read from a PlayStation3 controller connected over BlueTooth, including axis
calibration, centering and dead-zones, and the ability to bind functions to button presses. This uses pygame's joystick
support, and by default also performs the necessary pygame initialisation. If you're using pygame's event queue
elsewhere in your project you might need to go and change this.

.. autoclass:: triangula.input.SixAxis
    :members:

