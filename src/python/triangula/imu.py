import sys
import threading
import time

import os

sys.path.append('.')

_imu = None

try:
    import RTIMU

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
except ImportError:
    print 'Not importing RTIMU, expected during sphinx generation on OSX'


class IMUThread(threading.Thread):
    def __init__(self):
        super(IMUThread, self).__init__(name='IMU Thread')
        self.fusion_pose = None
        self.setDaemon(daemonic=True)

    def run(self):
        while True:
            if _imu.IMURead():
                data = _imu.getIMUData()
                self.fusion_pose = data["fusionPose"]
                time.sleep(_poll_interval * 2.0 / 1000.0)

if _imu is not None:
    thread = IMUThread()
    thread.start()


def name():
    return 'IMU: {}, Pressure: {}'.format(_imu.IMUName(), _pressure.pressureName())


def read():
    return thread.fusion_pose
