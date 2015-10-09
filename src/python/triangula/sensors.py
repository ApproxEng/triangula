__author__ = 'tom'
# Classes representing sensors on the robot

from math import pi
from threading import Thread
import sys
import time

import os
import RTIMU


class WheelEncoders():
    """
    Class to read absolute values of the quadrature encoders attached to the drive spindle on each wheel motor. These
    encoders are made available over the I2C bus from a microcontroller. This approach is used to allow for more robust
    interrupt driven handling of the encoders using the pin change interrupt vector on the ATMEGA328 chip (in this case
    within an Arduino Nano clone of some description).
    """

    def __init__(self):
        """
        Create a new proxy to the encoders. This doesn't attempt to actually read any data or test connectivity.
        """

    def read(self):
        """
        Read the values of the encoders. Values are stored as two byte unsigned integers in the microcontroller so will
        wrap at 0 and 2^16-1 for the low and high ends. The encoders emit around a thousand events per revolution, so it
        should be reasonably easy to distinguish between a wrap of the value and a genuinely large jump.

        :return:
            A sequence of integers containing the current absolute positions for each wheel
        """


class IMU(Thread):
    """
    Class to read the fused compass / gyro / pressure / temp sensors contained in the MPU6050 breakout board. Uses the
    RTIMULib library to set up the chip and read its values. This class inherits from Thread as it needs to continuously
    monitor the IMU. When the thread is running the various get_xxx methods will return live data.
    """

    def __init__(self, settings_path='RTIMULib'):
        """
        Create a new proxy to the IMU, performing any necessary initialisation. This does not start the update thread.
        """
        Thread.__init__(self, name='IMU Update Thread')
        self.setDaemon(True)
        sys.path.append('.')
        if not os.path.exists(settings_path + '.ini'):
            print 'Settings file not found at {}, will be created'.format(settings_path + '.ini')
        settings = RTIMU.Settings(settings_path)
        self.__imu = RTIMU.RTIMU(settings)
        self.__pressure = RTIMU.RTPressure(settings)
        print('IMU Name: ' + self.__imu.IMUName())
        print('Pressure Name: ' + self.__pressure.pressureName())

        # Initialise IMU, throwing a runtime error if we can't
        if not self.__imu.IMUInit():
            raise RuntimeError('Unable to initialise IMU')
        else:
            print('Initialised IMU')
        self.__imu.setSlerpPower(0.02)
        self.__imu.setGyroEnable(True)
        self.__imu.setAccelEnable(True)
        self.__imu.setCompassEnable(True)

        # Initialise pressure sensor, if we have one
        if not self.__pressure.pressureInit():
            print("Pressure sensor Init Failed")
        else:
            print("Pressure sensor Init Succeeded")

        self.__bearing_zero = 0
        self.__data = None
        self.__running = None

    def run(self):
        print 'Starting IMU update thread'
        self.__running = True
        poll_interval = self.__imu.IMUGetPollInterval()
        while self.__running:
            if self.__imu.IMURead():
                self.__data = self.__imu.getIMUData()
                (self.__data['pressureValid'],
                 self.__data['pressure'],
                 self.__data['temperatureValid'],
                 self.__data['temperature']) = self.__pressure.pressureRead()
            time.sleep(poll_interval * 1.0 / 1000.0)
        print 'Exiting IMU update thread'

    def stop(self):
        self.__running = False

    def zero_bearing(self):
        """
        Sets the current heading as the new zero point
        """
        if self.__data is not None:
            self.__bearing_zero = self.__data['fusionPose'][2]
        else:
            self.__bearing_zero = 0

    def get_bearing(self):
        """
        Return the current bearing calculated by the compass / gyro fusion. Bearing is expressed in degrees clockwise
        from the initial position of the robot when this class was initialised.

        :return:
            Float containing the value expressed as radians clockwise from the initial position.
        """
        if self.__data is not None:
            raw = self.__data['fusionPose'][2]
            corrected = raw - self.__bearing_zero
            if corrected < -pi:
                corrected += 2 * pi
            elif corrected > pi:
                corrected -= 2 * pi
            return corrected
        return None

    def get_pitch(self):
        if self.__data is not None:
            return self.__data['fusionPose'][0]
        return None

    def get_roll(self):
        if self.__data is not None:
            return self.__data['fusionPose'][1]

    def get_temperature(self):
        if self.__data is not None and self.__data['temperatureValid']:
            return self.__data['temperature']
        return None

    def get_altitude(self):
        def compute_height(pressure_value):
            return 44330.8 * (1 - pow(pressure_value / 1013.25, 0.190263))

        if self.__data is not None and self.__data['pressureValid']:
            return compute_height(pressure_value=self.__data['pressure'])
        return None

    def get_pressure(self):
        if self.__data is not None and self.__data['pressureValid']:
            return self.__data['pressure']
        return None
