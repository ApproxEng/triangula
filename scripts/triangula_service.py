"""
Triangula top level service script
"""

import triangula.arduino
import triangula.chassis
import triangula.imu
import triangula.input
import triangula.lcd
import triangula.util

# Construct a HoloChassis object to perform drive calculations, using the convenience
# method to build one with regular triangular geometry and identical wheels. The exact
# number of maximum rotations per second doesn't actually matter, as we're going to
# scale the output of the joystick such that we hit whatever this value is when at the
# extreme ranges of the stick.
chassis = triangula.chassis.get_regular_triangular_chassis(
    wheel_distance=200,
    wheel_radius=60,
    max_rotations_per_second=1.0)

# Maximum translation speed in mm/s
max_trn = chassis.get_max_translation_speed()
# Maximum rotation speed in radians/2
max_rot = chassis.get_max_rotation_speed()
# Show max speeds
print (max_trn, max_rot)

# Connect to the Arduino Nano over I2C, motors and lights are attached to the nano
arduino = triangula.arduino.Arduino()
arduino.set_lights(200, 255, 100)

# Hold whether we're navigating in relative or absolute terms, and what our correction is
state = {'bearing_zero': None,
         'last_bearing': 0.0}

# Start up the display, show the IP address
lcd = triangula.lcd.LCD()
lcd.set_text(row1='Triangula', row2=triangula.util.get_ip_address())

while 1:
    try:
        with triangula.input.SixAxisResource(bind_defaults=True) as joystick:
            lcd.set_text(row1='Triangula', row2='Controller found')
            arduino.set_lights(100,255,100)
    except IOError:
        lcd.set_text(row1='Waiting for ps3', row2='controller...')
