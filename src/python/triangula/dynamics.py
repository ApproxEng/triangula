from time import time as time_now


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
