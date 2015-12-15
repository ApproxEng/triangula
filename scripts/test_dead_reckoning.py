from euclid import Vector2, Point2
from triangula.chassis import get_regular_triangular_chassis, Motion, Pose

chassis = get_regular_triangular_chassis(
    wheel_distance=290,
    wheel_radius=60,
    max_rotations_per_second=1.0)

m1 = Motion(translation=Vector2(x=-26, y=152), rotation=0.2)
p = Pose(position=Point2(x=0, y=0), orientation=0)

print m1
print str(p.calculate_pose_change(motion=m1, time_delta=0.2))
