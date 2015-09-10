Raspberry Pi Configuration
==========================

Triangula's software is primarily written in Python, but there are some pre-requisites which must be either installed
or built from scratch, and which cannot be specified as dependencies in setuptools. In particular we need to enable and
set up I2C (Inter-Integrated Circuit) communication and build the bluetooth support modules for the Playstation 3
controller. This page describes the necessary steps, starting from a clean installation of Raspbian on a Raspberry Pi 2.

There's no guarantee that this will work with any other earlier board revision but there's also no particular reason it
shouldn't. We'll make use of the additional computing power of the v2 Pi when it comes to image analysis for line
following and similar but the basic functionality is relatively lightweight.