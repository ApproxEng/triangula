__author__ = 'tom'

import socket
import fcntl
import struct


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