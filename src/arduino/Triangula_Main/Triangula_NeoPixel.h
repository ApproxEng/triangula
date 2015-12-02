/*
  Triangula_NeoPixel.h - Library to control the NeoPixel LEDs on Triangula
  Created by Tom Oinn, December 2, 2015
  Apache Software License
*/
#ifndef Triangula_NeoPixel_h
#define Triangula_NeoPixel_h

#include <Adafruit_NeoPixel.h>

class Triangula_NeoPixel : public Adafruit_NeoPixel {
  public:
    Triangula_NeoPixel();
    uint32_t interpolate(uint32_t colour_a, uint32_t colour_b, float i);
    uint32_t hsvToColour(uint8_t h, uint8_t s, uint8_t v);
    void setCameraRing(uint8_t intensity);
    void setPylon(uint8_t pylonIndex, uint8_t saturation, uint8_t value, uint8_t hue_top, uint8_t hue_bottom, uint8_t mask);
  private:
    uint8_t Red(uint32_t colour);
    uint8_t Green(uint32_t colour);
    uint8_t Blue(uint32_t colour);
};

#endif

