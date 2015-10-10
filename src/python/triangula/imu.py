__author__ = 'tom'
import sys

sys.path.append('.')
import RTIMU
import time

SETTINGS_FILE = 'RTIMULib'

s = RTIMU.Settings(SETTINGS_FILE)
imu = RTIMU.RTIMU(s)
if not imu.IMUInit():
    raise ImportError('Unable to initialise IMU')
pressure = RTIMU.RTPressure(s)
if not pressure.PressureInit():
    raise ImportError('Unable to initialise pressure sensor')
imu.setSlerpPower(0.02)
imu.setGyroEnable(True)
imu.setAccelEnable(True)
imu.setCompassEnable(True)
poll_interval = imu.IMUGetPollInterval()

def name():
    return 'IMU: {}, Pressure: {}'.format(imu.IMUName(), pressure.pressureName())

def imu():
    d = False
    attempts = 0
    while not d and attempts < 3:
        if imu.IMURead():
            d = imu.getIMUData()
            (d['pressureValid'], d['pressure'], d['temperatureValid'], d['temperature']) = pressure.pressureRead()
        else:
            attempts += 1
            time.sleep(poll_interval * 1.0 / 1000)
    if d:
        return d
