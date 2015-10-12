import triangula.chassis
import triangula.arduino
import triangula.input
from euclid import Vector2, Point2

chassis = triangula.chassis.get_regular_triangular_chassis(
	wheel_distance=200, 
	wheel_radius=60,
	max_rotations_per_second=1.0)

max_trn = chassis.get_max_translation_speed()
max_rot = chassis.get_max_rotation_speed()

arduino = triangula.arduino.Arduino()

print (max_trn, max_rot)

with triangula.input.SixAxisResource() as joystick:
	while 1:
		translate = Vector2(
			joystick.axes[0].corrected_value(),
			joystick.axes[1].corrected_value()) * max_trn
		rotate = joystick.axes[2].corrected_value() * max_rot

		wheel_speeds = chassis.get_wheel_speeds(
			translation = translate,
			rotation = rotate,
			origin = Point2(0,0))

		speeds = wheel_speeds.speeds
		scaling = wheel_speeds.scaling

		print (scaling, speeds)

		arduino.set_motor_power(speeds[0], speeds[1], speeds[2])
