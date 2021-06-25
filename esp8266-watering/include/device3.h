#include <Arduino.h>

int pinCalibrationLED = LED_BUILTIN;
int nbSensors = 2;
String sensorIds[2] = {"misere", "cactusDeNoel"};
int pinSensors[3] = {D1, D2, D3};
int pinMotors[3] = {D5, D6, D7};
