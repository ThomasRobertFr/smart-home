#include <Arduino.h>

int pinCalibrationLED = LED_BUILTIN;
int nbSensors = 2;
String sensorIds[2] = {"misere", "cactusDeNoel"};
int pinSensors[2] = {D1, D2}; // {D1, D2, D3};
int pinMotors[2] = {LED_BUILTIN, LED_BUILTIN}; // {D5, D6, D7};
