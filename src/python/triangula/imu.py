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
imu.setSlerpPower(0.02)
imu.setGyroEnable(True)
imu.setAccelEnable(True)
imu.setCompassEnable(True)
poll_interval = imu.IMUGetPollInterval()


def get_data():
    success = False
    attempts = 0
    while not success and attempts < 3:
        if imu.IMURead():
            success = imu.getIMUData()
        else:
            attempts += 1
            time.sleep(poll_interval * 1.0 / 1000)
    if success:
        return success
