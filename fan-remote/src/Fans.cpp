#include "Fans.h"

#include <esp_task_wdt.h>
#include <esp_timer.h>

#include <mutex>

#include "NetLog.h"

Fans fans;

// Board: FAN1 PWM=D1 TACH=D2, FAN2 D3/D4, FAN3 D7/D10, FAN4 D6/D5 (verified against
// fan-controller.kicad_pcb).
static const uint8_t kPwmPin[kFans] = {D1, D3, D7, D6};
static const uint8_t kTachPin[kFans] = {D2, D4, D10, D5};

constexpr uint32_t kPwmHz = 25000;   // Intel 4-wire fan spec
constexpr uint8_t kPwmBits = 10;
constexpr uint32_t kPwmMax = (1u << kPwmBits) - 1;
constexpr uint32_t kTickMs = 20;
constexpr uint32_t kRpmWindowMs = 1000;
constexpr uint32_t kGlitchUs = 1500;  // tach edges closer than this are noise

struct Tach {
  volatile uint32_t total = 0;       // all edges ever, drives FanCore
  volatile uint32_t winCount = 0;    // edges in the current RPM window
  volatile uint32_t winFirst = 0;
  volatile uint32_t winLast = 0;
  volatile uint32_t lastUs = 0;
};

static Tach tach[kFans];
static portMUX_TYPE tachMux = portMUX_INITIALIZER_UNLOCKED;

static void IRAM_ATTR tachIsr(void *arg) {
  Tach *t = static_cast<Tach *>(arg);
  uint32_t now = (uint32_t)esp_timer_get_time();
  if ((uint32_t)(now - t->lastUs) < kGlitchUs) return;
  t->lastUs = now;
  t->total = t->total + 1;
  if (t->winCount == 0) t->winFirst = now;
  t->winLast = now;
  t->winCount = t->winCount + 1;
}

static fancore::Channel chan[kFans];
static fancore::RpmMeter meter[kFans];
static uint32_t windowStart[kFans];
static uint32_t lastDuty[kFans];
static uint8_t lastSpeedSeen[kFans];
static fancore::State lastState[kFans];
static bool lastFault[kFans];
static uint32_t rev = 1;
static volatile uint8_t event[kFans];   // 1 = stalled, 2 = turning again
static std::mutex mu;

void Fans::earlyInit() {
  for (int i = 0; i < kFans; i++) {
    pinMode(kPwmPin[i], OUTPUT);
    digitalWrite(kPwmPin[i], LOW);
  }
}

void Fans::configureChannel(int i) {
  const Settings &s = settings();
  fancore::ChannelParams p;
  p.minPct = s.ch[i].minPct;
  p.maxPct = s.ch[i].maxPct;
  p.startPct = s.ch[i].minPct < 15 ? s.ch[i].minPct : 15;
  p.tach = s.ch[i].tach;
  p.rampUpPctS = s.rampUp ? s.rampUp : 1;
  p.rampDownPctS = s.rampDown ? s.rampDown : 1;
  chan[i].configure(p);
  meter[i].setPulsesPerRev(s.ch[i].ppr);
}

void Fans::begin() {
  for (int i = 0; i < kFans; i++) {
    configureChannel(i);
    ledcAttach(kPwmPin[i], kPwmHz, kPwmBits);
    ledcWrite(kPwmPin[i], 0);
    pinMode(kTachPin[i], INPUT);  // 10k pull-up to 3V3 is on the board
    attachInterruptArg(digitalPinToInterrupt(kTachPin[i]), tachIsr, &tach[i], FALLING);
    windowStart[i] = millis();
  }
  xTaskCreate(taskEntry, "fans", 6144, this, configMAX_PRIORITIES - 3, nullptr);
}

void Fans::applyConfig() {
  std::lock_guard<std::mutex> l(mu);
  for (int i = 0; i < kFans; i++) configureChannel(i);
}

void Fans::taskEntry(void *self) {
  esp_task_wdt_add(nullptr);
  TickType_t t = xTaskGetTickCount();
  for (;;) {
    vTaskDelayUntil(&t, pdMS_TO_TICKS(kTickMs));
    esp_task_wdt_reset();
    static_cast<Fans *>(self)->tick();
  }
}

void Fans::tick() {
  std::lock_guard<std::mutex> l(mu);
  const uint32_t now = millis();
  for (int i = 0; i < kFans; i++) {
    const bool en = settings().ch[i].enabled;
    if (!en && chan[i].speed() != 0) chan[i].setSpeed(0);
    chan[i].update(now, tach[i].total);

    uint32_t d = (uint32_t)(chan[i].duty() * kPwmMax / 100.0f + 0.5f);
    if (d > kPwmMax) d = kPwmMax;
    if (d != lastDuty[i]) {
      ledcWrite(kPwmPin[i], d);
      lastDuty[i] = d;
    }

    if (now - windowStart[i] >= kRpmWindowMs) {
      uint32_t n, first, last;
      portENTER_CRITICAL(&tachMux);
      n = tach[i].winCount;
      first = tach[i].winFirst;
      last = tach[i].winLast;
      tach[i].winCount = 0;
      portEXIT_CRITICAL(&tachMux);
      meter[i].addWindow(n, first, last, (now - windowStart[i]) * 1000u);
      windowStart[i] = now;
    }

    if (chan[i].state() != lastState[i] || chan[i].fault() != lastFault[i] ||
        chan[i].speed() != lastSpeedSeen[i]) {
      // Logging may block on DNS/UDP: never from this task. loop() reports it.
      if (chan[i].fault() && !lastFault[i]) event[i] = 1;
      if (!chan[i].fault() && lastFault[i]) event[i] = 2;
      lastState[i] = chan[i].state();
      lastFault[i] = chan[i].fault();
      lastSpeedSeen[i] = chan[i].speed();
      rev++;
    }
  }
}

void Fans::setSpeed(int ch, int speed) {
  if (speed < 0) speed = 0;
  if (speed > 100) speed = 100;
  std::lock_guard<std::mutex> l(mu);
  for (int i = 0; i < kFans; i++) {
    if ((ch >= 0 && i != ch) || !settings().ch[i].enabled) continue;
    chan[i].setSpeed(speed);
    if (speed > 0) settings().lastOn[i] = speed;
    settings().lastSpeed[i] = speed;
  }
  rev++;
}

void Fans::setPower(int ch, bool on) {
  if (!on) {
    setSpeed(ch, 0);
    return;
  }
  for (int i = 0; i < kFans; i++) {
    if (ch >= 0 && i != ch) continue;
    int s;
    {
      std::lock_guard<std::mutex> l(mu);
      s = settings().lastOn[i];
    }
    setSpeed(i, s);
  }
}

int Fans::presetFor(int speed) {
  for (int i = 0; i < kPresets; i++)
    if (settings().presets[i] == speed) return i;
  return -1;
}

bool Fans::setPreset(int ch, const char *id) {
  for (int i = 0; i < kPresets; i++) {
    if (strcmp(id, kPresetIds[i]) == 0) {
      setSpeed(ch, settings().presets[i]);
      return true;
    }
  }
  return false;
}

FanStatus Fans::status(int ch) {
  std::lock_guard<std::mutex> l(mu);
  FanStatus s;
  s.enabled = settings().ch[ch].enabled;
  s.tach = settings().ch[ch].tach;
  s.speed = chan[ch].speed();
  s.duty = chan[ch].duty();
  s.rpm = meter[ch].rpm();
  s.state = chan[ch].state();
  s.fault = chan[ch].fault();
  return s;
}

void Fans::logEvents() {
  for (int i = 0; i < kFans; i++) {
    uint8_t e = event[i];
    if (!e) continue;
    event[i] = 0;
    if (e == 1) logf(LOG_WARN, "fan %d stalled", i + 1);
    else logf(LOG_INFO, "fan %d turning again", i + 1);
  }
}

uint32_t Fans::revision() {
  std::lock_guard<std::mutex> l(mu);
  return rev;
}
