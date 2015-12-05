__author__ = 'tom'
"""
Low level interface to the MPU. For whatever reason this wasn't working when used within an object. No idea why!
"""

import sys

sys.path.append('.')
import RTIMU
import time
import os

SETTINGS_FILE = 'RTIMULib'
print("Using settings file " + SETTINGS_FILE + ".ini")
if not os.path.exists(SETTINGS_FILE + ".ini"):
    print("Settings file does not exist, will be created")
s = RTIMU.Settings(SETTINGS_FILE)
print s
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
_poll_interval = _imu.IMUGetPollInterval()
print("Recommended Poll Interval: %dmS\n" % _poll_interval)
_last_read_time = None
_last_read_value = None


def name():
    return 'IMU: {}, Pressure: {}'.format(_imu.IMUName(), _pressure.pressureName())


def read():
    global _last_read_value
    global _last_read_time
    time_now = time.time()
    if _last_read_time is not None:
        delta_millis = time_now - _last_read_time * 1000
        if delta_millis <= _poll_interval:
            return _last_read_value
    _last_read_value = None
    attempts = 0
    while not _last_read_value and attempts < 3:
        if _imu.IMURead():
            d = _imu.getIMUData()
            (d['pressureValid'], d['pressure'], d['temperatureValid'], d['temperature']) = _pressure.pressureRead()
            _last_read_value = d
            _last_read_time = time_now
        else:
            attempts += 1
            time.sleep(_poll_interval * 1.0 / 1000)
    return _last_read_value
