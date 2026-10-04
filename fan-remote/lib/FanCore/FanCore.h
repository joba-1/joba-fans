// FanCore — fan channel logic without any hardware dependency.
// See docs/spec.md ("Fan control") for the reasoning behind the state machine.
#pragma once
#include <stdint.h>

namespace fancore {

struct ChannelParams {
  float minPct = 20;         // lowest duty that keeps the fan turning
  float maxPct = 100;        // duty at speed 100 (noise cap)
  float startPct = 15;       // duty where a spin-up attempt begins
  float kickPct = 50;        // ceiling of the spin-up search (and blind kick level)
  float rampUpPctS = 10;     // duty slew, speeding up (running fan)
  float rampDownPctS = 20;   // duty slew, slowing down
  float spinupPctS = 8;      // duty slew during the spin-up search
  bool tach = true;          // tach signal usable?
  uint16_t spinTimeoutMs = 3000;   // hold at the ceiling this long, then declare stall
  uint16_t stallMs = 5000;         // running, no tach edge this long -> stall
  uint16_t blindKickMs = 1000;     // tach off: hold the kick this long
  uint32_t retryMs = 15000;        // first retry after a stall
  uint32_t retryMaxMs = 300000;    // backoff ceiling
};

enum class State : uint8_t { Off, Spinup, Run, Fault };

const char *stateName(State s);

// speed 0..100 -> duty percent. 0 is off; 1..100 spreads over [min, max].
float dutyForSpeed(int speed, float minPct, float maxPct);

// Edges needed after the start of a spin-up to call the fan "turning" (2 revolutions
// at the usual 2 pulses per revolution).
constexpr uint32_t kSpinEdges = 4;

class Channel {
 public:
  void configure(const ChannelParams &p);
  const ChannelParams &params() const { return p_; }

  void setSpeed(int speed);              // clamps to 0..100
  int speed() const { return speed_; }

  // Advance the machine. `nowMs` is a free-running millisecond counter (wraps are
  // fine), `edges` the monotonically increasing tach edge count of this fan.
  void update(uint32_t nowMs, uint32_t edges);

  float duty() const { return duty_; }          // current PWM duty, percent
  float targetDuty() const;                     // duty the speed asks for
  State state() const { return state_; }
  bool fault() const { return fault_; }         // stalled, until a spin-up succeeds again

 private:
  void enterSpinup(uint32_t now, uint32_t edges);
  void enterFault(uint32_t now);
  void slew(float target, float dtS);

  ChannelParams p_;
  int speed_ = 0;
  float duty_ = 0;
  State state_ = State::Off;
  bool fault_ = false;
  bool started_ = false;
  uint32_t last_ = 0;
  uint32_t spinBase_ = 0;      // edge count at the start of the spin-up
  uint32_t capSince_ = 0;      // when the ramp first hit its ceiling
  bool atCap_ = false;
  uint32_t lastEdges_ = 0;     // stall watch
  uint32_t lastEdgeAt_ = 0;
  uint32_t faultSince_ = 0;
  uint32_t retryDelay_ = 0;
};

// RPM from windows of tach edges. The ISR records the count of edges in the window
// and the timestamps (µs) of the first and last one.
class RpmMeter {
 public:
  void setPulsesPerRev(uint8_t ppr) { ppr_ = ppr ? ppr : 2; }
  void addWindow(uint32_t edges, uint32_t firstUs, uint32_t lastUs, uint32_t windowUs);
  uint16_t rpm() const { return rpm_; }
  void reset() { rpm_ = 0; }

 private:
  uint8_t ppr_ = 2;
  uint16_t rpm_ = 0;
};

// ---- device identity -------------------------------------------------------------------
// Boards are named by a running number kept in devices.csv (MAC -> number), not by
// MAC-derived digits. An unregistered board still works under a recognisable temporary id.
struct DeviceEntry {
  uint8_t mac[6];
  uint16_t n;
};
// Number registered for this MAC, or 0.
int deviceNumber(const DeviceEntry *table, unsigned len, const uint8_t mac[6]);
// "fan-3" for a registered board, "fan-new-a1b2c3" (last three MAC bytes) otherwise.
void formatDeviceId(char *out, unsigned n, int number, const uint8_t mac[6]);

// ---- idle / active policy ---------------------------------------------------------------
// Full power for `timeoutMs` after the last user interaction, low power after that.
class PowerPolicy {
 public:
  void configure(uint32_t timeoutMs) { timeoutMs_ = timeoutMs; }
  void activity(uint32_t nowMs) { last_ = nowMs; seen_ = true; }
  // `forceActive`: something needs the radio at full speed (setup portal, OTA, no WiFi yet).
  bool idle(uint32_t nowMs, bool forceActive) const {
    if (forceActive || !seen_) return false;
    return (uint32_t)(nowMs - last_) >= timeoutMs_;
  }
  uint32_t idleInMs(uint32_t nowMs) const {   // 0 when already idle
    if (!seen_) return timeoutMs_;
    uint32_t e = nowMs - last_;
    return e >= timeoutMs_ ? 0 : timeoutMs_ - e;
  }

 private:
  uint32_t timeoutMs_ = 60000;
  uint32_t last_ = 0;
  bool seen_ = false;
};

}  // namespace fancore
