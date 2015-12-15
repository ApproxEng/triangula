__author__ = 'tom'

from time import sleep

import smbus

ARDUINO_ADDRESS = 0x70

I2C_RETRIES = 30
I2C_DELAY = 0.01


def float_to_byte(f):
    """
    Map a float from -1.0 to 1.0 onto the range 0-255 and return as a byte-compatible number.
    Used when sending bytes for e.g. the speed controllers.

    :param f:
        A float, between -1.0 and 1.0. Values outside this range will not behave sensibly.
    :return:
        An integer where 128 is equivalent to 0, 0 to -1.0 and 255 to +1.0
    """
    i = int((f + 1.0) * 128.0)
    return check_byte(i)


def check_byte(b):
    """
    Clamp the supplied value to an integer between 0 and 255 inclusive

    :param b:
        A number
    :return:
        Integer representation of the number, limited to be between 0 and 255
    """
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

    DEVICE_MOTORS_SET = 0x20
    DEVICE_LIGHTS_SET = 0x21
    DEVICE_ENCODERS_READ = 0x22

    def __init__(self,
                 arduino_address=ARDUINO_ADDRESS,
                 i2c_delay=I2C_DELAY,
                 max_retries=I2C_RETRIES,
                 bus_id=1):
        """
        Create a new client, uses the I2C bus to communicate with the arduino.

        :param arduino_address:
            7-bit address of the arduino on the I2C bus
        :param i2c_delay:
            Delay in seconds, used when we either retry transactions or inbetween immediately
            consecutive read and write operations. This attempts to mitigate problems we've had
            where transactions have failed, probably because the arduino is still handling the
            previous read / write mode and gets confused.
        :param max_retries:
            The maximum number of retries to attempt when an IOError occurs during a transaction.
        :param bus_id:
            The bus ID used when initialising the smbus library. For the Pi2 this is 1, others may
            be on bus 0.
        """
        self._bus = smbus.SMBus(bus_id)
        self._i2c_delay = i2c_delay
        self._max_retries = max_retries
        self._address = arduino_address

    def _compute_checksum(self, register, data):
        xor = register
        for data_byte in data:
            xor ^= data_byte
        return xor

    def _send(self, register, data):
        retries_left = self._max_retries
        while retries_left > 0:
            try:
                data_with_checksum = []
                data_with_checksum.extend(data)
                data_with_checksum.append(self._compute_checksum(register, data))
                self._bus.write_i2c_block_data(self._address, register, data_with_checksum)
                return
            except IOError:
                sleep(self._i2c_delay)
                retries_left -= 1
                pass
        raise IOError("Retries exceeded sending data to arduino.")

    def _read(self, register, bytes_to_read):
        """
        Work around issues we seem to have with bulk transfers by transferring a byte at
        a time after manually triggering the population of the read buffer on the arduino.

        :param register:
            The register to write a 0 to in order to start the read transaction. The slave
            device should respond to this by populating the export array, this is then read
            a byte at a time.
        :param bytes_to_read:
            The number of times the read_byte method needs to be called
        :return:
            A byte array, length equal to bytes_to_read, containing data read from the arduino.
        """
        retries_left = self._max_retries
        while retries_left > 0:
            try:
                # Prod the appropriate control register
                self._send(register, [0])
                # Delay for an arbitrary amount of time
                sleep(self._i2c_delay*10)
                # Call read_byte repeatedly to assemble our output data
                data = [self._bus.read_byte(self._address) for _ in xrange(bytes_to_read)]
                return data
            except IOError:
                sleep(self._i2c_delay)
                retries_left -= 1
        raise IOError("Retries exceeded when fetching data from arduino.")

    def set_motor_power(self, a, b, c):
        """
        Set motor power, writing values directly to the Syren controllers. Power values range from -1.0 to 1.0, where
        positive values correspond to increasing encoder counts and clockwise rotation when viewed from the outside
        of the robot looking inwards.

        :param float a:
            Wheel a power, -1.0 to 1.0. Pink pylon.
        :param float b:
            Wheel a power, -1.0 to 1.0. Yellow pylon.
        :param float c:
            Wheel a power, -1.0 to 1.0. Green pylon.
        """
        motor_values = [float_to_byte(-a),
                        float_to_byte(-b),
                        float_to_byte(-c)]

        self._send(Arduino.DEVICE_MOTORS_SET, motor_values)

    def set_lights(self, hue, saturation, value):
        """
        Set all the neopixel lights to a constant value.

        :param hue:
            0-255 hue
        :param saturation:
            0-255 saturation
        :param value:
            0-255 value
        """
        light_values = [check_byte(hue), check_byte(saturation), check_byte(value)]
        self._send(Arduino.DEVICE_LIGHTS_SET, light_values)

    def get_encoder_values(self):
        """
        Read data from the encoders, returning as a triple of what would be a uint16
        if we had such things.

        :return:
            Triple of encoder values for each wheel.
        """
        encoder_data = self._read(Arduino.DEVICE_ENCODERS_READ, 6)
        return [encoder_data[0] * 256 + encoder_data[1],
                encoder_data[2] * 256 + encoder_data[3],
                encoder_data[4] * 256 + encoder_data[5]]
