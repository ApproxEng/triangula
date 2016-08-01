Kinematics - Maths
==================

This page collects the various bits of vector maths used by Triangula's chassis kinematics.

.. hint::

    This document contains derivations for the equations used by the chassis code. If you don't want to work through
    these you don't need to, just look for boxes like this one which contain the most important bits. You don't have
    to follow the maths here to use the code, but I've written it up anyway in the hope that it'll be of interest.

Motion at a point
-----------------

Given an overall :class:`triangula.chassis.Motion`, what is the velocity of a given point on the robot's chassis?
Calculating the velocity at each individual wheel is the first thing we need to do when working out how fast each wheel
must be rotated.

.. hint::

    Suppose we have a motion :math:`\vec{M}=\begin{pmatrix}m_x\\m_y\\m_\theta\end{pmatrix}` relative to the robot's
    centre.

    :math:`\theta` *in the above expression is rotation in radians per second, where positive values correspond to
    clockwise motion when viewed from above.*

    We wish to determine the velocity :math:`\vec{V}=\begin{pmatrix}d_x\\d_y\end{pmatrix}` for a wheel :math:`W`

    The wheel is located, relative to the robot's centre point, at location :math:`W=\begin{pmatrix}w_x&w_y\end{pmatrix}`.

As the robot is a rigid structure, when the motion is purely a translation (i.e. :math:`m_\theta=0`) all points on the
robot will have the same velocity. Further, as we know that rotation and translation are independent, even when the
rotation part is non-zero we can consider the two parts of the motion (rotation and translation) independently, just
adding on the translation vector at the end. So, all we really need to work on is the rotation.

At this point we could do a lot of relatively awkward trigonometry, but there's a simpler approach:

Speed
_____

We know how fast we're moving, because we know the number of radians per second and we know the radius of the circle
in which we're moving. As we know the circumference of the circle is :math:`2\times\pi\times r`, and we know that there are
:math:`2\times\pi` radians (remember we use radians as our angular measurement!) in a circle, we can calculate we're
moving at :math:`2\pi r\times\frac\theta{2\pi}=r\theta` where :math:`r` is the radius of the circle and :math:`\theta`
is the angular speed in radians per second.

We know :math:`\theta` directly as it's part of our motion vector :math:`\vec{M}`.

We can calculate :math:`r` because we know our wheel is at :math:`W` relative to our centre of rotation. We need what's
known as the magnitude, or length, of the vector from :math:`\begin{pmatrix}0&0\end{pmatrix}` to :math:`W`, and basic
geometry tells us that this quantity :math:`\left|W\right|=\sqrt{w_x^2+w_y^2}`

.. hint::

    Putting these together gives us the equation for the speed (note, not velocity, we haven't worked out direction yet!) at
    this particular wheel to be:

    .. math:: s=m_\theta\times\sqrt{w_x^2+w_y^2}

Direction
_________

We know what direction we're moving in. This is because we know where the centre of rotation is, and it's always the
case that when rotating around a point, the direction we move is perpendicular to the direction to the centre of
rotation. If this isn't immediately obvious, imagine there's a rigid rod attached to the ground at one end and you're
holding the other end. As one end of the rod is attached to the ground you're always going to move in a circle - you
obviously can't push in the direction the rod's oriented as that would need you to change the length of the rod (you
can't, it's rigid), so you can only move at right angles to that direction.

In the general case we can rotate a vector by multiplying it by a matrix, where the values in the matrix are functions
of the angle through which we want to rotate (in this case positive values of :math:`\theta` correspond to clockwise
rotation) - note that :math:`\theta` in this case is the angle through which we're rotating the vector, and is *not*
related to the :math:`m_\theta` part of the motion!

.. math::
    \begin{bmatrix}
    x' \\
    y' \\
    \end{bmatrix} = \begin{bmatrix}
    \cos \theta & \sin \theta \\
    -\sin \theta & \cos \theta \\
    \end{bmatrix}\begin{bmatrix}
    x \\
    y \\
    \end{bmatrix}

In this particular case we want to rotate by a right angle to get the vector perpendicular to the radius of our circle
and therefore parallel to its circumference. When :math:`\theta=\frac\pi2` all the values in the matrix above are either
zero, one or minus 1:

.. math::
    \begin{bmatrix}
    x' \\
    y' \\
    \end{bmatrix} = \begin{bmatrix}
    \cos \frac\pi2 & \sin \frac\pi2 \\
    -\sin \frac\pi2 & \cos \frac\pi2 \\
    \end{bmatrix}\begin{bmatrix}
    x \\
    y \\
    \end{bmatrix} = \begin{bmatrix}
    0 & 1 \\
    -1 & 0 \\
    \end{bmatrix}\begin{bmatrix}
    x \\
    y \\
    \end{bmatrix} = \begin{bmatrix}
    y \\
    -x \\
    \end{bmatrix}

.. hint::

    So, plugging :math:`W` into the above means our direction vector :math:`\vec{D}` is as follows:

    .. math::
        \vec{D} = \begin{pmatrix}
        w_y \\
        -w_x \\
        \end{pmatrix}


Velocity from Rotation
______________________

As we have a direction and a speed we can calculate the velocity. First though we need to calculate the unit vector for
the direction - this will give us a vector of magnitude 1, which we can simply multiply by our speed to get our
wheel velocity. The unit vector is calculated by dividing each part of the direction vector by the magnitude of the
vector, so:

.. math::
    \widehat D=\frac{\overrightarrow D}{\left|D\right|}

We know that the magnitude of a vector is the square root of the sum of the squares of its components, so we can work
out that the unit vector in this case is:

.. math::
    \widehat D=\frac{\overrightarrow D}{\sqrt{w_y^2+(-w_x)^2}}=\frac{\overrightarrow D}{\sqrt{w_x^2+w_y^2}}

To get our velocity we multiple the unit vector by the speed:

.. math::
    :nowrap:

    \begin{align}
        \vec{V_{wheelRotation}} &= \widehat D \times s \\
        &= \frac{\overrightarrow D}{\sqrt{w_x^2+w_y^2}} \times s \\
        &= \frac{\overrightarrow D}{\sqrt{w_x^2+w_y^2}} \times m_\theta\times\sqrt{w_x^2+w_y^2} \\
        &= {\overrightarrow D}m_\theta \\
    \end{align}

Now everything simplifies out! We're left with our wheel velocity being our direction vector multiplied by our angular
velocity in radians per second. To finish the job we drop in our definition for :math:`\overrightarrow D` to get:

.. hint::

    The velocity due to the rotation component of the motion at wheel :math:`W` is:

    .. math:: \vec{V_{wheelRotation}} &= \begin{pmatrix} w_y -w_x \end{pmatrix}m_\theta

Final Velocity
______________

.. hint::

    All our above calculations have only included the velocity from the rotation component of the motion. To include the
    translation component is easy though - we just add it on! Our final equation for the velocity of the wheel (or, more
    precisely, the velocity of the point at which the wheel makes contact with the ground) is therefore:

    .. math::

        \vec{V_{wheel}} = \begin{pmatrix}
        w_y \\
        -w_x \\
        \end{pmatrix}m_\theta + \begin{pmatrix}
        m_x \\
        m_y \\
        \end{pmatrix}

Wheel Speed for Velocity
------------------------

Triangula uses omni-wheels. Once we know from the above maths exactly what velocity is needed at each wheel position for
a given desired motion we need to calculate the wheel speed in radians per second for each wheel. This is then passed on
to the motor controllers to drive the robot.

.. hint::

    Fistly we need a way to define the wheels. As used above, each wheel is located relative to the centre of the robot
    with a position vector, :math:`\vec{W}`.

    In addition to its position, we need to know two more things.

    1. We need to know in what direction the wheel is pointing.
    2. We need to know how big the wheel is, because a large wheel will require a smaller number of rotations or radians
       per second to achieve the same speed across the ground.

    We can model these pieces of information as a single wheel drive vector, :math:`\vec{WD}`, representing the
    direction and distance a regular wheel would roll in a single revolution.

Triangula's :class:`triangula.chassis.HoloChassis.OmniWheel` class contains the necessary logic to store the drive
vector and to calculate it from other information such as wheel radius and angle (this may be more convenient when you
need to specify your wheels). The maths, however, works on the drive vector as it's simpler to deal with.

As we are using omni-wheels, any wheel on Triangula's chassis can move in any direction. We know this by observation,
but mathematically we know that we can drive the wheel along its drive vector :math:`\vec{WD}`, and that the wheel can
also freely roll at right angles to this vector. We cannot control or measure the degree of movement at right angles to
our drive vector, so we can safely disregard it. All we care about is motion in the direction of the drive vector, and
we can obtain this by projecting the velocity onto the drive vector, using the formula:

.. math:: p=\frac{\overrightarrow{V_{wheel}}\cdot\overrightarrow{WD}}{\left|WD\right|}

For those not familiar with vector maths, the expression :math:`\vec{A}\cdot\vec{B}` sums the products of each component
of each vector. In other words:

.. math::

    \overrightarrow A\cdot\overrightarrow B=\begin{pmatrix}a_x\\a_y\end{pmatrix}
    \cdot\begin{pmatrix}b_x\\b_y\end{pmatrix}=a_x\times b_x+a_y\times b_y

So what are we doing when we project one vector onto another one? We're working in a two-dimensional plane, in which any
point can be defined by two coordinates. Typically we use x and y coordinates, something you'll have encountered
hundreds of times before in grids, maps, chess boards etc. What we actually mean when we use these though is slightly
more subtle - we can think of both x and y as vectors themselves, which, when added together in the appropriate
quantities, can be used to reach any point on the plane. So, our :math:`\vec{x}` represents a single unit movement along
the x axis, and the :math:`\vec{y}` the same distance along the y axis. Starting from the origin, we can express any
point on the plane as a motion involving a certain amount of :math:`\vec{x}` and a certain amount of :math:`\vec{y}`.

The projection operation can be read as *how much of unit vectors* :math:`\vec{x}` *and* :math:`\vec{y}` *do we need to add
together to get a particular vector* :math:`\vec{V}` *?* We project our target vector onto our basis vectors (those used
to represent the coordinate system) and read off the projection, which we can then use as a coordinate in that basis
vector's axis. When done with our regular x and y axes the results are exactly what you'd expect, the projection of
a vector :math:`\begin{pmatrix}V_x\\V_y\end{pmatrix}` onto :math:`\vec{x}` is :math:`V_x` and onto :math:`\vec{y}`
is :math:`V_y`.

Using vectors which correspond to the x and y axes is very convenient and easy to understand, but if all we want is a
pair of vectors which can, between them, reach every point on the plane, we don't actually have to use those particular
ones. In fact, all that's required is **any** pair of vectors that are not co-incident, that is to say one is not a
multiple of the other one.

Now, we know that our wheels have to have a velocity given by :math:`\vec{V_{wheel}}`, and we know we have a drive
vector :math:`\vec{WD}` and another vector which we haven't bothered naming which is non-coincident to the drive vector
in which the wheels can slide. What we want to know is how far we have to move per second in the direction of the drive
vector such that in combination with an unknown amount of movement orthogonal to this (the sliding vector) we end up
with the target wheel velocity.

So, we know that we need :math:`p` multiples of :math:`\widehat{WD}` to move as defined by :math:`\vec{V_{wheel}}`,
where :math:`p` is defined as :

.. math:: p=\frac{\overrightarrow{V_{wheel}}\cdot\overrightarrow{WD}}{\left|WD\right|}

.. hint::

    Now we know we need to move :math:`p` units of distance, to get the wheel speed in revolutions per second we simply
    divide by the distance travelled per revolution. As we already defined the drive vector to be the translation vector
    for a single revolution of the wheel we divide by :math:`{\left|WD\right|}` again, to give wheel speed :math:`s` (as
    revolutions per second) as :

    .. math:: s=\frac{\overrightarrow{V_{wheel}}\cdot\overrightarrow{WD}}{\left|WD\right|^2}

Wheel Speed from Motion
-----------------------

Combining the two sections above we can calculate the necessary speed for any wheel on the chassis for any target motion
for the robot as a whole.

.. hint::

    Given a wheel, with location relative to the origin of the chassis specified by :math:`\vec{W}` and drive vector :math:`\vec{WD}`,
    defined as the vector described by the wheel hub after one revolution of the wheel, and a target motion vector
    :math:`M` consisting of :math:`m_x` and :math:`m_y` linear velocities and angular velocity :math:`m_\theta`, we can calculate the speed
    at which the wheel will need to be driven, in revolutions per second, as:

    .. math::
        :nowrap:

        \begin{align}
            s & = \frac{(\begin{pmatrix} w_y \\ -w_x \\ \end{pmatrix}m_\theta + \begin{pmatrix} m_x \\ m_y \\
            \end{pmatrix})\cdot\overrightarrow{WD}}{\left|WD\right|^2} \\
            & \\
            & = \frac{\begin{pmatrix}w_ym_\theta+m_x\\-w_xm_\theta+m_y\end{pmatrix}
            \cdot\begin{pmatrix}wd_x\\{\mathrm{wd}}_y\end{pmatrix}}{wd_x^2+wd_y^2} \\
            & \\
            & = \frac{w_ym_\theta wd_x+m_xwd_x-w_xm_\theta wd_y+m_ywd_y}{wd_x^2+wd_y^2} \\
            & \\
            & = \frac{m_xwd_x+m_ywd_y+m_\theta(w_ywd_x-w_xwd_y)}{wd_x^2+wd_y^2}
        \end{align}

The most striking thing about the above equation is that wheel speed is a linear function of the components of the
motion vector. Unless the chassis changes over time, the coefficients of :math:`m_x`, :math:`m_y` and :math:`m_\theta`
are constant, and can be pre-computed. A seemingly complex problem is therefore extremely simple to actually implement.

Triangula's code is actually somewhat more complex, largely because in the sections above we have assumed that we are
always rotating around the origin of the robot's coordinate system. This assumption simplifies the maths, and allows for
the surprisingly simple expression above, but in reality we occasionally want to specify rotation around a different
point. For example. if carrying some kind of gripper we might want to always rotate around the gripper. In these cases
the effective geometry does change, as the vectors describing the wheel locations are in fact relative to the centre of
rotation under consideration rather than always being locked to the origin. This isn't, however, much of an extra
complication and if you've understood everything to this point you should be able to understand how the code works! The
only real difference is that the code doesn't reduce the equations down quite as much before running them.

Motion from Wheel Speeds
------------------------

Everything up to this point has focused on calculating wheel speeds for a given motion, but it is possible to go in the
other direction and to calculate motion from observed wheel speeds. Note that we can only do this because we have at
least as many wheels as we have dimensions in the motion vector (3 in this case). Also note that if our chassis had more
than 3 wheels we would never have a precise solution - in effect each wheel contributes an equation in a system of
linear simultaneous equations, so when we're solving for 3 unknowns and have 3 equations we'll (almost) always have a
single well-formed unique solution, but the moment we add in more equations, especially given our measurements will by
definition contain errors, we are very unlikely to ever have a perfect match and must use numerical methods to find the
best approximation. Triangula doesn't have this problem as she has 3 wheels, but were you to use this document to build
something with, say, 5 wheels you'd need to consider this issue.

Because we can arbitrarily define the centre point for our motion we can set it to the origin of the robot's coordinate
space for convenience. This in turn means we *can* use the simplest form of the equations above, and that we can
pre-compute the coefficients for each wheel. In fact, the code does exactly this - these lines in the init function
for :class:`triangula.chassis.HoloChassis.OmniWheel` should look familiar if you've just read the maths in the previous
sections:

.. code-block:: python

    self.co_x = self.vector.x / self.vector_magnitude_squared
    self.co_y = self.vector.y / self.vector_magnitude_squared
    self.co_theta = (self.vector.x * self.position.y -
                     self.vector.y * self.position.x) / self.vector_magnitude_squared

Now rather than using :math:`m_x`, :math:`m_y` and :math:`m_\theta` to find a set of wheel speeds, we need to use a set
of wheel speeds, one for each wheel to find :math:`m_x`, :math:`m_y` and :math:`m_\theta`.

To prevent things getting out of hand in terms of size let's set up some new terms. For a wheel
:math:`w_{n\;\in1,2,3...}` with speed :math:`s_n` we can pre-compute three coefficients.

.. hint::

    .. math::
        :nowrap:

        \begin{align}
            x_n & = \frac{wd_x}{wd_x^2+wd_y^2} \\
            & \\
            y_n & = \frac{wd_y}{wd_x^2+wd_y^2} \\
            & \\
            \theta_n & = \frac{w_ywd_x-w_xwd_y}{wd_x^2+wd_y^2}
        \end{align}

This allows us to concisely state three (in this case) simultaneous linear equations:

.. math::
    :nowrap:

    \begin{align}
    s_1 & = x_1m_x+y_1m_y+\theta_1m_\theta \\
    s_2 & = x_2m_x+y_2m_y+\theta_2m_\theta \\
    s_3 & = x_3m_x+y_3m_y+\theta_3m_\theta \\
    \end{align}


.. hint::

    As with any system of such equations we can express this in the form of a matrix:

    .. math:: \begin{bmatrix}x_1&y_1&\theta_1\\x_2&y_2&\theta_2\\x_3&y_3&\theta_3\end{bmatrix}\begin{bmatrix}m_x\\m_y\\m_\theta\end{bmatrix}=\begin{bmatrix}s_1\\s_2\\s_3\end{bmatrix}

    This is then amenable to numeric solving, in Triangula's case we use the NumPy library, which also includes
    functions to handle the case where we have more wheels than 3, although obviously in this particular instance we
    don't need to worry (Triangula is smart and fast, but she's thus far been incapable of spontaneously growing wheels).