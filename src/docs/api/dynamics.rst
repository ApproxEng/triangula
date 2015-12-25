triangula.dynamics: High Level Dynamics
=======================================

This package contains classes used to enforce higher level dynamics such as skid control, waypoint based navigation,
route planning and similar.

Acceleration limiting
---------------------

The :class:`triangula.dynamics.RateLimit` class is a general rate limiter. Constructed with a limit function, it is
called repeatedly, passed a list of new values. It enforces any supplied limits on the allowable rates of change of
these values and returns a modified set with the limits applied. This can be used, for example, in the manual control
task to prevent the requested motor powers changing at too high a rate, providing a simple form of skid control at the
expense of responsiveness.

The limit function takes a previous value with associated timepoint, and a new value and new timepoint, and returns a
potentially limited version of the new value. The simple static function generator within this class will enforce fixed
rate per second limiting, but other functions could be passed in to provide smarter logic such as always allowing a
reduction in the absolute value but limiting increases in magnitude.

.. autoclass:: triangula.dynamics.RateLimit
    :members:
