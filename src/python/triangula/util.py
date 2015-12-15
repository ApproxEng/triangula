__author__ = 'tom'

import fcntl
import socket
import struct
from time import time


class IntervalCheck:
    """
    Utility class which can be used to run code within a polling loop at most once per n seconds. Set up an instance
    of this class with the minimum delay between invocations then enclose the guarded code in a construct such as
    if interval.should_run(): - this will manage the scheduling and ensure that the inner code will only be called if
    at least the specified amount of time has elapsed.
    """

    def __init__(self, interval):
        """
        Constructor

        :param float interval:
            The number of seconds that must pass between True values from the should_run() function
        """
        self.interval = interval
        self.last_time = None

    def should_run(self):
        now = time()
        if self.last_time is None or now - self.last_time > self.interval:
            self.last_time = now
            return True
        else:
            return False


def get_ip_address(ifname='wlan0'):
    """
    Get a textual representation of the IP address for the specified interface, defaulting to wlan0 to pick
    up our wireless connection if we have one.

    :param ifname:
        Name of the interface to query, defaults to 'wlan0'

    :return:
        Textual representation of the IP address
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])
    except Exception:
        return '--.--.--'
