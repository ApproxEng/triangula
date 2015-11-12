__author__ = 'tom'

import serial


class LCD():
    """
    Handle the serial attached LCD display

    To enable this display on the Raspberry Pi you need to first disable the serial console from raspi-config

    """

    def __init__(self):
        """
        Create a new serial connection and clear the display
        """
        self.ser = serial.Serial(port='/dev/ttyAMA0', baudrate=9600)
        self.row1 = ''
        self.row2 = ''
        self.clear()

    def set_text(self, row1=None, row2=None):
        """
        Set the text for either or both rows, send the updated values to the display. In order to fit on our display
        both rows must be at most sixteen characters in length. The display controller actually accepts 40 character
        rows but the display won't display them! This will trim any strings to 16 characters as that's the maximum
        length of our rows

        :param row1:
            Text for row 1
        :param row2:
            Text for row 2
        """
        if row1 is not None:
            self.row1 = row1[:16]
        if row2 is not None:
            self.row2 = row2[:16]
        self._update()

    def set_backlight(self, red=0, green=0, blue=0):
        """
        Set the backlight colour, red green and blue values all range from 0 to 10

        :param red:
            Red value, int 0 to 10
        :param green:
            Green value, int 0 to 10
        :param blue:
            Blue value, int 0 to 10
        """
        if red > 10:
            red = 10
        elif red < 0:
            red = 0
        if green > 10:
            green = 10
        elif green < 0:
            green = 0
        if blue > 10:
            blue = 10
        elif blue < 0:
            blue = 0
        self._send('pb' + str(red) + ',' + str(green) + ',' + str(blue))

    def clear(self):
        """
        Clear the display
        """
        self._send('pc1')

    def cursor_off(self):
        """
        Disable the cursor
        """
        self._send('pc12')

    def cursor_blink(self):
        """
        Set the cursor to a flashing block
        """
        self._send('pc15')

    def cursor_on(self):
        """
        Set the cursor to a normal underscore character
        """
        self._send('pc14')

    def _update(self):
        """
        Update the display with the current text in row1 and row2

        :internal:
        """
        self.clear()
        padded_row1 = self.row1 + ' ' * (40 - len(self.row1))
        self._send('pd' + padded_row1 + self.row2)

    def _send(self, command):
        """
        Send a carriage return terminated message to the display

        :internal:

        :param command:
            string or byte array to send
        """
        self.ser.write(command)
        self.ser.write([0xd])