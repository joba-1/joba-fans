// Settings.h — everything persistent, kept in NVS (Preferences).
// Compile-time values from config.ini are only the defaults of a fresh board.
#pragma once
#include <Arduino.h>

constexpr int kFans = 4;
constexpr int kPresets = 5;

struct ChannelCfg {
  char name[24];
  bool enabled;
  uint8_t minPct;   // lowest duty that keeps the fan turning
  uint8_t maxPct;   // duty at speed 100
  bool tach;        // tach signal wired and usable
  uint8_t ppr;      // tach pulses per revolution (PC fans: 2)
};

struct Settings {
  char name[32];        // friendly name ("Living room")
  char adminPass[48];
  char mqttHost[64];
  uint16_t mqttPort;
  char mqttUser[32];
  char mqttPass[64];
  char syslogHost[64];
  char ntpHost[64];
  ChannelCfg ch[kFans];
  uint8_t presets[kPresets];   // speeds for quiet, low, medium, high, max
  uint8_t rampUp;              // duty slew, %/s
  uint8_t rampDown;
  uint8_t bootMode;            // 0 = restore last speeds, 1 = all off
  bool protectControl;         // require the admin login for /api/set as well
  uint8_t lastSpeed[kFans];    // target speeds, restored at boot
  uint8_t lastOn[kFans];       // last non-zero speed ("ON" brings this back)
};

extern const char *const kPresetIds[kPresets];  // "quiet", "low", "medium", "high", "max"

Settings &settings();
void settingsLoad();
void settingsSaveAll();                  // identity, channels, presets, ramps, flags
void settingsSaveNet();                  // name, mqtt*, syslog, ntp, adminPass
void settingsSaveSpeeds();               // lastSpeed / lastOn
void settingsDefaults(bool netOnly);     // back to config.ini defaults (not saved)
void settingsEraseNet();                 // forget runtime network targets

const char *deviceId();                  // "fan-3": the number registered for this MAC in devices.csv
bool deviceRegistered();                 // false: temporary id "fan-new-xxxxxx", register the board
