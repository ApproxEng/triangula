__author__ = 'tom'
# Classes representing sensors on the robot

class WheelEncoders():
    """
    Class to read absolute values of the quadrature encoders attached to the drive spindle on each wheel motor. These
    encoders are made available over the I2C bus from a microcontroller. This approach is used to allow for more robust
    interrupt driven handling of the encoders using the pin change interrupt vector on the ATMEGA328 chip (in this case
    within an Arduino Nano clone of some description).
    """

    def __init__(self):
        """
        Create a new proxy to the encoders. This doesn't attempt to actually read any data or test connectivity.
        """

    def read(self):
        """
        Read the values of the encoders. Values are stored as two byte unsigned integers in the microcontroller so will
        wrap at 0 and 2^16-1 for the low and high ends. The encoders emit around a thousand events per revolution, so it
        should be reasonably easy to distinguish between a wrap of the value and a genuinely large jump.

        :return:
            A sequence of integers containing the current absolute positions for each wheel
        """

class Compass():
    """
    Class to read the fused compass / gyro contained in the MPU6050 breakout board. Uses the RTIMULib library to set up
    the chip and read its values.
    """

    def __init__(self):
        """
        Create a new proxy to the compass, performing any necessary initialisation.
        """

    def get_bearing(self):
        """
        Return the current bearing calculated by the compass / gyro fusion. Bearing is expressed in degrees clockwise
        from the initial position of the robot when this class was initialised.

        :return:
            Float containing the value expressed as degrees clockwise from the initial position.
        """