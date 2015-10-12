__author__ = 'tom'

import smbus

ARDUINO_ADDRESS = 0x77
DEVICE_MOTORS = 0x00


class Arduino:
    """
    Handles communication over I2C with the Arduino, exposing methods which can be used to
    read e.g. wheel encoder positions, and to set wheel speeds, light colours etc.

    Client code based on documentation at
    http://www.raspberry-projects.com/pi/programming-in-python/i2c-programming-in-python/using-the-i2c-interface-2

    The logic for programming the Arduino to respond to these messages is implemented
    elsewhere, and based on the code at http://dsscircuits.com/articles/arduino-i2c-slave-guide.
    """

    def __init__(self):
        self.bus = smbus.SMBus(1)

    def set_power(self, a, b, c):
        """
        Set motor power, writing values directly to the Syren controllers

        :param int a:
            signed 8 bit power value from -127 to 127 for wheel a
        :param int b:
            signed 8 bit power value from -127 to 127 for wheel b
        :param int c:
            signed 8 bit power value from -127 to 127 for wheel c
        """
        motor_values = [a, b, c]
        self.bus.write_i2c_block_data(ARDUINO_ADDRESS, DEVICE_MOTORS, motor_values)

    def set_lights(self, brightness, a1, a2, b1, b2, c1, c2):
        """
        Set the end colours of the light strips, and their overall brightness

        :param int brightness:
            8 bit unsigned int, 0 is off, 255 is full intensity
        :param int a1:
            8 bit unsigned int, hue for top of light stick a
        :param int a2:
            8 bit unsigned int, hue for bottom of light stick a
        :param int b1:
            8 bit unsigned int, hue for top of light stick b
        :param int b2:
            8 bit unsigned int, hue for bottom of light stick b
        :param int c1:
            8 bit unsigned int, hue for top of light stick c
        :param int c2:
            8 bit unsigned int, hue for bottom of light stick c
        """

    def get_encoder_values(self):
        """
        Retrieve encoder values from the arduino, these values are unsigned 16 bit integers

        :return:
            an array of ints containing the encoder values for wheels a, b, and c.
        """