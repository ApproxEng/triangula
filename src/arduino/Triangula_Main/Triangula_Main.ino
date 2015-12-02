
/**
 * Simple sketch to directly control the Syren drivers. Send an I2C message containing 3 bytes, one
 * for each motor, these are converted to values in the range -128 to 127 and sent to the motor drivers
 */
#include <Adafruit_NeoPixel.h>
#include "Triangula_NeoPixel.h"
#include <Wire.h>
#include <Sabertooth.h>

#define SLAVE_ADDRESS  0x70
#define REG_MAP_SIZE   3
#define MAX_SENT_BYTES 4

byte registerMap[REG_MAP_SIZE];
byte receivedCommands[MAX_SENT_BYTES];
volatile boolean newDataAvailable = false;

// Motor drivers, must be configured in packet serial mode with addresses 128, 129 and 130
Sabertooth ST[3] = { Sabertooth(128), Sabertooth(129), Sabertooth(130) };
// Lights
Triangula_NeoPixel pixels = Triangula_NeoPixel();

void setup() {
  pixels.begin();
  Serial.begin(57600);
  Wire.begin(SLAVE_ADDRESS);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);
  // Start up connection to Syren motor controllers, setting baud rate
  // then waiting two seconds to allow the drivers to power up and sending
  // the auto-calibration signal to all controllers on the same bus
  SabertoothTXPinSerial.begin(9600);
  Sabertooth::autobaud(SabertoothTXPinSerial);
}

void requestEvent() {
  Wire.write(registerMap, REG_MAP_SIZE);  //Set the buffer up to send all 14 bytes of data
}

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

void loop() {
  if (newDataAvailable) {
    newDataAvailable = false;
    for (int i = 1; i < MAX_SENT_BYTES; i++) {
      registerMap[i - 1] = receivedCommands[i];
    }
    for (int i = 0; i < 3; i++) {
      ST[i].motor(((int)(registerMap[i])) - 128);
    }
    setColours(registerMap, REG_MAP_SIZE, 8, 0);
  }
}

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

