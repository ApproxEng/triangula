__author__ = 'tom'
# Classes representing sensors on the robot

from math import pi

import os
import RTIMU
import sys


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
    Class to read the fused compass / gyro / pressure sensor contained in the MPU6050 breakout board. Uses the
    RTIMULib library to set up the chip and read its values.
    """

    def __init__(self, settings_path='RTIMULib'):
        """
        Create a new proxy to the IMU, performing any necessary initialisation.
        """
        sys.path.append('.')
        if not os.path.exists(settings_path + '.ini'):
            print 'Settings file not found at {}, will be created'.format(settings_path + '.ini')
        s = RTIMU.Settings(settings_path)
        print s
        self.imu = RTIMU.RTIMU(s)
        print self.imu
        self.pressure = RTIMU.RTPressure(s)
        print self.pressure
        print('IMU Name: ' + self.imu.IMUName())
        print('Pressure Name: ' + self.pressure.pressureName())
        if not self.imu.IMUInit():
            raise RuntimeError('Unable to initialise IMU')
        else:
            print('Initialised IMU')
        self.imu.setSlerpPower(0.02)
        self.imu.setGyroEnable(True)
        self.imu.setAccelEnable(True)
        self.imu.setCompassEnable(True)
        self.bearing_zero = 0
        self.data = None
        self.update()

    def update(self):
        if self.imu.IMURead():
            self.data = self.imu.getIMUData()
            (self.data["pressureValid"], self.data["pressure"], self.data["temperatureValid"],
             self.data["temperature"]) = self.pressure.pressureRead()
            return True
        return False

    def zero_bearing(self):
        """
        Sets the current heading as the new zero point
        """
        if self.data is not None:
            self.bearing_zero = self.data['fusionPose'[2]]
        else:
            self.bearing_zero = 0

    def get_bearing(self):
        """
        Return the current bearing calculated by the compass / gyro fusion. Bearing is expressed in degrees clockwise
        from the initial position of the robot when this class was initialised.

        :return:
            Float containing the value expressed as radians clockwise from the initial position.
        """
        if self.data is not None:
            raw = self.data['fusionPose'[2]]
            corrected = raw - self.bearing_zero
            if corrected < -pi:
                corrected += 2 * pi
            elif corrected > pi:
                corrected -= 2 * pi
            return corrected
        return None

    def get_pitch(self):
        if self.data is not None:
            return self.data['fusionPose'[0]]
        return None

    def get_roll(self):
        if self.data is not None:
            return self.data['fusionPose'[1]]

    def get_temperature(self):
        if self.data is not None and self.data['temperatureValid']:
            return self.data['temperature']
        return None

    def get_altitude(self):
        def computeHeight(pressure_value):
            return 44330.8 * (1 - pow(pressure_value / 1013.25, 0.190263))
        if self.data is not None and self.data['pressureValid']:
            return computeHeight(pressure_value = self.data['pressure'])
        return None

    def get_pressure(self):
        if self.data is not None and self.data['pressureValid']:
            return self.data['pressure']
        return None