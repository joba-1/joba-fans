// Fans.h — hardware side of the four fan channels: PWM, tach ISRs and the task that
// runs FanCore. Independent of WiFi/MQTT/web: they only call setSpeed() and read status().
#pragma once
#include <Arduino.h>

#include "FanCore.h"
#include "Settings.h"

struct FanStatus {
  bool enabled;
  bool tach;
  uint8_t speed;      // target speed 0..100
  float duty;         // PWM duty now, percent
  uint16_t rpm;
  fancore::State state;
  bool fault;
};

class Fans {
 public:
  // Drive the PWM pins low before anything else. Call first thing in setup().
  static void earlyInit();

  void begin();          // after settingsLoad(); starts the fan task
  void applyConfig();    // re-read limits / ramps from settings()

  // ch is 0-based; -1 = all enabled channels.
  void setSpeed(int ch, int speed);
  void setPower(int ch, bool on);              // on = last non-zero speed
  bool setPreset(int ch, const char *id);      // false if the id is unknown
  static int presetFor(int speed);             // preset index with exactly that speed, or -1

  FanStatus status(int ch);
  uint32_t revision();                         // bumps on speed / state / fault changes
  void logEvents();                            // call from loop(): reports stalls / recoveries

 private:
  static void taskEntry(void *self);
  void tick();
  void configureChannel(int i);
};

extern Fans fans;
