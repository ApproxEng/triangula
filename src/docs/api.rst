API Documentation
=================

Once the necessary native code and other supporting configuration has been set up, the following modules provide access
to Triangula's hardware.

PlayStation3 Controller Support
-------------------------------

The SixAxis class contains the logic to read from a PlayStation3 controller connected over BlueTooth, including axis
calibration, centering and dead-zones, and the ability to bind functions to button presses. This uses evdev for event
handling, attempting to use this on any other platform than Linux will probably not work.

.. autoclass:: triangula.input.SixAxis
    :members:

An additional class allows for use within a 'with' binding. The connection and disconnection is managed automatically
by the resource, so there's no need to call connect() on the generated :class:`triangula.input.SixAxis` instance.

.. autoclass:: triangula.input.SixAxisResource
    :members:

As an example, the following code will bind to an already paired PS3 controller and continuously print its axes:

.. code-block:: python

    from triangula.input import SixAxisResource
    # Get a joystick, this will fail unless the SixAxis controller is paired and active
    with SixAxisResource() as joystick:
        while 1:
            # Default behaviour is to print the values of the four analogue axes
            print joystick

Low-level Motion Dynamics
-------------------------

The HoloChassis class specifies a chassis defined as an arrangement of various size omni-wheels. Wheels can be added to
the chassis object with arbitrary orientation and position, and wheels of multiple sizes can be specified. This class
is then responsible for converting an arbitrary motion 3-vector (x, y, rotation) into target speeds for each wheel
expressed as revolutions per second.

.. autoclass:: triangula.chassis.HoloChassis
    :members:

Sensor Inputs
-------------

Classes for reading sensor data are contained in this module. The current set of sensors is relatively limited: the
encoders attached to each wheel provide absolute position information and a gyro / compass fusion provides orientation
but we plan to add more sensors such as LIDAR and other range-finder mechanisms once the basic chassis is completed.

.. automodule:: triangula.sensors
    :members: