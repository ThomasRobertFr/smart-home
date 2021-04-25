#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WebServer.h>
#include <WiFiClient.h>
#include <RBDdimmer.h>

class ESP8266WebServerCustom: public ESP8266WebServer {
  using ESP8266WebServer::ESP8266WebServer;
  public:
    unsigned long lastClient() { return _statusChange;}
};


WiFiClient client;
HTTPClient http;
ESP8266WebServerCustom server(80);
dimmerLamp dimmer(D7, D6);

const char* ssid = "TOFILL";
const char* password = "TOFILL";

void deepSleep(uint64_t durationMin = 1) {
  ESP.deepSleep(durationMin * 60 * 1000 * 1000);
  delay(1000);
}

void wifiConnect(unsigned int max_time_sec = 60) {
  Serial.println("Connecting to wifi...");
  WiFi.persistent(false); // don't save info to flash!!!
  WiFi.begin(ssid, password);

  // Wait for Wifi to connect
  unsigned int retries = 0;
  while (WiFi.status() != WL_CONNECTED) {
    Serial.println("Trying to connect");
    delay(100);
    retries++;

    if (retries == max_time_sec * 10) {
      Serial.println("Abort wifi connect");
      deepSleep();
      return;
    }
  }
  
  Serial.print("Connected with IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("Gateway: ");
  Serial.println(WiFi.gatewayIP());
  Serial.print("Netmask: ");
  Serial.println(WiFi.subnetMask());
}

bool lightOn = true;
int lightBrightness = 1023;

void update_light() {
  if (lightOn) {
    dimmer.setState(ON);
    dimmer.setPower(lightBrightness * 100 / 1023);
  }
  else {
    dimmer.setState(OFF);
  }
}

void handle_query() {
  for (int i = 0; i < server.args(); i++) {
    if (server.argName(i) == "on")
      lightOn = true;
    else if (server.argName(i) == "off")
      lightOn = false;
    else if (server.argName(i) == "brightness")
      lightBrightness = server.arg(i).toInt();
  }
  update_light();

  server.send(200, "text/json", "{\"on\": " + String(lightOn) + ", \"brightness\": "+ String(lightBrightness) +"}");
}

void setup() {
  Serial.begin(115200);
  Serial.println("Hello world! " + ESP.getResetReason());
  wifiConnect();
  server.on("/", handle_query);
  server.begin();
  Serial.println("HTTP server started");
  dimmer.begin(NORMAL_MODE, ON);
  dimmer.setPower(99);
}

void loop() {
  server.handleClient();

  // It seems like looping on handling Wifi clients solicitate the CPU quite a lot and sometimes
  // does not let it handle the interruptions needed for the AC dimmer. This code below allows to
  // add some delays, which depends on how long it has been since the last wifi client. Indeed,
  // it is frequent to change the brightness multiple times in a row to a desired value.
  unsigned long lastClientDelay = (millis() - server.lastClient()) / 1000;
  if (lastClientDelay < 10) // < 10s before last request, we look frequently for new request
    delay(80);
  else if (lastClientDelay < 30) // 10-30s before last request, we look sometimes for new request
    delay(400);
  else  //  // > 30s before last request, we look rarely for new request
    delay(666);
}
