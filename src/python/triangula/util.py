__author__ = 'tom'

import socket
import fcntl
import struct


def get_ip_address(ifname='WLAN0'):
    """
    Get a textual representation of the IP address for the specified interface, defaulting to WLAN0 to pick
    up our wireless connection if we have one.

    :param ifname:
        Name of the interface to query, defaults to 'WLAN0'

    :return:
        Textual representation of the IP address
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
