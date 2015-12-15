triangula.chassis: Kinematics
=============================

The triangula.chassis module handles kinematics, that is the way in which the motors and the chassis dimensions interact
to produce motion, and how we can use sensors on the motors to infer changes in the robot's position. There are two
kinds of kinematics:

Forward Kinematics
    Given a set of motor speeds and the properties of the chassis, what movement are we performing?

Reverse Kinematics
    Given a target movement, what do we need to do with the motors to perform that movement?

Basics
------

Before we can do anything clever we have to define two concepts:

Pose
    The position of the robot. This consists of the location on a 2-dimensional plane of the robot's centre point, and
    an orientation. The coordinates here are in 'world space', that is to say they're relative to some fixed point in
    the world in which the robot is moving. The :class:`triangula.chassis.Pose` class represents a pose.

Motion
    The robot's speed both in translation (a 2-dimensional vector representing movement across the plane) and rotation
    (around a centre point). These are expressed in 'robot space', so all motions are relative to the robot's chassis.
    This means that a motion with a translation component of ``[0,1]`` is always 'forwards' as far as the robot is
    concerned. The :class:`triangula.chassis.Motion` class represents a motion.

Because this library is dealing with small scale robots, I use millimetres as my distance dimension. This isn't actually
codified anywhere, so as long as you're entirely consistent you could use metres, yards, furlongs or whatever, it only
matters that you always use the same unit whenever either distance or speed is required.

Angular units, rotation speeds and orientations, are **always** in radians. This is extremely important, if you find
radians hard to grapple with you can use the functions 'math.radians' and 'math.degrees' to convert degrees to radians
and radians to degrees respectively.

Time units are always seconds, although again you could use something different as long as you're entirely consistent.
This applies to time and, consequently, speeds and velocities.

.. autoclass:: triangula.chassis.Pose
    :members:

.. autoclass:: triangula.chassis.Motion
    :members:

Defining the Chassis
--------------------

In order to perform any kinds of calculations we need to know about the geometry of the chassis. In Triangula's case her
chassis is a triangle with omni-wheels at each corner, perpendicular to the vertex normal vector, but the code in this
module is capable of handling any arbitrary combination of omni-wheel position, size, orientation etc.

The :class:`triangula.chassis.HoloChassis` class specifies a chassis defined as an arrangement of various size
omni-wheels. Wheels can be added to the chassis object with arbitrary orientation and position, and wheels of multiple
sizes can be specified. This class is then responsible for converting an arbitrary :class:`triangula.chassis.Motion` to
target speeds for each wheel expressed as revolutions per second. It can also perform the inverse mapping, taking a set
of wheel speeds and producing the inferred Motion.

.. autoclass:: triangula.chassis.HoloChassis
    :members:

When calculating the target wheel speeds for a given motion, it's possible that we simply can't perform the desired
motion. This typically happens because a requested wheel speed is impossibly high for one or more of the motors. If this
happens the entire motion will be scaled back such that the fastest wheel is moving at full speed. The
:class:`triangula.chassis.WheelSpeeds` class wraps up the speeds of each wheel in revolutions per second, and also any
scaling that has been applied to bring the motion into the range that's possible to actually perform.

.. autoclass:: triangula.chassis.WheelSpeeds
    :members:

Location Awareness
------------------

Triangula has hall effect encoders on all her wheels. This means we can track, with reasonable precision, the exact
movement of each wheel (although bear in mind we can't track whether those wheels are actually driving across the ground
rather than slipping). In a case where we have perfect traction we can therefore use these encoder values, or, more
accurately, changes in the encoder values, to compute the :class:`triangula.chassis.Motion` we're currently performing.

When we have a motion, and a time during which that motion applied, we can calculate the change in pose. For example,
if we know we're moving forwards at 10mm/s and that 1s has passed we can trivially move our current pose 10mm forwards.
For cases where we're also rotating (given Triangula's design this is pretty much all the time) the logic is more
complicated, the :class:`triangula.chassis.Pose` class contains a function ``calculate_pose_change`` which will handle
these cases, taking a motion and time delta and returning a new pose representing the pose after the motion has been
applied.

This logic is all wrapped up in the :class:`triangula.chassis.DeadReckoning` class:

.. autoclass:: triangula.chassis.DeadReckoning
    :members:

This class tracks the current best guess for the robot's pose, and can be updated with encoder values (in which case it
works out the derived motion and applies it over the time since the last update), or with explicit values for the pose
(this is useful when we want to reset the current pose, or when we have information from some absolute sensor such as
a compass).

Bear in mind that any dead-reckoning algorithm will inevitably accumulate errors over time. The degree to which this
happens is down to a number of properties of the chassis, the wheels, the encoders, the ground over which the robot is
moving, and many others. With good quality hardware, a rigid chassis, and, crucially, accurate dimensions, the accuracy
appears to be pretty good. Any errors in dimensions, or any loss of traction, will very rapidly introduce errors in the
estimated pose. It's good enough for three-point-turn challenges, probably not good enough to navigate to somewhere
hundreds of metres away, but the exact level of accuracy will depend on how you've built your robot!