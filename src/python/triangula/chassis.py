from math import cos, sin, pi

from euclid import Vector2, Point2

__author__ = 'tom'


def test():
    chassis = HoloChassis(wheels=[
        HoloChassis.OmniWheel(position=Point2(1, 0), angle=0, radius=60),
        HoloChassis.OmniWheel(position=Point2(-1, 0), angle=0, radius=60)]
    )
    print chassis.get_wheel_speeds(translation=Vector2(0, 0), rotation=0.5)
    print chassis.get_wheel_speeds(translation=Vector2(0, 0), rotation=0.5, origin=Point2(1, 0))


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
            A sequence of floats defining the revolutions per second required to obtain the appropriate overall motion.
            The sequence contains one speed for each previously specified wheel, there is no limiting in operation so
            this can potentially return results which are not physically possible, a subsequent processing step may be
            required to detect this condition and either scale all motion back or revisit the motion plan to try to find
            a better target vector.
        """

        def velocity_at(point):
            """
            Compute the velocity as a Vector2 at the specified point given the enclosing translation and rotation values

            :param euclid.Point2 point:
                Point at which to calculate velocity
            :return:
                A :class:`euclid.Vector2` representing the velocity at the specified point in mm/s
            """
            d = point - origin
            return d.normalized().cross() * abs(d) * rotation + translation

        return list(wheel.speed(velocity_at(wheel.position)) for wheel in self.wheels)

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

        def __init__(self, position, angle=None, radius=None, vector=None):
            """
            Create a new omni-wheel object, specifying the position and either a direction vector directly or the angle
            in degrees clockwise from the position Y axis along with the radius of the wheel.

            :param euclid.Point2 position:
                The wheel's contact point with the surface, specified relative to the centre of the
                chassis. Units are millimetres.
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
            if angle is None and radius is None and vector is not None:
                #  Specify wheel based on direct vector """
                self.vector = vector
            elif angle is not None and radius is not None and vector is None:
                # Specify based on angle from positive Y axis and radius """
                circumference = 2 * pi * radius
                self.vector = Vector2(sin(angle) * circumference, cos(angle) * circumference)
            else:
                raise ValueError('Must specify exactly one of angle and radius or translation vector')

        def speed(self, velocity):
            """
            Given a velocity at a wheel contact point, calculate the speed in revolutions per second at which the wheel
            should be driven.

            :param euclid.Vector2 velocity:
                The velocity at the wheel's contact point with the surface
            :return:
                Target wheel speed in rotations per second to hit the desired vector at the contact point.
            """
            return velocity.dot(self.vector) / self.vector.magnitude_squared()
