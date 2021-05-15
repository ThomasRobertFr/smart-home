#include <Arduino.h>

int pinCalibrationLED = LED_BUILTIN;
int nbSensors = 1;
String sensorIds[1] = {"romarin"};
int pinSensors[1] = {D1}; // , D2, D3};
int pinMotors[1] = {D5}; // , D6, D7};
