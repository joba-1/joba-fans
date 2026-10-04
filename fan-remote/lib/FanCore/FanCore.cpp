#include "FanCore.h"

#include <math.h>
#include <stdio.h>

namespace fancore {

const char *stateName(State s) {
  switch (s) {
    case State::Off: return "off";
    case State::Spinup: return "spinup";
    case State::Run: return "run";
    case State::Fault: return "fault";
  }
  return "?";
}

float dutyForSpeed(int speed, float minPct, float maxPct) {
  if (speed <= 0) return 0;
  if (speed > 100) speed = 100;
  if (maxPct < minPct) maxPct = minPct;
  return minPct + (maxPct - minPct) * (float)speed / 100.0f;
}

void Channel::configure(const ChannelParams &p) { p_ = p; }

void Channel::setSpeed(int speed) {
  if (speed < 0) speed = 0;
  if (speed > 100) speed = 100;
  speed_ = speed;
}

float Channel::targetDuty() const { return dutyForSpeed(speed_, p_.minPct, p_.maxPct); }

void Channel::enterSpinup(uint32_t now, uint32_t edges) {
  state_ = State::Spinup;
  float tgt = targetDuty();
  duty_ = p_.startPct < tgt ? p_.startPct : tgt;
  spinBase_ = edges;
  atCap_ = false;
  capSince_ = now;
}

void Channel::enterFault(uint32_t now) {
  state_ = State::Fault;
  fault_ = true;
  duty_ = 0;
  faultSince_ = now;
  if (retryDelay_ == 0) retryDelay_ = p_.retryMs;
}

void Channel::slew(float target, float dtS) {
  if (duty_ < target) {
    duty_ += p_.rampUpPctS * dtS;
    if (duty_ > target) duty_ = target;
  } else if (duty_ > target) {
    duty_ -= p_.rampDownPctS * dtS;
    if (duty_ < target) duty_ = target;
  }
}

void Channel::update(uint32_t now, uint32_t edges) {
  float dtS = 0;
  if (started_) {
    uint32_t dt = now - last_;
    if (dt > 500) dt = 500;  // a late tick must not turn into a big duty jump
    dtS = dt / 1000.0f;
  }
  started_ = true;
  last_ = now;

  const float tgt = targetDuty();

  switch (state_) {
    case State::Off:
      duty_ = 0;
      if (tgt > 0) {
        enterSpinup(now, edges);
        // fall through the next tick; the first duty is already set
      }
      break;

    case State::Spinup: {
      if (tgt <= 0) {  // cancelled
        state_ = State::Off;
        duty_ = 0;
        break;
      }
      const float ceiling = p_.kickPct > tgt ? p_.kickPct : tgt;
      if (p_.tach) {
        if (edges - spinBase_ >= kSpinEdges) {  // turning
          state_ = State::Run;
          fault_ = false;
          retryDelay_ = 0;
          lastEdges_ = edges;
          lastEdgeAt_ = now;
          break;
        }
        duty_ += p_.spinupPctS * dtS;
        if (duty_ >= ceiling) {
          duty_ = ceiling;
          if (!atCap_) {
            atCap_ = true;
            capSince_ = now;
          } else if (now - capSince_ >= p_.spinTimeoutMs) {
            enterFault(now);
          }
        }
      } else {  // blind: no feedback, use a short fixed kick
        duty_ += p_.spinupPctS * dtS;
        if (duty_ >= ceiling) {
          duty_ = ceiling;
          if (!atCap_) {
            atCap_ = true;
            capSince_ = now;
          } else if (now - capSince_ >= p_.blindKickMs) {
            state_ = State::Run;
          }
        }
      }
      break;
    }

    case State::Run:
      slew(tgt, dtS);
      if (tgt <= 0) {
        if (duty_ <= 0) {
          duty_ = 0;
          state_ = State::Off;
        }
        break;
      }
      if (p_.tach) {
        if (edges != lastEdges_) {
          lastEdges_ = edges;
          lastEdgeAt_ = now;
        } else if (now - lastEdgeAt_ >= p_.stallMs) {
          enterFault(now);
        }
      }
      break;

    case State::Fault:
      duty_ = 0;
      if (tgt <= 0) {  // switching off acknowledges the fault
        state_ = State::Off;
        fault_ = false;
        retryDelay_ = 0;
        break;
      }
      if (now - faultSince_ >= retryDelay_) {
        uint32_t next = retryDelay_ * 2;
        retryDelay_ = next > p_.retryMaxMs ? p_.retryMaxMs : next;
        enterSpinup(now, edges);  // fault_ stays set until the fan turns again
      }
      break;
  }
}

void RpmMeter::addWindow(uint32_t edges, uint32_t firstUs, uint32_t lastUs, uint32_t windowUs) {
  if (edges == 0 || windowUs == 0) {
    rpm_ = 0;
    return;
  }
  double rpm;
  uint32_t span = lastUs - firstUs;  // wrap-safe
  if (edges >= 2 && span > 0) {
    rpm = (double)(edges - 1) * 60e6 / ((double)span * ppr_);
  } else {
    rpm = 60e6 / ((double)windowUs * ppr_);  // one edge: coarse upper bound, still "alive"
  }
  if (rpm > 65535) rpm = 65535;
  rpm_ = (uint16_t)(rpm + 0.5);
}

int deviceNumber(const DeviceEntry *table, unsigned len, const uint8_t mac[6]) {
  for (unsigned i = 0; i < len; i++) {
    bool same = true;
    for (int b = 0; b < 6; b++)
      if (table[i].mac[b] != mac[b]) { same = false; break; }
    if (same) return table[i].n;
  }
  return 0;
}

void formatDeviceId(char *out, unsigned n, int number, const uint8_t mac[6]) {
  if (number > 0) snprintf(out, n, "fan-control-%d", number);
  else snprintf(out, n, "fan-control-new-%02x%02x%02x", mac[3], mac[4], mac[5]);
}

}  // namespace fancore
