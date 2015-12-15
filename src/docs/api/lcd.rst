triangula.lcd: Serial LCD Display Support
=========================================

Triangula uses a simple 16x2 LCD display to provide feedback. This display is connected to the serial port of the
Raspberry Pi, it can accept commands to change the cursor, the colour of the backlight, clear the display and to display
text. Because the command set is slightly cryptic and because there appear to be timing issues, I've wrapped up this
functionality into a simple Python class:

.. autoclass:: triangula.lcd.LCD
    :members: