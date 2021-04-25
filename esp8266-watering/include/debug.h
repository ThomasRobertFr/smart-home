#include <Arduino.h>

int pinCalibrationLED = LED_BUILTIN;
int nbSensors = 3;
String sensorIds[3] = {"debug1", "debug2", "debug3"};
int pinSensors[3] = {D1, D2, D3};
int pinMotors[3] = {LED_BUILTIN, LED_BUILTIN, LED_BUILTIN};
