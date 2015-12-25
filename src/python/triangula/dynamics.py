from time import time as time_now

from triangula.chassis import Motion


class MotionLimit:
    """
    Utility class to limit rate of motion changes, similar to the :class:`triangula.dynamics.RateLimit` but specialised
    to limit rate of change of :class:`triangula.chassis.Motion` instances.
    """

    def __init__(self, linear_acceleration_limit, angular_acceleration_limit):
        """
        Create a new instance configured with the specified limits.
        :param float linear_acceleration_limit:
            Maximum allowed linear acceleration in mm per second per second
        :param radial_acceleration_limit:
            Maximum allowed radial acceleration in radians per second per second
        """
        self.linear_acceleration_limit = linear_acceleration_limit
        self.angular_acceleration_limit = angular_acceleration_limit
        self.last_motion = None
        self.last_motion_time = None

    def limit_and_return(self, motion):
        """
        Apply limits to the requested motion based on the current state of the MotionLimit, returning the closest Motion
        which complies with the specified limits.

        :param triangula.chassis.Motion motion:
            The requested :class:`triangula.chassis.Motion`,
        :return:
            The modified motion, or the supplied one if it complied with the limits
        """
        now = time_now()
        if self.last_motion is None:
            self.last_motion = motion
            self.last_motion_time = now
            return motion
        # Calculate the requested linear acceleration magnitude in mm/s/s to achieve the desired motion change
        time_delta = now - self.last_motion_time
        motion_delta = abs(motion.translation - self.last_motion.translation)
        linear_acceleration = motion_delta / time_delta
        angular_acceleration = abs(motion.rotation - self.last_motion.rotation) / time_delta
        scaling = 1.0
        if linear_acceleration > self.linear_acceleration_limit:
            scaling = self.linear_acceleration_limit / linear_acceleration
        if angular_acceleration > self.angular_acceleration_limit:
            scaling = min(scaling, self.angular_acceleration_limit / angular_acceleration)
        scaled_translation = motion.translation * scaling + self.last_motion.translation * (1.0 - scaling)
        ':type : euclid.Vector2'
        scaled_rotation = motion.rotation * scaling + self.last_motion.rotation * (1.0 - scaling)
        scaled_motion = Motion(rotation=scaled_rotation, translation=scaled_translation)
        self.last_motion = scaled_motion
        self.last_motion_time = now
        return scaled_motion


class RateLimit:
    """
    Utility class to provide time-based rate limiting.
    """

    def __init__(self, limit_function=None):
        """
        Create a new rate limit object, this can be used to enforce maximum rates of change in a set of values, these
        are generally expressed in rate per second, but could use any arbitrary function. For a default application the
        provided function which can handle rate per second should be sufficient, but the ability to provide a custom
        function allows for e.g. permitting larger rates when decreasing. This can be used in conjunction with the motor
        power functions to provide a degree of traction control (we can't actually detect slipping in wheels, we just
        don't have sufficient information), by limiting the maximum requested power rate change over time.

        :param limit_function:
            A function of old_value * old_time * new_value * new_time which will return a potentially limited new value
            given a requested value, historical value and timepoints for both.
        """
        self.previous_values = None
        self.previous_time = None
        self.limit_function = limit_function

    def limit_and_return(self, values):
        """
        Take a list of values, update the internal state of the RateLimit and return a modified list of values which are
        restricted by the configured limit function.

        :param float[] values:
            Values to attempt to apply
        :return:
            New values to apply, modified by the configured limit function
        """
        now = time_now()
        if self.previous_time is None:
            self.previous_time = now
            self.previous_values = values
            return values
        updated_values = [self.limit_function(previous_value, self.previous_time, value, now) for
                          (previous_value, value) in
                          zip(self.previous_values, values)]
        self.previous_values = updated_values
        self.previous_time = now
        return updated_values

    @staticmethod
    def fixed_rate_limit_function(rate_per_second):
        """
        Create and return a new limit function which will lock the maximum delta applied to the specified rate per
        second.

        :param float rate_per_second:
            Largest allowed delta per second
        :return:
            A function which can be used in the :class:`triangula.dynamics.RateLimit` constructor and which will enforce
            a fixed maximum absolute rate of change across successive values such that no value in the supplied vector
            will vary at a higher rate than provided.
        """

        def limit_function(previous_value, previous_time, new_value, new_time):
            time_delta = new_time - previous_time
            value_delta = abs(previous_value - new_value)
            requested_rate = value_delta / time_delta
            if requested_rate <= rate_per_second:
                return new_value
            else:
                return previous_value + ((new_value - previous_value) * rate_per_second / requested_rate)

        return limit_function
