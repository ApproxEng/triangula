__author__ = 'tom'

import smbus

ARDUINO_ADDRESS = 0x70
DEVICE_MOTORS_SET = 0x20
DEVICE_LIGHTS_SET = 0x21


def float_to_byte(f):
    i = int((f + 1.0) * 128.0)
    return check_byte(i)


def check_byte(b):
    i = int(b)
    if i < 0:
        i = 0
    elif i > 255:
        i = 255
    return i


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

    def _send(self, register, data):
        success = False
        retries = 4
        while not success:
            try:
                self.bus.write_i2c_block_data(ARDUINO_ADDRESS, register, data)
                success = True
            except IOError:
                retries -= 1
                if retries == 0:
                    raise IOError("Can't communicate with I2C bus")
                pass

    def _read(self, register, bytes):
        success = False
        while not success:
            try:
                return self.bus.read_i2c_block_data(ARDUINO_ADDRESS, register)[:bytes]
            except IOError:
                pass

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
        motor_values = [float_to_byte(a),
                        float_to_byte(b),
                        float_to_byte(c)]

        self._send(DEVICE_MOTORS_SET, motor_values)

    def set_lights(self, hue, saturation, value):
        """
        Set the neopixel lights to a constant value
        :param hue: 0-255 hue
        :param saturation: 0-255 saturation
        :param value: 0-255 value
        """
        light_values = [check_byte(hue), check_byte(saturation), check_byte(value)]
        self._send(DEVICE_LIGHTS_SET, light_values)

    def get_encoder_values(self):
        """
        Read data from the encoders, returning as a triple of what would be a uint16 if we had such things.
        :return: Triple of encoder values for each wheel.
        """
        encoder_data = self._read(0, 6)
        return [encoder_data[0] * 256 + encoder_data[1],
                encoder_data[2] * 256 + encoder_data[3],
                encoder_data[4] * 256 + encoder_data[5]]
