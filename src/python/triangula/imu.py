__author__ = 'tom'
"""
Low level interface to the MPU. For whatever reason this wasn't working when used within an object. No idea why!
"""

import sys

sys.path.append('.')
import RTIMU
import time

SETTINGS_FILE = 'RTIMULib'

s = RTIMU.Settings(SETTINGS_FILE)
_imu = RTIMU.RTIMU(s)
if not _imu.IMUInit():
    raise ImportError('Unable to initialise IMU')
_pressure = RTIMU.RTPressure(s)
if not _pressure.pressureInit():
    raise ImportError('Unable to initialise pressure sensor')
_imu.setSlerpPower(0.02)
_imu.setGyroEnable(True)
_imu.setAccelEnable(True)
_imu.setCompassEnable(True)
poll_interval = _imu.IMUGetPollInterval()


def name():
    return 'IMU: {}, Pressure: {}'.format(_imu.IMUName(), _pressure.pressureName())


def read():
    d = False
    attempts = 0
    while not d and attempts < 3:
        if _imu.IMURead():
            d = _imu.getIMUData()
            (d['pressureValid'], d['pressure'], d['temperatureValid'], d['temperature']) = _pressure.pressureRead()
        else:
            attempts += 1
            time.sleep(poll_interval * 1.0 / 1000)
    if d:
        return d
