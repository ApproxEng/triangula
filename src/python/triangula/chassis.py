from math import cos, sin, pi, radians

from euclid import Vector2, Point2

__author__ = 'tom'


def test():
    chassis = HoloChassis(wheels=[
        HoloChassis.OmniWheel(position=Point2(1, 0), angle=0, radius=60),
        HoloChassis.OmniWheel(position=Point2(-1, 0), angle=0, radius=60)]
    )
    print chassis.get_wheel_speeds(translation=Vector2(0, 0), rotation=0.5)
    print chassis.get_wheel_speeds(translation=Vector2(0, 0), rotation=0.5, origin=Point2(1, 0))


def rotate_point(point, angle, origin=None):
    """
    Rotate a Point2 around another Point2

    :param euclid.Point2 point:
        The point to rotate
    :param float angle:
        Angle in radians
    :param euclid.Point2 origin:
        Origin of the rotation, defaults to (0,0) if not specified
    :return:
        A new :class:`euclid.Point2` containing the rotated input point
    """
    if origin is None:
        origin = Point2(0, 0)
    s = sin(angle)
    c = cos(angle)
    return Point2(c * (point.x - origin.x) - s * (point.y - origin.y) + origin.x,
                  s * (point.x - origin.x) + c * (point.y - origin.y) + origin.y)


def rotate_vector(vector, angle, origin=None):
    """
    Rotate a :class:`euclid.Vector2` around a :class:`euclid.Point2`

    :param euclid.Point2 point:
        The point to rotate
    :param float angle:
        Angle in radians
    :param euclid.Point2 origin:
        Origin of the rotation, defaults to (0,0) if not specified
    :return:
        A new :class:`euclid.Point2` containing the rotated input point
    """
    if origin is None:
        origin = Point2(0, 0)
    s = sin(angle)
    c = cos(angle)
    return Vector2(c * (vector.x - origin.x) - s * (vector.y - origin.y) + origin.x,
                   s * (vector.x - origin.x) + c * (vector.y - origin.y) + origin.y)


def get_regular_triangular_chassis(wheel_distance, wheel_radius, max_rotations_per_second):
    """
    Build a HoloChassis object with three wheels, each identical in size and maximum speed. Each wheel is positioned
    at the corner of a regular triangle, and with direction perpendicular to the normal vector at that corner.

    :param wheel_distance:
        Distance in millimetres between the contact points of each pair of wheels (i.e. the length of each edge of the
        regular triangle)
    :param wheel_radius:
        Wheel radius in millimetres
    :param max_rotations_per_second:
        Maximum wheel speed in revolutions per second
    :return:
        An appropriately configured HoloChassis
    """
    point = Point2(0, cos(radians(30)) * wheel_distance / 2.0)
    vector = Vector2(2 * pi * wheel_radius, 0)

    wheel_a = HoloChassis.OmniWheel(
        position=point,
        vector=vector,
        max_speed=max_rotations_per_second)
    wheel_b = HoloChassis.OmniWheel(
        position=rotate_point(point, pi * 2 / 3),
        vector=rotate_vector(vector, pi * 2 / 3),
        max_speed=max_rotations_per_second)
    wheel_c = HoloChassis.OmniWheel(
        position=rotate_point(point, pi * 4 / 3),
        vector=rotate_vector(vector, pi * 4 / 3),
        max_speed=max_rotations_per_second)

    return HoloChassis(wheels=[wheel_a, wheel_b, wheel_c])


class WheelSpeeds:
    """
    A simple container to hold desired wheel speeds, and to indicate whether any speeds were scaled back due to
    impossibly high values.
    """

    def __init__(self, speeds, scaling):
        self.speeds = speeds
        self.scaling = scaling


class HoloChassis:
    """
    An assembly of wheels at various positions and angles, which can be driven independently to create a holonomic drive
    system. A holonomic system is one where number of degrees of freedom in the system is equal to the number of
    directly controllable degrees of freedom, so for a chassis intended to move in two dimensions the degrees of freedom
    are two axes of translation and one of rotation. For a full holonomic system we therefore need at least three wheels
    defined.
    """

    def __init__(self, wheels):
        """
        Create a new chassis, specifying a set of wheels.
        
        :param wheels:
            A sequence of :class:`triangula.chassis.HoloChassis.OmniWheel` objects defining the wheels for this chassis.
        """
        self.wheels = wheels

    def get_max_translation_speed(self):
        """
        Calculate the maximum translation speed, assuming all directions are equivalent and that there is no rotation
        component to the motion.

        :return:
            Maximum speed in millimetres per second as a float
        """
        unrealistic_speed = 10000.0
        scaling = self.get_wheel_speeds(translation=Vector2(0, unrealistic_speed), rotation=0).scaling
        return unrealistic_speed * scaling

    def get_max_rotation_speed(self):
        """
        Calculate the maximum rotation speed around the origin in radians per second, assuming no translation motion
        at the same time.

        :return:
            Maximum radians per second as a float
        """
        unrealistic_speed = 2 * pi * 100
        scaling = self.get_wheel_speeds(translation=Vector2(0, 0), rotation=unrealistic_speed).scaling
        return unrealistic_speed * scaling

    def get_wheel_speeds(self, translation, rotation, origin=Point2(x=0, y=0)):
        """
        Calculate speeds to drive each wheel in the chassis at to attain the specified rotation / translation 3-vector.

        :param euclid.Vector2 translation:
            Desired translation vector specified in millimetres per second.
        :param float rotation:
            Desired anguar velocity, specified in radians per second where positive values correspond to clockwise
            rotation of the chassis when viewed from above.
        :param euclid.Point2 origin:
            Optional, can define the centre of rotation to be something other than 0,0. Units are in millimetres.
            Defaults to rotating around x=0, y=0.
        :return:
            A :class:`triangula.chassis.WheelSpeeds` containing both the target wheel speeds and the scaling, if any,
            which was required to bring those speeds into the allowed range for all wheels. This prevents unexpected
            motion in cases where only a single wheel is being asked to turn too fast, in such cases all wheel speeds
            will be scaled back such that the highest is within the bounds allowed for that particular wheel. This
            can accommodate wheels with different top speeds.
        """

        def velocity_at(point):
            """
            Compute the velocity as a Vector2 at the specified point given the enclosing translation and rotation values

            Method: Normalise the vector from the origin to the point, then take the cross of itself to produce a unit
            vector with direction that of a rotation around the origin. Scale this by the distance from the origin and
            by the rotation in radians per second, then simply add the translation vector.

            :param euclid.Point2 point:
                Point at which to calculate velocity
            :return:
                A :class:`euclid.Vector2` representing the velocity at the specified point in mm/s
            """
            d = point - origin
            return d.normalized().cross() * abs(d) * rotation + translation

        wheel_speeds = list(wheel.speed(velocity_at(wheel.position)) for wheel in self.wheels)
        scale = 1.0
        for speed, wheel in zip(wheel_speeds, self.wheels):
            if wheel.max_speed is not None and abs(speed) > wheel.max_speed:
                wheel_scale = wheel.max_speed / abs(speed)
                scale = min(scale, wheel_scale)
        return WheelSpeeds(speeds=list(speed * scale for speed in wheel_speeds), scaling=scale)

    class OmniWheel:
        """
        Defines a single omni-wheel within a chassis assembly. Omni-wheels are wheels formed from rollers, where the
        motion of the roller is perpendicular to the motion of the primary wheel. This is distinct from a mechanum wheel
        where the rollers are at an angle (normally around 40-30 degrees) to the primary wheel. Omni-wheels must be
        positioned on the chassis with non-parallel unit vectors, mechanum wheels can in some cases be positioned with
        all unit vectors parallel.

        A wheel has a location relative to the chassis centre and a vector describing the direction of motion of the
        wheel when driven with a positive angular velocity. The location is specified in millimetres, and the magnitude
        of the wheel vector should be equal to the number of millimetres travelled in a single revolution. This allows
        for different sized wheels to be handled within the same chassis.
        """

        def __init__(self, position, max_speed=0, angle=None, radius=None, vector=None):
            """
            Create a new omni-wheel object, specifying the position and either a direction vector directly or the angle
            in degrees clockwise from the position Y axis along with the radius of the wheel.

            :param euclid.Point2 position:
                The wheel's contact point with the surface, specified relative to the centre of the
                chassis. Units are millimetres.
            :param float max_speed:
                The maximum number of revolutions per second allowed for this wheel. When calculating the wheel speeds
                required for a given trajectory this value is used to scale back all motion if any wheel would have to
                move at an impossible speed. If not specified this defaults to None, indicating that no speed limit
                should be placed on this wheel.
            :param angle:
                The angle, specified in radians from the positive Y axis where positive values are clockwise from this
                axis when viewed from above, of the direction of travel of the wheel when driven with a positive speed.
                If this value is specified then radius must also be specified and dx,dy left as None.
            :param radius:
                The radius in millimetres of the wheel, measuring from the centre to the contact point with the surface,
                this may be hard to determine for some wheels based on their geometry, particularly for wheels with
                cylindrical rollers, as the radius will vary. For these cases it may be worth directly measuring the
                circumference of the entire assembly and calculating radius rather than measuring directly. This is used
                to determine the magnitude of the direction vector. If this is not None then the angle must also be
                specified, and dx,dy left as None.
            :param euclid.Vector2 vector:
                2 dimensional vector defining the translation of the wheel's contact point after a full
                revolution of the wheel.
            """
            self.position = position
            self.max_speed = max_speed
            if angle is None and radius is None and vector is not None:
                #  Specify wheel based on direct vector """
                self.vector = vector
            elif angle is not None and radius is not None and vector is None:
                # Specify based on angle from positive Y axis and radius """
                circumference = 2 * pi * radius
                self.vector = Vector2(sin(angle) * circumference, cos(angle) * circumference)
            else:
                raise ValueError('Must specify exactly one of angle and radius or translation vector')
            self.vector_magnitude_squared = self.vector.magnitude_squared()

        def speed(self, velocity):
            """
            Given a velocity at a wheel contact point, calculate the speed in revolutions per second at which the wheel
            should be driven.

            Method: we want to find the projection of the velocity onto the vector representing the drive of this wheel.
            We store the vector representing a single revolution of travel as self.vector, so the projection onto this
            would be velocity.dot(self.vector / abs(self.vector)). However, we want revolutions per second, so we must
            then divide again by abs(self.vector), leading to
            velocity.dot(self.vector / abs(self.vector))/abs(self.vector). Because the definition of the dot product is
            the sum of x1*x2, y1*y2, ... any scalar applied to each x, y ... of a single vector can be moved outside
            the dot product, so we can simplify as velocity.dot(self.vector) / abs(self.vector)^2. As the magnitude of
            the vector is taken by sqrt(x^2+y^2) we can simply express this as (x^2+y^2), held in the convenient
            function magnitude_squared(). So our final simplified form is
            velocity.dot(self.vector) / self.vector.magnitude_squared(). For efficiency, and because self.vector doesn't
            change, we can pre-compute this.

            :param euclid.Vector2 velocity:
                The velocity at the wheel's contact point with the surface, expressed in mm/s
            :return:
                Target wheel speed in rotations per second to hit the desired vector at the contact point.
            """
            return velocity.dot(self.vector) / self.vector_magnitude_squared
