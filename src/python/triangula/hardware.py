"""
Hardware drivers for Triangula's motor driver boards, encoders, LED lighting, and LCD display. The motor drivers,
encoders, and LEDs are driven from an Arduino nano sitting on a simple custom HAT, the serial display is attached
directory to the Pi via a level shifter. There's an IMU available on the I2C bus as well, an MPU9150 breakout
board. This isn't used anywhere in the current code, but in principle it should be able to provide acceleration
information and similar, it also has a temperature sensor.
"""
import colorsys
import logging
from typing import List
from time import sleep
import serial
from approxeng.hwsupport import add_properties
from smbus2 import SMBus

from triangula.util import IntervalCheck

LOG = logging.getLogger('triangula.hardware')


class MPU9150:
    """
    Attached motion processor
   """
    ACCEL_RANGES = {2: 0x00,
                    4: 0x08,
                    8: 0x10,
                    16: 0x18}

    GYRO_RANGES = {250: 0x00,
                   500: 0x08,
                   1000: 0x10,
                   2000: 0x18}

    ACCEL_CONFIG = 0x1C
    GYRO_CONFIG = 0x1B

    def __init__(self, address=0x68, bus=1):
        self._address = address
        self._bus = bus

        # Wake up the sensor
        PWR_MGMT_1 = 0x6B
        with SMBus(self._bus) as bus:
            bus.write_byte_data(self._address, PWR_MGMT_1, 0x00)

    def _read_i2c_word(self, register: int) -> int:
        # Read data from a pair of consecutive registers
        with SMBus(self._bus) as bus:
            high = bus.read_byte_data(self._address, register)
            low = bus.read_byte_data(self._address, register + 1)

        value = (high << 8) + low
        if value >= 0x8000:
            return -((65535 - value) + 1)
        else:
            return value

    def _read_i2c_byte(self, register: int) -> int:
        """
        Read a single byte from a register
        """
        with SMBus(self._bus) as bus:
            return bus.read_byte_data(self._address, register)

    @property
    def temperature(self):
        """
        Temperature in degrees Celsius
        """
        TEMP_OUT0 = 0x41
        raw_temp = self._read_i2c_word(TEMP_OUT0)
        return (raw_temp / 340.0) + 35

    @property
    def accel_range(self):
        """
        Acceleration range in g, will be one of 2, 4, 8, 16
        """
        raw_data = self._read_i2c_byte(self.ACCEL_CONFIG)
        for g, raw in self.ACCEL_RANGES.items():
            if raw == raw_data:
                return g
        return None

    @accel_range.setter
    def accel_range(self, g):
        """
        Set range, must be one of 2, 4, 8, 16
        """
        if g in self.ACCEL_RANGES:
            raw_data = self.ACCEL_RANGES[g]
            with SMBus(self._bus) as bus:
                bus.write_byte_data(self._address, self.ACCEL_CONFIG, 0x00)
                bus.write_byte_data(self._address, self.ACCEL_CONFIG, raw_data)
        else:
            raise ValueError(f'acceleration range must be in {self.ACCEL_RANGES.keys()}')

    @property
    def acceleration(self):
        """
        3 vector in meters per second squared
        """
        ACCEL_XOUT0 = 0x3B
        ACCEL_YOUT0 = 0x3D
        ACCEL_ZOUT0 = 0x3F
        GRAVITIY_MS2 = 9.80665
        scale = 32768 / (self.accel_range * GRAVITIY_MS2)
        return {'x': self._read_i2c_word(ACCEL_XOUT0) / scale,
                'y': self._read_i2c_word(ACCEL_YOUT0) / scale,
                'z': self._read_i2c_word(ACCEL_ZOUT0) / scale}

    @property
    def magnetometer(self):
        """
        Values in micro-Tesla TODO - this doesn't work at the moment for some reason
        """
        MAG_XOUT0 = 0x03
        MAG_YOUT0 = 0x05
        MAG_ZOUT0 = 0x07
        MAG_CTRL = 0x0A
        scale = 1229 / 4096
        with SMBus(bus=self._bus) as bus:
            bus.write_byte_data(i2c_addr=self._address, register=MAG_CTRL, value=0b001)
        return {'x': self._read_twos_complement_word(MAG_XOUT0) * scale,
                'y': self._read_twos_complement_word(MAG_YOUT0) * scale,
                'z': self._read_twos_complement_word(MAG_ZOUT0) * scale}

    def _read_twos_complement_word(self, register: int) -> int:
        # Read data from a pair of consecutive registers
        with SMBus(self._bus) as bus:
            high = bus.read_byte_data(self._address, register)
            low = bus.read_byte_data(self._address, register + 1)
        if high > 15:
            return low + (high & 0b1111) * 256 - 4096
        else:
            return low + high * 256

    @property
    def gyro_range(self):
        """
        Gyro range will be one of 250, 500, 1000, or 2000
        """
        raw_data = self._read_i2c_byte(self.GYRO_CONFIG)
        for t, raw in self.GYRO_RANGES.items():
            if raw == raw_data:
                return t
        return None

    @gyro_range.setter
    def gyro_range(self, t):
        if t in self.GYRO_RANGES:
            raw_data = self.GYRO_RANGES[t]
            with SMBus(self._bus) as bus:
                bus.write_byte_data(self._address, self.GYRO_CONFIG, 0x00)
                bus.write_byte_data(self._address, self.GYRO_CONFIG, raw_data)
        else:
            raise ValueError(f'gyro range must be in {self.GYRO_RANGES.keys()}')

    @property
    def gyro(self):
        """
        3 vector in degrees per second squared
        """
        GYRO_XOUT0 = 0x43
        GYRO_YOUT0 = 0x45
        GYRO_ZOUT0 = 0x47
        scale = 32768 / self.gyro_range
        return {'x': self._read_i2c_word(GYRO_XOUT0) / scale,
                'y': self._read_i2c_word(GYRO_YOUT0) / scale,
                'z': self._read_i2c_word(GYRO_ZOUT0) / scale}


class Arduino:
    """
    The attached microcontroller on the I2C bus which manages the Syren10 motor drivers, rotary
    encoders on the wheels, and the integrated neopixel strips and rings
    """

    def __init__(self, address=0x70, bus=1):
        self._bus = bus
        self._address = address
        add_properties(board=self, leds=[0])
        self.led0_brightness = 0.8
        self.led0_gamma = 1.5

    @staticmethod
    def _float_to_byte(f: float) -> int:
        return Arduino._check_byte(int((f + 1.0) * 128.0))

    @staticmethod
    def _check_byte(b: int) -> int:
        return min(255, max(0, int(b)))

    def _send(self, register: int, data: List[int]):
        def checksum():
            xor = register
            for data_byte in data:
                xor ^= data_byte
            return [xor]

        with SMBus(self._bus) as bus:
            block = data + checksum()
            LOG.debug(f'sending "{block}" to I2C')
            try:
                bus.write_i2c_block_data(i2c_addr=self._address,
                                         register=register,
                                         data=data + checksum())
            except IOError:
                retries = 0
                success = False
                while retries < 10 and not success:
                    try:
                        sleep(0.02)
                        bus.write_i2c_block_data(i2c_addr=self._address,
                                                 register=register,
                                                 data=data + checksum())
                        success = True
                    except IOError:
                        retries += 1


    def _read(self, register: int, bytes_to_read: int):
        self._send(register, [0])
        with SMBus(self._bus) as bus:
            # Arduino code expects to see one at a time requests here, so while
            # the newer smbus2 actually works fine with a bulk read, the microcontroller
            # code does not and I don't really want to mess around with it now.
            return [bus.read_byte(self._address) for _ in range(bytes_to_read)]
            # return bus.read_i2c_block_data(i2c_addr=self._address, register=register, length=bytes_to_read)

    def _set_led_rgb(self, led: int = 0, red: float = 0, green: float = 0, blue: float = 0):
        assert led == 0
        light_values = list([Arduino._check_byte(f * 255) for f in colorsys.rgb_to_hsv(red, blue, green)])
        self._send(register=0x21, data=light_values)

    def set_motor_power(self, a, b, c):
        """
        Set motor powers, values from -1.0 to 1.0
        """
        self._send(register=0x20, data=[Arduino._float_to_byte(-f) for f in [a, b, c]])

    def stop(self):
        self.set_motor_power(0, 0, 0)

    @property
    def encoder_values(self):
        """
        Raw values from the three rotary encoders attached to the motors
        """
        data = self._read(register=0x22, bytes_to_read=6)
        return list([a * 256 + b for a, b in zip(data[::2], data[1::2])])


class P017LCD:
    """
    Driver for a https://projects-raspberry.com/lcd-chip-p017serial-p018i2c/ 16x2 LCD display
    with an RGB backlight driven over a serial port

    Backlight is available as the led0 property, can be set to CSS4 colours by name as per
    approxeng.hwsupport LED management. Set text by writing to the 'text' property.
    """

    def __init__(self, port='/dev/serial0', baudrate=9600, min_delay=0.05, columns=16, rows=2):
        self._port = port
        self._baudrate = baudrate
        self._text = [''] * rows
        self._interval = IntervalCheck(interval=min_delay)
        self._columns = columns
        self._rows = rows
        add_properties(board=self, leds=[0])

    @property
    def text(self):
        return self._rows

    @text.setter
    def text(self, new_text):
        """
        Set text either with a string (which will be wrapped around the columns) or with a list of
        strings which will be treated as rows. In our case we only have two rows!
        """
        if isinstance(new_text, str):
            self._text = list(new_text[row * self._columns:self._columns] for row in range(self._rows))
            self._update()
        elif isinstance(new_text, list):
            self._text = [''] * self._rows
            for i in range(min(self._rows, len(new_text))):
                self._text[i] = new_text[i][:self._columns]
            self._update()
        else:
            self.text = str(new_text)

    def clear(self):
        """
        Clear the display
        """
        with self._interval:
            self._send('pc1')

    def cursor_off(self):
        """
        Disable the cursor
        """
        with self._interval:
            self._send('pc12')

    def cursor_blink(self):
        """
        Set the cursor to a flashing block
        """
        with self._interval:
            self._send('pc15')

    def cursor_on(self):
        """
        Set the cursor to a normal underscore character
        """
        with self._interval:
            self._send('pc14')

    def _set_led_rgb(self, led: int = 0, red: float = 0, green: float = 0, blue: float = 0):
        """
        Set the backlight colour, red green and blue values all range from 0 to 1.0
        """

        def to_range(i: float) -> str:
            # noinspection PyTypeChecker
            return str(round(max(0, min(i, 1.0)) * 10))

        with self._interval:
            self._send('pb' + to_range(red) + ',' + to_range(green) + ',' + to_range(blue))

    def _update(self):
        with self._interval:
            self._send('pc2')
            self._send('pd' + self._text[0].ljust(40) + self._text[1].ljust(16))

    def _send(self, command):
        with serial.Serial(port=self._port, baudrate=self._baudrate) as ser:
            ser.write(command.encode('UTF-8') + bytes([0xd]))
            LOG.debug(f'written "{command}" to serial')
