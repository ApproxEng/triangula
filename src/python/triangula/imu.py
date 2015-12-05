__author__ = 'tom'
"""
Low level interface to the MPU. For whatever reason this wasn't working when used within an object. No idea why!
"""

import sys

sys.path.append('.')
import RTIMU
import os
import threading
import time

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


class IMUThread(threading.Thread):
    def __init__(self):
        super(IMUThread, self).__init__(name='IMU Thread')
        self.fusion_pose = None
        self.data_request = False
        self.setDaemon(daemonic=True)
        self.con = threading.Condition()

    def get_data(self):
        self.con.acquire()
        self.data_request = True
        self.fusion_pose = None
        self.con.notify()
        self.con.release()
        while not self.fusion_pose:
            time.sleep(_poll_interval / 2000.0)
        return self.fusion_pose

    def run(self):
        while True:
            self.con.acquire()
            while not self.data_request:
                self.con.wait()
            if _imu.IMURead():
                data = _imu.getIMUData()
                self.fusion_pose = data["fusionPose"]
                self.data_request = False
                time.sleep(_poll_interval / 1000.0)
            self.con.release()


thread = IMUThread()
thread.start()


def name():
    return 'IMU: {}, Pressure: {}'.format(_imu.IMUName(), _pressure.pressureName())


def read():
    return thread.get_data()
