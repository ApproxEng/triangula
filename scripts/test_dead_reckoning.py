from math import radians, pi, sqrt

from euclid import Vector2, Point2
from triangula_unit.chassis import get_regular_triangular_chassis, Motion, Pose, rotate_vector

chassis = get_regular_triangular_chassis(
    wheel_distance=290,
    wheel_radius=60,
    max_rotations_per_second=1.0)


def check(motion, time_delta, target_pose):
    for translation in [Vector2(x * 10, y * 10) for x in range(0, 6) for y in range(0, 6)]:
        final_pose = Pose().translate(translation).calculate_pose_change(motion=motion, time_delta=time_delta)
        translated_target = target_pose.translate(translation)
        try:
            assert final_pose.is_close_to(translated_target)
        except AssertionError as e:
            print 'Failed: {} not {}, translation {}, motion {}, time_delta {}'.format(final_pose, translated_target,
                                                                                       translation, motion, time_delta)
            raise e


check(Motion(translation=rotate_vector(Vector2(0, -100 * pi / 2), radians(45)), rotation=radians(90)),
      1.0,
      Pose(position=Point2(-sqrt(2) * 100, 0), orientation=radians(90)))

check(Motion(rotation=radians(30)),
      0.5,
      Pose(orientation=radians(15)))

check(Motion(translation=Vector2(0, 100 * pi / 2), rotation=radians(90)),
      1.0,
      Pose(position=Point2(100, 100), orientation=radians(90)))

check(Motion(translation=Vector2(0, 100 * pi / 2), rotation=radians(90)),
      2.0,
      Pose(position=Point2(200, 0), orientation=radians(180)))

check(Motion(translation=Vector2(0, 100 * pi / 2), rotation=radians(-90)),
      2.0,
      Pose(position=Point2(-200, 0), orientation=radians(180)))

check(Motion(translation=Vector2(0, 100 * pi), rotation=radians(180)),
      0.5,
      Pose(position=Point2(100, 100), orientation=radians(90)))

check(Motion(translation=Vector2(100, 100), rotation=0),
      0.5,
      Pose(position=Point2(50, 50), orientation=0))
