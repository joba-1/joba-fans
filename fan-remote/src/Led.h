// Led.h — optional status LED(s): fans on/off and healthy/unhealthy, dimmed at night.
// Pins come from build flags (platformio.ini): LED_FAN_PIN, LED_ALERT_PIN, LED_ACTIVE_LOW.
// No flag, no LED: everything below is then a no-op. See docs/spec.md ("Status LED").
#pragma once
#include <Arduino.h>

void ledBegin();
void ledLoop();                // call from loop(); cheap, does its work every ~40 ms
bool ledAvailable();           // this build has a LED to drive
uint8_t healthIssues();        // fancore::kIssue* bit mask, 0 = healthy
bool ledNightNow();            // inside the night window (needs a synchronised clock)
uint8_t ledPercentNow();       // brightness the LED is allowed right now, 0 when switched off
