#include "Power.h"

#include <WiFi.h>

#include "FanCore.h"
#include "Net.h"
#include "NetLog.h"

static fancore::PowerPolicy policy;
static volatile uint32_t lastActivity = 0;   // written from the web / MQTT tasks
static volatile bool pending = false;
static bool idle = false;

void powerBegin() {
  policy.configure((uint32_t)CFG_IDLE_S * 1000u);
  policy.activity(millis());   // the first minute after boot is always full power
  setCpuFrequencyMhz(CFG_CPU_ACTIVE_MHZ);
}

void powerActivity() {
  lastActivity = millis();
  pending = true;
}

static void apply(bool toIdle) {
  if (toIdle) {
    WiFi.setSleep(true);                       // WIFI_PS_MIN_MODEM: wake at every DTIM
    setCpuFrequencyMhz(CFG_CPU_IDLE_MHZ);
  } else {
    setCpuFrequencyMhz(CFG_CPU_ACTIVE_MHZ);    // clock up first, then the radio
    WiFi.setSleep(false);
  }
  idle = toIdle;
  logf(LOG_DEBUG, "power: %s, cpu %u MHz", idle ? "standby" : "active", (unsigned)getCpuFrequencyMhz());
}

void powerLoop() {
  if (pending) {
    pending = false;
    policy.activity(lastActivity);
  }
  if (!CFG_POWER_SAVE) return;
  // Setup portal, no WiFi yet: nothing to save, and the portal wants the radio awake.
  const bool force = !netConnected() || netPortalActive();
  const bool wantIdle = policy.idle(millis(), force);
  if (wantIdle != idle) apply(wantIdle);
}

bool powerIdle() { return idle; }
uint32_t powerCpuMhz() { return getCpuFrequencyMhz(); }
uint32_t powerIdleInS() { return (policy.idleInMs(millis()) + 999) / 1000; }
