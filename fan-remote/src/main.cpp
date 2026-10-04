// fan-remote — firmware for the 4-channel fan controller (XIAO ESP32-C3).
// See docs/spec.md. The fans run in their own task (Fans.cpp); this file wires up the
// network side and persists the speeds.
#include <Arduino.h>

#include "Fans.h"
#include "Mqtt.h"
#include "Net.h"
#include "Power.h"
#include "NetLog.h"
#include "Settings.h"
#include "Web.h"

static uint8_t savedSpeed[kFans];
static uint32_t changedAt = 0;
static bool dirty = false;

static void persistSpeeds() {
  // Write the target speeds 5 s after the last change: sliders must not wear the flash.
  Settings &s = settings();
  bool differs = false;
  for (int i = 0; i < kFans; i++)
    if (s.lastSpeed[i] != savedSpeed[i]) differs = true;
  if (differs && !dirty) {
    dirty = true;
    changedAt = millis();
  }
  if (dirty && millis() - changedAt > 5000) {
    settingsSaveSpeeds();
    for (int i = 0; i < kFans; i++) savedSpeed[i] = s.lastSpeed[i];
    dirty = false;
  }
}

void setup() {
  Fans::earlyInit();  // PWM pins low first, before anything can take time
  Serial.begin(115200);
  settingsLoad();
  logf(LOG_INFO, "fan-remote %s (%s) %s", FW_VERSION, FW_GIT, deviceId());

  fans.begin();
  powerBegin();
  Settings &s = settings();
  for (int i = 0; i < kFans; i++) savedSpeed[i] = s.lastSpeed[i];
  if (s.bootMode == 0) {
    for (int i = 0; i < kFans; i++)
      if (s.lastSpeed[i] && s.ch[i].enabled) fans.setSpeed(i, s.lastSpeed[i]);  // soft start
  }

  mqttBegin();
  netBegin();     // may take up to ~20 s; the fans do not care
}

static bool webUp = false;

void loop() {
  netLoop();
  // The setup portal and the web server both want port 80: start the server only once
  // WiFi is connected and the portal is gone.
  if (!webUp && netConnected() && !netPortalActive()) {
    webBegin();
    webUp = true;
  }
  fans.logEvents();
  powerLoop();
  netlogLoop();
  mqttLoop();
  if (webUp) webLoop();
  persistSpeeds();
  delay(5);
}
