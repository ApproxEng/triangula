#include <Sabertooth.h>
#include <PID_v1.h>
#include <Wire.h>

/**
 * Firmware for the arduino running the encoder scanning. This consists of pin change interrupts to detect encoder value changes,
 * along with a timer interrupt to regularly read the encoder position and compute velocity for each wheel
 */

// PID controls, one for each encoder / wheel combination
// Cautious settings are used when wheel speed is close to the setpoint, aggressive ones for when
// we're further away.
const double aggressive_Kp = 4.0;
const double aggressive_Ki = 0.2;
const double aggressive_Kd = 1.0;
const double cautious_Kp = 1.0;
const double cautious_Ki = 0.05;
const double cautious_Kd = 0.25;
// Note - do not set this directly, it's set from the volatile value created by the encoders.
double input_a = 0.0d;
double setpoint_a = 0.0d;
double control_a = 0.0d;
PID pid_a = PID(&input_a, &control_a, &setpoint_a, cautious_Kp, cautious_Ki, cautious_Kd, DIRECT);
double input_b = 0.0d;
double setpoint_b = 0.0d;
double control_b = 0.0d;
PID pid_b = PID(&input_b, &control_b, &setpoint_b, cautious_Kp, cautious_Ki, cautious_Kd, DIRECT);
double input_c = 0.0d;
double setpoint_c = 0.0d;
double control_c = 0.0d;
PID pid_c = PID(&input_c, &control_c, &setpoint_c, cautious_Kp, cautious_Ki, cautious_Kd, DIRECT);

// Set frequency to poll encoder counts when calculating velocity. Higher values will cause faster
// updates but at the cost of potentially lower accuracy
const int velocityTimerHertz = 50;
// The length of the buffer into which we record encoder values. Longer tracks allow for greater
// precision at the cost of latency. The maximum latency, which will occur when speed drops to zero
// is the length of the track divided by the velocity timer frequency. When running at higher speeds
// the latency will be a single unit of the velocity timer frequency, the high levels of latency only
// apply to cases where we have very low values.
const byte trackLength = 16;
// The delta in readings to search for. The algorithm walks back in time along the track until it finds
// a delta between the current encoder value and the historic one of at least this magnitude. Higher
// values will result in more accuracy at the cost of higher latency as we have to track back further in
// time, more frequently, to obtain the result.
const int targetDelta = 50;

// Track absolute encoder values, these are unsigned ints and can (and will) roll over. The difference()
// function handles these cases properly. Note that these are volatile as they're updated on pin change
// interrupts, when reading them you should disable interrupts or risk reading half-way through an update.
volatile unsigned int pos_a = 0;
volatile unsigned int pos_b = 0;
volatile unsigned int pos_c = 0;

// Track encoder velocities, these are expressed as the number of encoder ticks (can be negative) per tick
// of the velocity timer. A full rotation of the output shaft of our motors is around a thousand ticks, as
// we have a 64 counts per revolution sensor and a reduction of 19:1, so the velocity in revolutions per
// second is given by this value * velocityTimerHertz / (19 * 64)
volatile double vel_a = 0.0d;
volatile double vel_b = 0.0d;
volatile double vel_c = 0.0d;

// Motor drivers, must be configured in packet serial mode with addresses 128, 129 and 130
Sabertooth ST[3] = { Sabertooth(128), Sabertooth(129), Sabertooth(130) };

// Monitor for the 3 quadrature encoders. Assumes that encoders are attached to pins 8+9, 10+11, 12+13
// for motors 0, 1 and 2 respectively. Important to match this with the motor driver addresses!
void setup() {
  // Stop interrupts
  cli();
  // Configure port 0, pins 8-13, as inputs
  // Note - this requires a 10k pullup between 5V and pin 13
  for (int pin = 8; pin <= 13; pin++) {
    pinMode(pin, INPUT);
    digitalWrite(pin, HIGH);
  }
  // Configure pins to disable motors! These pins need 10k pulldowns to ground or the entire
  // thing goes utterly mental when programming (as the drivers are connected to the TX on the
  // arduino's UART)
  for (int pin = 4; pin <= 6; pin++) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);
  }
  // Enable interrupts on port 0
  PCICR |= (1 << PCIE0);
  // Un-mask all pins
  PCMSK0 = 63;

  // Set timer 1 interrupt
  TCCR1A = 0;// set entire TCCR1A register to 0
  TCCR1B = 0;// same for TCCR1B
  TCNT1  = 0;//initialize counter value to 0
  // set compare match register for 50hz increments
  OCR1A = (15625 / velocityTimerHertz) - 1;// = (16*10^6) / (50*1024) - 1 (must be <65536)
  // turn on CTC mode
  TCCR1B |= (1 << WGM12);
  // Set CS10 and CS12 bits for 1024 prescaler
  TCCR1B |= (1 << CS12) | (1 << CS10);
  // enable timer compare interrupt
  TIMSK1 |= (1 << OCIE1A);

  // Enable interrupts
  sei();

  // Enable wire library to act as I2C slave with address 0x10
  Wire.begin(0x10);
  // Handle requests for data with wireRequest()
  Wire.onRequest(wireRequest);

  // Start up connection to Syren motor controllers, setting baud rate
  // then waiting two seconds to allow the drivers to power up and sending
  // the auto-calibration signal to all controllers on the same bus
  SabertoothTXPinSerial.begin(9600);
  Sabertooth::autobaud(SabertoothTXPinSerial);

  // Configure PID controllers with output range and enable them
  pid_a.SetOutputLimits(-127, 127);
  pid_b.SetOutputLimits(-127, 127);
  pid_c.SetOutputLimits(-127, 127);
  pid_a.SetMode(AUTOMATIC);
  pid_b.SetMode(AUTOMATIC);
  pid_c.SetMode(AUTOMATIC);


}

/**
 * Each time round the loop we update the PID controls, if active, then call their compute methods. If the compute methods
 * fire we set the motor speeds appropriately based on the PID output. Note that this will only take effect if the PIDs are
 * actually enabled, otherwise the loop will do nothing.
 */
void loop() {
  // Copy values to inputs for PIDs, disabling interrupts while we do it otherwise we risk
  // copying a volatile value half-way through its update.
  cli();
  input_a = vel_a;
  input_b = vel_b;
  input_c = vel_c;
  sei();

  if (abs(input_a - setpoint_a) < 5) {
    pid_a.SetTunings(cautious_Kp, cautious_Ki, cautious_Kd);
  }
  else {
    pid_a.SetTunings(aggressive_Kp, aggressive_Ki, aggressive_Kd);
  }
  if (abs(input_b - setpoint_b) < 5) {
    pid_b.SetTunings(cautious_Kp, cautious_Ki, cautious_Kd);
  }
  else {
    pid_b.SetTunings(aggressive_Kp, aggressive_Ki, aggressive_Kd);
  }
  if (abs(input_c - setpoint_c) < 5) {
    pid_c.SetTunings(cautious_Kp, cautious_Ki, cautious_Kd);
  }
  else {
    pid_c.SetTunings(aggressive_Kp, aggressive_Ki, aggressive_Kd);
  }

  if (pid_a.Compute()) {
    // Update control for A
    setMotorSpeed(0, control_a);
  }
  if (pid_b.Compute()) {
    // Update control for B
    setMotorSpeed(1, control_b);
  }
  if (pid_c.Compute()) {
    // Update control for C
    setMotorSpeed(2, control_c);
  }
}

void setMotorSpeed(byte motor, double motor_speed) {
  ST[motor].motor(motor_speed);
}


// Calculate the difference between two encoder readings, allowing for values which wrap. Will be positive
// if the second reading is larger than the first.
int difference(unsigned int a, unsigned int b) {
  int d = b - a;
  if (abs(d) > 0x7FFFu) {
    d = 0xFFFFu - (b + a);
  }
  return d;
}

// Handle request for encoder values over I2C
void wireRequest() {
  Wire.write(pos_a >> 8);
  Wire.write(pos_a);
  Wire.write(pos_b >> 8);
  Wire.write(pos_b);
  Wire.write(pos_c >> 8);
  Wire.write(pos_c);
}

/**
Sequence of pulses clockwise is 0,1,3,2

Assuming that the first state is the two LSB of a four bit value

So we have the following returning '1'
0->1 : 4
1->3 : 13
3->2 : 11
2->0 : 2
In the opposite direction we have 2,3,1,0
2->3 : 14
3->1 : 7
1->0 : 1
0->2 : 8
All other values should return 0 as they don't represent valid state transitions
*/
const int encoderValues[] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};

// Track previous encoder states
byte encoder_a;
byte encoder_b;
byte encoder_c;

// Handle pin change interrupts
ISR (PCINT0_vect) {
  byte last_read = PINB;
  byte a = (last_read & 48) >> 4;
  byte b = (last_read & 12) >> 2;
  byte c = last_read & 3;
  pos_a += encoderValues[a + (encoder_a << 2)];
  pos_b += encoderValues[b + (encoder_b << 2)];
  pos_c += encoderValues[c + (encoder_c << 2)];
  encoder_a = a;
  encoder_b = b;
  encoder_c = c;
}

// Where we currently are within the track
byte trackPos = 0;
// Track [trackLength] values of historic encoder positions
unsigned int track_a[trackLength];
unsigned int track_b[trackLength];
unsigned int track_c[trackLength];

// Handle timer interrupt
// Each tick we stash the current value of the absolute position for each encoder, then walk
// back in time in the buffer until we have at least a certain magnitude delta, at which point
// we set the velocity value for that encoder to be the difference divided by the number of
// steps back in time. The length of the buffer and the frequency of the timer along with the
// minimum delta define the precision and latency of the velocity detection.
ISR (TIMER1_COMPA_vect) {
  // Write current absolute encoder values into the track arrays
  track_a[trackPos] = pos_a;
  track_b[trackPos] = pos_b;
  track_c[trackPos] = pos_c;
  // Try to work out velocity based on track history
  vel_a = velocity(track_a);
  vel_b = velocity(track_b);
  vel_c = velocity(track_c);
  // Increment and wrap track position
  trackPos++;
  if (trackPos >= trackLength) {
    trackPos -= trackLength;
  }
}

double velocity(unsigned int track[]) {
  unsigned int current = track[trackPos];
  unsigned int past;
  double dif;
  for (int d = 1; d < trackLength; d++) {
    int pastIndex = trackPos - d;
    if (pastIndex < 0) {
      pastIndex += trackLength;
    }
    past = track[pastIndex];
    dif = difference(past, current);
    if (abs(dif) >= targetDelta) {
      return dif / (double)d;
    }
  }
  // Fallen off the end of the loop, return best guess
  return dif / (trackLength - 1);
}

