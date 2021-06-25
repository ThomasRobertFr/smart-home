#define ARDUINOJSON_USE_LONG_LONG 1
#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include "wifi_setup.h"
#include "device3.h"

struct SensorData {
    String id;
    String postJSON_calibrations = "[]";
    String postJSON_measures = "[]";
    int postJSON_watering = 0;

    int pinSensor = -1;
    int pinMotor;

    bool calibrate;
    bool watering;
    bool force_watering;

    unsigned long calibration_duration;
    int calibration_max;
    int calibration_min;

    uint64_t measure_interval;
    uint64_t watering_cooldown;

    unsigned long watering_cycle_duration;
    unsigned long watering_cycle_sleep;
    int watering_cycle_nb_max;
    int watering_humidity_target;
    int watering_humidity_threshold;
    uint64_t watering_last_delta;
};

const int jsonCapacity = JSON_OBJECT_SIZE(40);
const float motorPWM = 0.75;  // This powers motors with PWM to reduce apparent voltage of the battery, cf README
SensorData sensors[3] = {};

WiFiClient client;
HTTPClient http;

// HEADERS

void initSensors(bool http);
void deepSleep(uint64_t durationMin);
bool isDeepSleepWake();
void wifiConnect(uint64_t max_time_sec);
void httpGetSensor(String url, SensorData& sensor);
void httpPostJSON(String url, String &json);
void sensorsOff();
void sensorOn(SensorData &sensor);
int analogMeasure(short loop);
String calibration(SensorData &sensor);
int getHumidity(int humidity_raw, SensorData &sensor);
void watering(SensorData &sensor);

// DATA

void initSensors(bool http = true) {
    for (int i = 0; i < nbSensors; i++) {
        sensors[i].id = sensorIds[i];
        sensors[i].pinSensor = pinSensors[i];
        sensors[i].pinMotor = pinMotors[i];
        if (http)
            httpGetSensor(baseURL + sensors[i].id, sensors[i]);
    }
}

// SLEEP

void deepSleep(uint64_t durationMin = 10) {
    ESP.deepSleep(durationMin * 60 * 1000 * 1000);
    delay(1000);
}

bool isDeepSleepWake() {
    return ESP.getResetInfoPtr()->reason == REASON_DEEP_SLEEP_AWAKE;
}

// NETWORKING

uint32_t calculateCRC32(const uint8_t *data, size_t length) {
    uint32_t crc = 0xffffffff;
    while (length--) {
        uint8_t c = *data++;
        for (uint32_t i = 0x80; i > 0; i >>= 1) {
            bool bit = crc & 0x80000000;
            if (c & i) { bit = !bit; }
            crc <<= 1;
            if(bit) { crc ^= 0x04c11db7; }
        }
    }
    return crc;
}

void cleanRTCMemory() {
    uint64_t blank = 0;
    ESP.rtcUserMemoryWrite(0, (uint32_t*)&blank, sizeof(blank));
}

void wifiConnect(unsigned int max_time_sec = 60) {
    /* Connect to wifi, return when connected. If takes more than `max_time_sec` to connect, enter
     * deep sleep mode for `deep_sleep_min`.
    */
   if (WiFi.status() == WL_CONNECTED) {
       Serial.println("Already connected to Wifi");
       return;
   }

    // RTC use for faster Wifi connection is based on this work:
    // https://www.bakke.online/index.php/2017/06/24/esp8266-wifi-power-reduction-avoiding-network-scan/
    // The ESP8266 RTC memory is arranged into blocks of 4 bytes. The access methods read and write 4 bytes at a time, so the RTC data structure should be padded to a 4-byte multiple.
    struct {
    uint32_t crc32;   // 4 bytes
    uint8_t channel;  // 1 byte,   5 in total
    uint8_t bssid[6]; // 6 bytes, 11 in total
    uint8_t padding;  // 1 byte,  12 in total
    uint32_t ip;
    uint32_t gateway;
    uint32_t subnet;
    } rtcData;

    // Try to read WiFi settings from RTC memory
    bool rtcValid = false;
    if (isDeepSleepWake() && ESP.rtcUserMemoryRead(0, (uint32_t*) &rtcData, sizeof(rtcData))) {
        uint32_t crc = calculateCRC32(((uint8_t*)&rtcData) + 4, sizeof(rtcData) - 4);
        if(crc == rtcData.crc32)
            rtcValid = true;
    }

    Serial.println("Connecting to wifi...");
    WiFi.persistent(false); // don't save info to flash!!!
    if (rtcValid) {
        Serial.println("Using RTC data (fixed IP, existing wifi channel)...");
        WiFi.config(IPAddress(rtcData.ip), IPAddress(rtcData.gateway), IPAddress(rtcData.subnet));
        WiFi.begin(ssid, password, rtcData.channel, rtcData.bssid, true);
    }
    else
        WiFi.begin(ssid, password);

    // Wait for Wifi to connect
    unsigned int retries = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(100);
        retries++;

        // Abort RTC connect after 5s
        if (retries == 50 && rtcValid) {
            Serial.println("Try regular wifi connect");
            WiFi.disconnect(); delay(10);
            WiFi.forceSleepBegin(); delay(10);
            WiFi.forceSleepWake(); delay(10);
            WiFi.begin(ssid, password);
        }
        // Abort wifi connect after 30s
        if (retries == max_time_sec * 10) {
            Serial.println("Abort wifi connect");
            cleanRTCMemory();
            deepSleep();
            return;
        }
    }
    
    // Log info
    Serial.print("Connected with IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("Gateway: ");
    Serial.println(WiFi.gatewayIP());
    Serial.print("Netmask: ");
    Serial.println(WiFi.subnetMask());

    // Save to RTC memory for next reboot
    rtcData.channel = WiFi.channel();
    rtcData.ip = (uint32_t) WiFi.localIP();
    rtcData.gateway = (uint32_t) WiFi.gatewayIP();
    rtcData.subnet = (uint32_t) WiFi.subnetMask();
    memcpy(rtcData.bssid, WiFi.BSSID(), 6); // Copy 6 bytes of BSSID (AP's MAC address)
    rtcData.crc32 = calculateCRC32(((uint8_t*)&rtcData) + 4, sizeof(rtcData) - 4);
    ESP.rtcUserMemoryWrite(0, (uint32_t*)&rtcData, sizeof(rtcData));
}

void httpGetSensor(String url, SensorData& sensor) {
    StaticJsonDocument<jsonCapacity> doc;

    // GET request with retry
    int responseCode = -1;
    unsigned int maxRetry = 15;
    unsigned int retries = 0;
    while (responseCode != HTTP_CODE_OK) {
        // abandon if tried too many times
        retries++;
        if (retries > maxRetry) {
            Serial.println("Retried too many times to GET, sleeping for 10 min");
            cleanRTCMemory(); // in case the GET failed because of bad IP for example
            deepSleep();
        }

        // send HTTP request
        http.useHTTP10(true);
        http.begin(client, url.c_str());
        responseCode = http.GET();

        // if failed, wait a bit
        if (responseCode != HTTP_CODE_OK) {
            Serial.print("GET: bad response code: ");
            Serial.println(responseCode);
            delay(1500);
        }
    }
    

    // read JSON, check for error
    DeserializationError err = deserializeJson(doc, http.getStream());
    if (err) {
        Serial.print("GET: JSON fail: ");
        Serial.println(err.c_str());
        deepSleep();
    }

    // parse data
    Serial.println("GET: success");
    serializeJsonPretty(doc, Serial); Serial.println();
    sensor.calibrate = doc["calibrate"]; // true
    sensor.calibration_duration = doc["calibration_duration"]; // 30
    sensor.calibration_max = doc["calibration_max"]; // 0
    sensor.calibration_min = doc["calibration_min"]; // 1023
    sensor.measure_interval = doc["measure_interval"]; // 3600
    sensor.watering = doc["watering"]; // false
    sensor.force_watering = doc["force_watering"]; // false
    sensor.watering_cooldown = doc["watering_cooldown"]; // 10800
    sensor.watering_cycle_duration = doc["watering_cycle_duration"]; // 5
    sensor.watering_cycle_sleep = doc["watering_cycle_sleep"]; // 5
    sensor.watering_cycle_nb_max = doc["watering_cycle_nb_max"]; // 30
    sensor.watering_humidity_target = doc["watering_humidity_target"]; // 60
    sensor.watering_humidity_threshold = doc["watering_humidity_threshold"]; // 30
    sensor.watering_last_delta = doc["watering_last_delta"]; // 300000
    http.end();
}

void httpPostJSON(String url, String &json) {
    wifiConnect();
    http.begin(client, url.c_str());
    http.addHeader("Content-Type", "application/json");
    http.POST(json);
    http.end();
}

// MEASURING

void sensorsOff() {
    for (int i = 0; i < nbSensors; i++) {
        if (sensors[i].pinSensor >= 0) {
            pinMode(sensors[i].pinSensor, OUTPUT);
            digitalWrite(sensors[i].pinSensor, LOW);
        }
    }
}

void sensorOn(SensorData &sensor) {
    sensorsOff();
    if (sensor.pinSensor >= 0) {
        digitalWrite(sensor.pinSensor, HIGH);
        delay(150);
    }
}

int analogMeasure(short loop=4) {
    int n_sum = 0;
    int calibration_sum = 0;
    for (unsigned short i = 0; i < loop; i++) {
        calibration_sum += analogRead(A0);
        n_sum += 1;
        delay(250);
    }
    return calibration_sum / n_sum;
}

String calibration(SensorData &sensor) {
    Serial.print("Doing calibration: ");
    uint64_t start = millis();

    uint8_t pinStatus = LOW;
    String calibrations = "";

    while (millis() - start < sensor.calibration_duration * 1000) {
        // oscillate LED
        pinStatus = pinStatus == LOW ? HIGH : LOW;
        if (pinCalibrationLED >= 0)
            digitalWrite(pinCalibrationLED, pinStatus);

        int val = analogMeasure();
        Serial.print(val); Serial.print(" ");
        calibrations += calibrations.isEmpty() ? "[" + String(val) : "," + String(val);
        if (val < sensor.calibration_min) sensor.calibration_min = val;
        if (val > sensor.calibration_max) sensor.calibration_max = val;
    }
    calibrations += "]";
    Serial.println("");

    return calibrations;
}

int getHumidity(int humidity_raw, SensorData &sensor) {
    if ((sensor.calibration_max - sensor.calibration_min) == 0)
        sensor.calibration_min -= 1;
    return (sensor.calibration_max - humidity_raw) * 100 / (sensor.calibration_max - sensor.calibration_min); // /!\ max raw = min humidity
}

void watering(SensorData &sensor) {
    Serial.println("Considering watering for " + sensor.id);

    // start with a measure of humidity
    int humidity_raw = analogMeasure();
    int humidity = getHumidity(humidity_raw, sensor);
    unsigned long start = millis();
    sensor.postJSON_watering = 0;
    sensor.postJSON_measures = "[0," + String(humidity_raw) + "]";

    Serial.println("Humidity: raw=" + String(humidity_raw) + " percent=" + String(humidity));

    // enter watering if active and needed
    pinMode(sensor.pinMotor, OUTPUT);
    if (sensor.force_watering || sensor.watering && humidity < sensor.watering_humidity_threshold && sensor.watering_last_delta > sensor.watering_cooldown) {
        Serial.println("Starting watering!");
        while ((sensor.force_watering || humidity < sensor.watering_humidity_target) && sensor.postJSON_watering < sensor.watering_cycle_nb_max) {
            Serial.print("Watering... ");

            analogWrite(sensor.pinMotor, sensor.pinMotor == LED_BUILTIN ? 0 : PWMRANGE * motorPWM);
            delay(sensor.watering_cycle_duration * 1000); // water for watering_cycle_duration
            digitalWrite(sensor.pinMotor, sensor.pinMotor == LED_BUILTIN ? HIGH : LOW);
            delay(sensor.watering_cycle_sleep * 1000); // wait for watering_cycle_sleep for water to diffuse

            humidity_raw = analogMeasure();
            humidity = getHumidity(humidity_raw, sensor);
            sensor.postJSON_measures += ",[" + String((millis() - start) / 1000) + "," + String(humidity_raw) + "]";
            sensor.postJSON_watering++;

            Serial.println("humidity after: " + String(humidity));
        }
    }
    else
        Serial.println("No watering needed");
}

// MAIN LOOP

void setup() {
    // boot setup
    Serial.begin(115200);
    Serial.println("Hello world! " + ESP.getResetReason());
    for (int i = 0; i < 10; i++) {
        pinMode(LED_BUILTIN, OUTPUT);
        digitalWrite(LED_BUILTIN, ((i % 2) == 0) ? LOW : HIGH);
        delay(200);
    }

    // connect to wifi
    wifiConnect();
 
    // load config (loads details via http)
    initSensors();

    // calibrations of all sensors if requested
    for (int i = 0; i < nbSensors; i++) {
        if (sensors[i].calibrate) {
            sensorOn(sensors[i]); // power up humidity sensor

            if (pinCalibrationLED >= 0)
                pinMode(pinCalibrationLED, OUTPUT);

            sensors[i].postJSON_calibrations = calibration(sensors[i]); // actual calibration

            if (pinCalibrationLED >= 0) {
                for (int i = 0; i < 30; i++) {
                    digitalWrite(pinCalibrationLED, LOW);
                    delay(250);
                    digitalWrite(pinCalibrationLED, HIGH);
                    delay(250);
                }
                digitalWrite(pinCalibrationLED, pinCalibrationLED == LED_BUILTIN ? HIGH : LOW);
            }
            else
                delay(15000);
        }
    }

    // for each sensor, do humidity measuring and water if needed
    for (int i = 0; i < nbSensors; i++) {
        sensorOn(sensors[i]);
        watering(sensors[i]);
    }

    sensorsOff();

    // send reports via wifi
    Serial.println("Sending reports via wifi");
    for (int i = 0; i < nbSensors; i++) {
        String postJSON = "{\"calibrations\":" + sensors[i].postJSON_calibrations + ",\"measures\":[" + sensors[i].postJSON_measures + "],\"waterings\":" + sensors[i].postJSON_watering + "}";
        Serial.println(postJSON);
        httpPostJSON(baseURL + sensors[i].id + "/report", postJSON);
    }

    // deep sleep
    Serial.println("Going to sleep :)");
    uint64_t min_measure_interval = sensors[0].measure_interval;
    for (int i = 1; i < nbSensors; i++)
        if (sensors[i].measure_interval < min_measure_interval)
            min_measure_interval = sensors[i].measure_interval;
    ESP.deepSleep(min_measure_interval * 1000 * 1000);
}

void loop() {
    // should not be reached
    delay(10000);
}
