__author__ = 'tom'
# Classes representing sensors on the robot

from math import pi
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


class IMU():
    """
    Class to read the fused compass / gyro / pressure / temp sensors contained in the MPU6050 breakout board. Uses the
    RTIMULib library to set up the chip and read its values. This class inherits from Thread as it needs to continuously
    monitor the IMU. When the thread is running the various get_xxx methods will return live data.
    """

    def __init__(self, settings_path='RTIMULib'):
        """
        Create a new proxy to the IMU, performing any necessary initialisation. This does not start the update thread.
        """
        sys.path.append('.')
        if not os.path.exists(settings_path + '.ini'):
            print 'Settings file not found at {}, will be created'.format(settings_path + '.ini')
        settings = RTIMU.Settings(settings_path)
        self.__imu = RTIMU.RTIMU(settings)
        self.__pressure = RTIMU.RTPressure(settings)
        print('IMU Name: ' + self.__imu.IMUName())
        print('Pressure Name: ' + self.__pressure.pressureName())

        self.__bearing_zero = 0
        self.__poll_interval = 0

    def _init_imu(self):
        if self.__imu.IMUInit():
            self._imu_poll_interval = self.__imu.IMUGetPollInterval() * 0.001
            self.__imu.setSlerpPower(0.02)
            self.__imu.setGyroEnable(True)
            self.__imu.setAccelEnable(True)
            self.__imu.setCompassEnable(True)
            print('IMU initialised')
        else:
            raise OSError('IMU init failed')

    def _init_pressure(self):
        if self.__pressure.pressureInit():
            print('Pressure sensor initialised')
        else:
            raise OSError('Pressure sensor init failed')

    def _read_imu(self):
        self._init_imu()
        self._init_pressure()
        attempts = 0
        success = False
        while not success and attempts < 3:
            success = self.__imu.IMURead()
            attempts += 1
            time.sleep(self.__poll_interval)

    def get_data(self):
        self._read_imu()
        data = self.__imu.getIMUData()
        (data['pressureValid'],
         data['pressure'],
         data['temperatureValid'],
         data['temperature']) = self.__pressure.pressureRead()
        return data

    def _get_bearing_uncorrected(self):
        data = self.get_data()
        if data is not None:
            return data['fusionPose'][2]

    def zero_bearing(self):
        """
        Sets the current heading as the new zero point
        """
        bearing = self._get_bearing_uncorrected()
        if bearing is not None:
            self.__bearing_zero = bearing

    def get_bearing(self):
        """
        Return the current bearing calculated by the compass / gyro fusion. Bearing is expressed in radians clockwise
        from the initial position of the robot when this class was initialised.

        :return:
            Float containing the value expressed as radians clockwise from the initial position.
        """
        bearing_uncorrected = self._get_bearing_uncorrected()
        if bearing_uncorrected is not None:
            corrected = bearing_uncorrected - self.__bearing_zero
            if corrected < -pi:
                corrected += 2 * pi
            elif corrected > pi:
                corrected -= 2 * pi
            return corrected
        return None

    def get_pitch(self):
        data = self.get_data()
        if data is not None:
            return data['fusionPose'][0]

    def get_roll(self):
        data = self.get_data()
        if data is not None:
            return data['fusionPose'][1]

    def get_temperature(self):
        data = self.get_data()
        if data is not None and data['temperatureValid']:
            return data['temperature']

    def get_altitude(self):
        data = self.get_data()
        if data is not None and data['pressureValid']:
            return 44330.8 * (1 - pow(data['pressure'] / 1013.25, 0.190263))

    def get_pressure(self):
        data = self.get_data()
        if data is not None and data['pressureValid']:
            return data['pressure']
