#include "Led.h"

#include <time.h>

#include "FanCore.h"
#include "Fans.h"
#include "Mqtt.h"
#include "Net.h"
#include "NetLog.h"
#include "Settings.h"

#ifndef LED_FAN_PIN
#define LED_FAN_PIN -1
#endif
#ifndef LED_ALERT_PIN
#define LED_ALERT_PIN -1
#endif
#ifndef LED_ACTIVE_LOW
#define LED_ACTIVE_LOW 1
#endif

using namespace fancore;

static constexpr uint32_t kLedHz = 1000;
static constexpr uint8_t kLedBits = 10;
static constexpr uint32_t kLedMax = (1u << kLedBits) - 1;

static bool attached = false;

bool ledAvailable() { return LED_FAN_PIN >= 0; }

// Brightness 0..100 (percent of full), applied to the pin honouring the polarity.
static void writePct(int pin, uint8_t pct) {
  if (pin < 0) return;
  uint32_t duty = (uint32_t)pct * kLedMax / 100;
  ledcWrite(pin, LED_ACTIVE_LOW ? kLedMax - duty : duty);
}

void ledBegin() {
  if (!ledAvailable()) return;
  attached = ledcAttach(LED_FAN_PIN, kLedHz, kLedBits);
  if (LED_ALERT_PIN >= 0) attached = ledcAttach(LED_ALERT_PIN, kLedHz, kLedBits) && attached;
  writePct(LED_FAN_PIN, 0);
  writePct(LED_ALERT_PIN, 0);
}

bool ledNightNow() {
  time_t now = time(nullptr);
  if (now < 1700000000) return false;   // clock not set: treat as day
  struct tm tm;
  localtime_r(&now, &tm);
  return inNightWindow(tm.tm_hour, settings().nightFrom, settings().nightTo);
}

uint8_t ledPercentNow() {
  const Settings &s = settings();
  if (!s.ledMode) return 0;
  return ledPercent(ledNightNow(), s.ledDay, s.ledNight);
}

uint8_t healthIssues() {
  HealthInput h;
  for (int i = 0; i < kFans; i++) {
    FanStatus st = fans.status(i);
    if (st.enabled && st.fault) h.stalledFans++;
  }
  h.wifi = netConnected();
  h.mqttWanted = settings().mqttHost[0] != 0;
  h.mqtt = mqttConnected();
  h.timeSynced = resNtp().lastOkMs != 0;
  return fancore::healthIssues(h);
}

void ledLoop() {
  if (!attached) return;
  static uint32_t last = 0;
  uint32_t now = millis();
  if (now - last < 40) return;
  last = now;

  bool fansOn = false;
  for (int i = 0; i < kFans; i++) {
    FanStatus st = fans.status(i);
    if (st.enabled && st.speed > 0) fansOn = true;
  }
  const bool healthy = healthIssues() == 0;
  const uint8_t pct = ledPercentNow();

  if (LED_ALERT_PIN >= 0) {
    // Two LEDs: one for "fans on", one that lights when something is wrong.
    writePct(LED_FAN_PIN, fansOn ? pct : 0);
    writePct(LED_ALERT_PIN, healthy ? 0 : pct);
  } else {
    // One LED carries both facts as a pattern.
    writePct(LED_FAN_PIN, ledPhaseOn(ledPatternCombined(fansOn, healthy), now) ? pct : 0);
  }
}
