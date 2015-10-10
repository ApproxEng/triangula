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
        self._imu = RTIMU.RTIMU(settings)
        self._pressure = RTIMU.RTPressure(settings)
        print('IMU Name: ' + self._imu.IMUName())
        print('Pressure Name: ' + self._pressure.pressureName())
        self._init_imu = False
        self._init_pressure = False
        self._bearing_zero = 0
        self._compass_enabled = False
        self._gyro_enabled = False
        self._accel_enabled = False
        self._last_orientation = {'pitch': 0, 'roll': 0, 'yaw': 0}

    def _imu_init(self):
        if not self._init_imu:
            self._init_imu = self._imu.IMUInit()
            if self._init_imu:
                self._imu_poll_interval = self._imu.IMUGetPollInterval() * 0.001
                # Enable everything on IMU
                self.set_imu_config(True, True, True)
            else:
                raise OSError('IMU Init Failed, please run as root / use sudo')

    def _pressure_init(self):
        if not self._init_pressure:
            self._init_pressure = self._pressure.pressureInit()
            if not self._init_pressure:
                raise OSError('Pressure Init Failed, please run as root / use sudo')

    def set_imu_config(self, compass_enabled, gyro_enabled, accel_enabled):
        """
        Enables and disables the gyroscope, accelerometer and/or magnetometer
        input to the orientation functions
        """

        # If the consuming code always calls this just before reading the IMU
        # the IMU consistently fails to read. So prevent unnecessary calls to
        # IMU config functions using state variables

        self._imu_init()  # Ensure imu is initialised

        if (not isinstance(compass_enabled, bool)
            or not isinstance(gyro_enabled, bool)
            or not isinstance(accel_enabled, bool)):
            raise TypeError('All set_imu_config parameters must be of boolan type')

        if self._compass_enabled != compass_enabled:
            self._compass_enabled = compass_enabled
            self._imu.setCompassEnable(self._compass_enabled)

        if self._gyro_enabled != gyro_enabled:
            self._gyro_enabled = gyro_enabled
            self._imu.setGyroEnable(self._gyro_enabled)

        if self._accel_enabled != accel_enabled:
            self._accel_enabled = accel_enabled
            self._imu.setAccelEnable(self._accel_enabled)

    def _init_pressure(self):
        if self._pressure.pressureInit():
            print('Pressure sensor initialised')
        else:
            raise OSError('Pressure sensor init failed')

    def _read_imu(self):
        self._imu_init()
        attempts = 0
        success = False
        self._imu_poll_interval = (float)(self._imu.IMUGetPollInterval()) * 0.001
        while not success and attempts < 3:
            success = self._imu.IMURead()
            attempts += 1
            time.sleep(self._imu_poll_interval)

    def get_data(self):
        self._read_imu()
        return self._imu.getIMUData()

    def _get_bearing_uncorrected(self):
        return self.get_orientation()['yaw']

    def zero_bearing(self):
        """
        Sets the current heading as the new zero point
        """
        bearing = self._get_bearing_uncorrected()
        if bearing is not None:
            self._bearing_zero = bearing

    def get_bearing(self):
        """
        Return the current bearing calculated by the compass / gyro fusion. Bearing is expressed in radians clockwise
        from the initial position of the robot when this class was initialised.

        :return:
            Float containing the value expressed as radians clockwise from the initial position.
        """
        bearing_uncorrected = self._get_bearing_uncorrected()
        if bearing_uncorrected is not None:
            corrected = bearing_uncorrected - self._bearing_zero
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

    def _get_raw_data(self, is_valid_key, data_key):
        """
        Internal. Returns the specified raw data from the IMU when valid
        """
        result = None
        if self._read_imu():
            data = self._imu.getIMUData()
            if data[is_valid_key]:
                raw = data[data_key]
                result = {
                    'x': raw[0],
                    'y': raw[1],
                    'z': raw[2]
                }
        return result

    def get_orientation(self):
        """
        Returns a dictionary object to represent the current orientation in
        radians using the aircraft principal axes of pitch, roll and yaw
        """

        raw = self._get_raw_data('fusionPoseValid', 'fusionPose')

        if raw is not None:
            raw['roll'] = raw.pop('x')
            raw['pitch'] = raw.pop('y')
            raw['yaw'] = raw.pop('z')
            self._last_orientation = raw

        return self._last_orientation

    def get_altitude(self):
        """
        Return an estimate of altitude based on the pressure sensor
        """
        pressure = self.get_pressure()
        if pressure is not None:
            return 44330.8 * (1 - pow(pressure / 1013.25, 0.190263))

    def get_pressure(self):
        """
        Returns the pressure in Millibars
        """
        self._pressure_init()  # Ensure pressure sensor is initialised
        pressure = 0
        data = self._pressure.pressureRead()
        if data[0]:  # Pressure valid
            pressure = data[1]
        return pressure

    def get_temperature(self):
        """
        Returns the temperature in Celsius from the pressure sensor
        """
        self._pressure_init()  # Ensure pressure sensor is initialised
        temp = 0
        data = self._pressure.pressureRead()
        if data[2]:  # Temp valid
            temp = data[3]
        return temp
