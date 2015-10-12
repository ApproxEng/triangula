__author__ = 'tom'

import smbus

ARDUINO_ADDRESS = 0x70
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

    def set_motor_power(self, a, b, c):
        """
        Set motor power, writing values directly to the Syren controllers

        :param float a:
            Wheel a power, -1.0 to 1.0
        :param float b:
            Wheel a power, -1.0 to 1.0
        :param float c:
            Wheel a power, -1.0 to 1.0
        """

        def float_to_byte(f):
            i = int((f + 1.0) * 128.0)
            if i < 0:
                i = 0
            elif i > 255:
                i = 255
            return i

        motor_values = [float_to_byte(a),
                        float_to_byte(b),
                        float_to_byte(c)]

        # Sometimes get IOError when sending due to clock stretch, a simple retry normally fixes it.
        success = False
        while not success:
            try:
                self.bus.write_i2c_block_data(ARDUINO_ADDRESS, DEVICE_MOTORS, motor_values)
                success = True
            except IOError:
                print('IOError, retrying')