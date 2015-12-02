
/**
   Simple sketch to directly control the Syren drivers. Send an I2C message containing 3 bytes, one
   for each motor, these are converted to values in the range -128 to 127 and sent to the motor drivers
*/
#include <Adafruit_NeoPixel.h>
#include "Triangula_NeoPixel.h"
#include <Wire.h>
#include <Sabertooth.h>

#define SLAVE_ADDRESS  0x70

#define MOTOR_SPEED_SET 0x20
#define SET_SOLID_COLOUR 0x21
#define ENCODER_READ 0x22

#define REG_MAP_SIZE   6
#define MAX_SENT_BYTES 4

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

byte registerMap[REG_MAP_SIZE];
byte receivedCommands[MAX_SENT_BYTES];
volatile boolean newDataAvailable = false;

// Motor drivers, must be configured in packet serial mode with addresses 128, 129 and 130
Sabertooth ST[3] = { Sabertooth(128), Sabertooth(129), Sabertooth(130) };
// Lights
Triangula_NeoPixel pixels = Triangula_NeoPixel();

void setup() {
  pixels.begin();
  Serial.begin(9600);
  Wire.begin(SLAVE_ADDRESS);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);
  // Start up connection to Syren motor controllers, setting baud rate
  // then waiting two seconds to allow the drivers to power up and sending
  // the auto-calibration signal to all controllers on the same bus
  //SabertoothTXPinSerial.begin(9600);
  //Sabertooth::autobaud(SabertoothTXPinSerial);
  // Stop interrupts
  cli();
  // Configure port 0, pins 8-13, as inputs
  // Note - this requires a 10k pullup between 5V and pin 13
  for (int pin = 8; pin <= 13; pin++) {
    pinMode(pin, INPUT);
    digitalWrite(pin, HIGH);
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

  //for (int i = 0; i < 3; i++) {
  //  ST[i].motor(0);
  //}
  pixels.setSolidColour(170, 255, 60);
  pixels.show();
}

void loop() {
  if (newDataAvailable) {
    newDataAvailable = false;
    uint8_t i2c_command = receivedCommands[0];
    switch (i2c_command) {
      case MOTOR_SPEED_SET:
        for (int i = 1; i < MAX_SENT_BYTES; i++) {
          registerMap[i - 1] = receivedCommands[i];
        }
        for (int i = 0; i < 3; i++) {
          ST[i].motor(((int)(receivedCommands[i + 1])) - 128);
        }
        setColours(registerMap, REG_MAP_SIZE, 8, 0);
        break;
      case SET_SOLID_COLOUR:
        pixels.setSolidColour(receivedCommands[1], receivedCommands[2], receivedCommands[3]);
        pixels.show();
        break;
      case ENCODER_READ:
        pixels.setSolidColour(80, 255, 50);
        pixels.show();
        break;
      default:
        // Unknown command, stop the motors.
        for (int i = 0; i < 3; i++) {
          ST[i].motor(0);
        }
        pixels.setSolidColour(0, 255, 50);
        pixels.show();
        break;
    }
  }
}

// Called on I2C data request
void requestEvent() {
  byte data[] = {(byte)((pos_a & 0xff00) >> 8),
                    (byte)(pos_a & 0xff),
                    (byte)((pos_b & 0xff00) >> 8),
                    (byte)(pos_b & 0xff),
                    (byte)((pos_c & 0xff00) >> 8),
                    (byte)(pos_c & 0xff)
                   };
  Serial.println("a");
  Serial.println(data[0]);
  Serial.println("b");

  Serial.println(data[1]);
  Serial.println("c");

  Serial.println(data[2]);

  Serial.println("d");
  Serial.println(data[3]);
  Serial.println("e");
  Serial.println(data[4]);

  Serial.println("f");
  Serial.println(data[5]);
  Serial.println(Wire.write(data,6));

}

// Called on I2C data reception
void receiveEvent(int bytesReceived) {
  for (int a = 0; a < bytesReceived; a++) {
    if (a < MAX_SENT_BYTES) {
      receivedCommands[a] = Wire.read();
    }
    else {
      Wire.read();  // if we receive more data then allowed just throw it away
    }
  }
  newDataAvailable = true;
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

/*
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

/*
  Handle timer interrupt
  Each tick we stash the current value of the absolute position for each encoder, then walk
  back in time in the buffer until we have at least a certain magnitude delta, at which point
  we set the velocity value for that encoder to be the difference divided by the number of
  steps back in time. The length of the buffer and the frequency of the timer along with the
  minimum delta define the precision and latency of the velocity detection.
*/
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

// Set colours based on the signal received from the Pi
void setColours(byte hues[], int hueCount, int pixelsPerValue, int fromPixel) {
  int pixel = fromPixel;
  for (int i = 0; i < hueCount; i++) {
    uint32_t colour_a = pixels.hsvToColour(hues[i], 255, 150);
    uint32_t colour_b = pixels.hsvToColour(hues[(i + 1) % hueCount], 255, 150);
    for (int j = 0; j < pixelsPerValue; j++) {
      uint32_t colour = pixels.interpolate(colour_a, colour_b, ((float)j) / ((float)pixelsPerValue));
      pixels.setPixelColor(pixel++, colour);
    }
  }
  pixels.show();
}

