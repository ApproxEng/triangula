import triangula.arduino
import triangula.lcd
from time import sleep

arduino = triangula.arduino.Arduino(i2c_delay=0.002)
lcd = triangula.lcd.LCD()
lcd.cursor_off()
lcd.set_backlight(red=8, green=4, blue=4)

while True:
  (a,b,c) = arduino.get_encoder_values()
  lcd.set_text(row1='p={} y={}'.format(str(a).ljust(6),b), row2='g={} Enc.'.format(str(c).ljust(6)))
