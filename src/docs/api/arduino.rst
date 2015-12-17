triangula.arduino: Controlling the Arduino
==========================================

The Raspberry Pi is great, but sometimes you need to work closer to the hardware than is comfortable on a computer with
a full operating system. In Triangula's case, we have three wheels, each of which has a quadrature encoder on the motor
shaft to measure rotation. Quadrature encoders work by sending two streams of on / off signals, by monitoring these
streams and detecting changes we can calculate exactly where Triangula's wheels are. However, to do that we have to
be able to monitor six rapidly changing inputs - if we tried to do this with the Python code we'd certainly end up
missing some of them, and that would make our wheel positions inaccurate. No good.

To solve this, Triangula has an Arduino - in contrast to the Pi, the Arduino is extremely simple, it's really just a
single microcontroller (a much simpler processor than the ARM chip on the Pi) and the bare minimum needed to make that
chip work. The lovely thing about the Arduino is that it doesn't have an operating system, sd-card, display, network, or
really anything that makes a modern computer useful. The reason this is a lovely thing, rather than a drawback, is that
it means there is nothing else running on the chip; when we run code on the Pi there's all sorts of other stuff
happening behind the scenes that we can't see, when we run code on the Arduino we know exactly what's happening, so it's
a great environment to run code which has to handle fast data processing, read analogue values (the Arduino has built-in
analogue input), and other low level stuff.

So, in the case of our wheel encoders, the Arduino is responsible for the low level monitoring of the encoder data, and
for interpreting it and working out a wheel position, and the Pi then needs to be able to get that calculated position
from the Arduino. To do this we use the I2C bus through the ``smbus`` module. This is a very low-level interface, in
that all it allows you to do is send and receive bytes of data from devices connected to the I2C bus. To make this more
friendly the :class:`triangula.arduino.Arduino` class exists, wrapping up the low level calls to the ``smbus`` library,
and thence to the Arduino, into things that look more like sensible Python function calls.

Python Code
-----------

This code runs on the Pi and sends messages to the Arduino over I2C

.. automodule:: triangula.arduino
    :members:

Arduino Code
------------

This code runs on the Arduino and receives messages from the Pi over I2C

The main code running on the Arduino. This is responsible for monitoring the wheel encoders, sending power values to the
Syren10 motor drivers, and for setting colours on the attached LEDs.

.. literalinclude:: ../../arduino/Triangula_Main/Triangula_Main.ino
    :caption: Triangula_Main.ino
    :language: c
    :linenos:

Triangula_NeoPixel
__________________

A simple extension to the AdaFruit NeoPixel library to handle colours in HSV space rather than RGB, and to manage a
slightly higher-level view on the neopixel strips.

.. literalinclude:: ../../arduino/Triangula_Main/Triangula_NeoPixel.h
    :caption: Triangula_NeoPixel.h
    :language: c
    :linenos:

.. literalinclude:: ../../arduino/Triangula_Main/Triangula_NeoPixel.cpp
    :caption: Triangula_NeoPixel.cpp
    :language: c
    :linenos:
