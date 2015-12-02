#include "Triangula_NeoPixel.h"

// Three 8 pixel rods and a 24 pixel ring around the camera
#define LED_COUNT 48
// Connected to arduino pin 6
#define LED_PIN   6

Triangula_NeoPixel::Triangula_NeoPixel():
  Adafruit_NeoPixel(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800) {
};

// Returns the Red component of a 32-bit colour
uint8_t Triangula_NeoPixel::Red(uint32_t colour) {
  return (colour >> 16) & 0xFF;
};

// Returns the Green component of a 32-bit colour
uint8_t Triangula_NeoPixel::Green(uint32_t colour) {
  return (colour >> 8) & 0xFF;
};

// Returns the Blue component of a 32-bit colour
uint8_t Triangula_NeoPixel::Blue(uint32_t colour) {
  return colour & 0xFF;
};

// Interpolate two 32-bit colours
uint32_t Triangula_NeoPixel::interpolate(uint32_t colour_a, uint32_t colour_b, float i) {
  if (i < 0.0 || i > 1.0) {
    i = 0.0;
  }
  float j = 1.0 - i;
  return Color(Red(colour_a) * j + Red(colour_b) * i,
               Green(colour_a) * j + Green(colour_b) * i,
               Blue(colour_a) * j + Blue(colour_b) * i);
};

// Get a 32-bit colour from a triple of hue, saturation and value
uint32_t Triangula_NeoPixel::hsvToColour(uint8_t h, uint8_t s, uint8_t v) {
  unsigned char region, remainder, p, q, t;
  h = (h + 256) % 256;
  if (s > 255) s = 255;
  if (v > 255) v = 255;
  else v = (v * v) >> 8;
  if (s == 0) return Color(v, v, v);
  region = h / 43;
  remainder = (h - (region * 43)) * 6;
  p = (v * (255 - s)) >> 8;
  q = (v * (255 - ((s * remainder) >> 8))) >> 8;
  t = (v * (255 - ((s * (255 - remainder)) >> 8))) >> 8;
  switch (region) {
    case 0:
      return Color(v, p, t);
    case 1:
      return Color(q, p, v);
    case 2:
      return Color(p, t, v);
    case 3:
      return Color(p, v, q);
    case 4:
      return Color(t, v, p);
  }
  return Color(v, q, p);
};

void Triangula_NeoPixel::setCameraRing(uint8_t intensity) {
};

void Triangula_NeoPixel::setPylon(uint8_t pylonIndex, uint8_t saturation, uint8_t value, uint8_t hue_top, uint8_t hue_bottom, uint8_t mask) {
};

void Triangula_NeoPixel::setSolidColour(uint8_t hue, uint8_t saturation, uint8_t value) {
  uint32_t colour = this->hsvToColour(hue, saturation, value);
  for (int i = 0; i < LED_COUNT; i++) {
    this->setPixelColor(i, colour);
  }
};

