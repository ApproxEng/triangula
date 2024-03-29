from time import time, sleep as time_sleep


class IntervalCheck:
    """
    Utility class which can be used to run code within a polling loop at most once per n seconds. Set up an instance
    of this class with the minimum delay between invocations then enclose the guarded code in a construct such as
    if interval.should_run(): - this will manage the scheduling and ensure that the inner code will only be called if
    at least the specified amount of time has elapsed.

    This class is particularly used to manage hardware where we may wish to include a hardware read or write in a fast
    polling loop such as the task manager, but where the hardware itself cannot usefully be written or read at that
    high rate.

    Instances of this class can also be used in 'with' clauses, i.e. 'with interval:' - this will sleep if required
    before running the gated code, then set the last run time to be the current time. This is not quite the same as
    just calling sleep() before running a code block, as it resets the time after the code has run, instead of after
    the sleep call has completed. Used in this mode therefore the interval is from the end of one code block to the
    start of the next, whereas normally it is from the start of one code block to the start of the next.
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
        """
        Determines whether the necessary interval has elapsed. If it has, this returns True and updates the internal
        record of the last runtime to be 'now'. If the necessary time has not elapsed this returns False
        """
        now = time()
        if self.last_time is None or now - self.last_time > self.interval:
            self.last_time = now
            return True
        else:
            return False

    def sleep(self):
        """
        Sleep, if necessary, until the minimum interval has elapsed. If the last run time is not set this function will
        set it as a side effect, but will not sleep in this case. Calling sleep() repeatedly will therefore not sleep
        on the first invocation but will subsequently do so each time.
        """
        now = time()
        if self.last_time is None:
            self.last_time = now
            return
        elif now - self.last_time > self.interval:
            return
        else:
            remaining_interval = self.interval - (now - self.last_time)
            time_sleep(remaining_interval)
            self.last_time = now + remaining_interval

    def __enter__(self):
        self.sleep()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.last_time = time()
