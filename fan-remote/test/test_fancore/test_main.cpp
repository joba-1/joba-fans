// Unit tests for FanCore — run with: pio test -e native
#include <unity.h>

#include <math.h>

#include "FanCore.h"

using namespace fancore;

// A tiny simulated fan: needs `startDuty` to begin turning from standstill, keeps
// turning down to `holdDuty`, makes 2 edges per revolution at rpm = duty * 30.
struct SimFan {
  float startDuty = 28, holdDuty = 12;
  bool turning = false;
  bool blocked = false;
  double edgeAcc = 0;
  uint32_t edges = 0;
  void step(float duty, uint32_t dtMs) {
    if (blocked) { turning = false; return; }
    if (!turning && duty >= startDuty) turning = true;
    if (turning && duty < holdDuty) turning = false;
    if (turning) {
      double rpm = duty * 30.0;
      edgeAcc += rpm / 60.0 * 2.0 * dtMs / 1000.0;
      while (edgeAcc >= 1) { edgeAcc -= 1; edges++; }
    }
  }
};

static void run(Channel &c, SimFan &f, uint32_t &now, uint32_t ms, uint32_t tick = 20) {
  for (uint32_t t = 0; t < ms; t += tick) {
    now += tick;
    c.update(now, f.edges);
    f.step(c.duty(), tick);
  }
}

void setUp() {}
void tearDown() {}

void test_duty_mapping() {
  TEST_ASSERT_EQUAL_FLOAT(0, dutyForSpeed(0, 20, 100));
  TEST_ASSERT_EQUAL_FLOAT(100, dutyForSpeed(100, 20, 100));
  TEST_ASSERT_FLOAT_WITHIN(0.01, 60, dutyForSpeed(50, 20, 100));
  TEST_ASSERT_FLOAT_WITHIN(0.01, 20.8, dutyForSpeed(1, 20, 100));
  TEST_ASSERT_FLOAT_WITHIN(0.01, 80, dutyForSpeed(100, 20, 80));  // noise cap
  TEST_ASSERT_EQUAL_FLOAT(100, dutyForSpeed(250, 20, 100));       // clamped
  TEST_ASSERT_EQUAL_FLOAT(30, dutyForSpeed(50, 30, 10));          // max < min -> min
}

void test_starts_from_low_duty_and_stays_below_kick() {
  Channel c; c.configure(ChannelParams{}); SimFan f; uint32_t now = 0;
  c.setSpeed(10);  // target = 28 %
  float peak = 0;
  for (int i = 0; i < 400; i++) { run(c, f, now, 20); if (c.duty() > peak) peak = c.duty(); }
  TEST_ASSERT_EQUAL(State::Run, c.state());
  TEST_ASSERT_FALSE(c.fault());
  TEST_ASSERT_TRUE(peak <= 34.0f);  // started at ~28 %, never anywhere near the 50 % kick
  TEST_ASSERT_FLOAT_WITHIN(0.5, c.targetDuty(), c.duty());
}

void test_first_duty_is_gentle() {
  Channel c; c.configure(ChannelParams{}); c.setSpeed(100);
  c.update(0, 0);   // Off -> Spinup
  c.update(20, 0);
  TEST_ASSERT_EQUAL(State::Spinup, c.state());
  TEST_ASSERT_TRUE(c.duty() < 20.0f);  // starts at startPct, not at 100 %
}

void test_start_duty_never_above_target() {
  ChannelParams p; p.minPct = 10; p.startPct = 15;
  Channel c; c.configure(p); c.setSpeed(1);  // target 10.9 %
  c.update(0, 0);
  TEST_ASSERT_TRUE(c.duty() <= c.targetDuty() + 0.001f);
}

void test_spinup_detects_turning_and_slews_down_after() {
  Channel c; c.configure(ChannelParams{}); SimFan f; uint32_t now = 0;
  c.setSpeed(100);  // target 100 %: spin-up search runs up to the target, then ramp
  run(c, f, now, 20000);
  TEST_ASSERT_EQUAL(State::Run, c.state());
  TEST_ASSERT_FLOAT_WITHIN(0.5, 100.0, c.duty());
  c.setSpeed(1);  // now slow down; the fan keeps turning (hold 12 %)
  run(c, f, now, 20000);
  TEST_ASSERT_EQUAL(State::Run, c.state());
  TEST_ASSERT_FALSE(c.fault());
  TEST_ASSERT_FLOAT_WITHIN(0.5, 20.8, c.duty());
}

void test_slew_limits() {
  Channel c; c.configure(ChannelParams{}); SimFan f; uint32_t now = 0;
  c.setSpeed(1); run(c, f, now, 10000);
  float before = c.duty();
  c.setSpeed(100);
  run(c, f, now, 1000);  // 1 s at 10 %/s
  TEST_ASSERT_TRUE(c.duty() - before <= 10.5f);
  TEST_ASSERT_TRUE(c.duty() - before >= 9.0f);
}

void test_off_ramps_down_then_cuts() {
  Channel c; c.configure(ChannelParams{}); SimFan f; uint32_t now = 0;
  c.setSpeed(50); run(c, f, now, 15000);
  TEST_ASSERT_EQUAL(State::Run, c.state());
  c.setSpeed(0);
  run(c, f, now, 200);
  TEST_ASSERT_TRUE(c.duty() > 0);          // not an instant cut
  run(c, f, now, 10000);
  TEST_ASSERT_EQUAL(State::Off, c.state());
  TEST_ASSERT_EQUAL_FLOAT(0, c.duty());
  TEST_ASSERT_FALSE(c.fault());
}

void test_blocked_fan_faults_and_stops_driving() {
  Channel c; c.configure(ChannelParams{}); SimFan f; f.blocked = true; uint32_t now = 0;
  c.setSpeed(60);
  float peak = 0;
  // search 15 -> 60 % at 8 %/s (~5.6 s) + 3 s hold at the ceiling
  for (int i = 0; i < 600; i++) { run(c, f, now, 20); if (c.duty() > peak) peak = c.duty(); }
  TEST_ASSERT_EQUAL(State::Fault, c.state());
  TEST_ASSERT_TRUE(c.fault());
  TEST_ASSERT_EQUAL_FLOAT(0, c.duty());
  TEST_ASSERT_TRUE(peak <= 68.0f + 0.01f);  // never above max(kick, target)
}

void test_fault_retries_with_backoff_and_recovers() {
  Channel c; ChannelParams p; c.configure(p); SimFan f; f.blocked = true; uint32_t now = 0;
  c.setSpeed(60);
  run(c, f, now, 10000);
  TEST_ASSERT_EQUAL(State::Fault, c.state());
  f.blocked = false;                        // the obstruction is gone
  run(c, f, now, 30000);                    // retry (15 s) must pick it up
  TEST_ASSERT_EQUAL(State::Run, c.state());
  TEST_ASSERT_FALSE(c.fault());
}

void test_retry_backoff_doubles_and_caps() {
  ChannelParams p; p.retryMs = 1000; p.retryMaxMs = 4000; p.spinTimeoutMs = 100;
  Channel c; c.configure(p); SimFan f; f.blocked = true; uint32_t now = 0;
  c.setSpeed(100);
  // Count spin-up attempts over 60 s: with 1,2,4,4,4... s backoff plus ~6 s search
  // each, a doubling+cap scheme gives clearly fewer attempts than a flat 1 s retry.
  int attempts = 0; State last = c.state();
  for (int i = 0; i < 3000; i++) {
    run(c, f, now, 20);
    if (c.state() == State::Spinup && last != State::Spinup) attempts++;
    last = c.state();
  }
  TEST_ASSERT_TRUE(attempts >= 3);
  TEST_ASSERT_TRUE(attempts <= 10);
}

void test_switching_off_clears_fault() {
  Channel c; c.configure(ChannelParams{}); SimFan f; f.blocked = true; uint32_t now = 0;
  c.setSpeed(40); run(c, f, now, 10000);
  TEST_ASSERT_TRUE(c.fault());
  c.setSpeed(0); run(c, f, now, 100);
  TEST_ASSERT_FALSE(c.fault());
  TEST_ASSERT_EQUAL(State::Off, c.state());
}

void test_running_fan_that_stops_is_detected() {
  Channel c; c.configure(ChannelParams{}); SimFan f; uint32_t now = 0;
  c.setSpeed(50); run(c, f, now, 15000);
  TEST_ASSERT_EQUAL(State::Run, c.state());
  f.blocked = true;  // somebody sticks a finger in
  run(c, f, now, 6000);
  TEST_ASSERT_EQUAL(State::Fault, c.state());
  TEST_ASSERT_TRUE(c.fault());
}

void test_already_turning_fan_starts_quietly() {
  // After a fault retry or a quick off/on the fan still coasts: edges arrive at once,
  // so the search ends at the start duty instead of climbing.
  Channel c; c.configure(ChannelParams{}); SimFan f; f.turning = true; f.holdDuty = 5; uint32_t now = 0;
  c.setSpeed(30);
  float peak = 0;
  for (int i = 0; i < 100; i++) { run(c, f, now, 20); if (c.duty() > peak) peak = c.duty(); }
  TEST_ASSERT_EQUAL(State::Run, c.state());
  TEST_ASSERT_TRUE(peak <= c.targetDuty() + 0.5f);
}

void test_blind_mode_kicks_then_settles_without_tach() {
  ChannelParams p; p.tach = false; Channel c; c.configure(p); uint32_t now = 0;
  c.setSpeed(10);  // target 28 %, kick 50 %
  float peak = 0;
  for (int i = 0; i < 1000; i++) { now += 20; c.update(now, 0); if (c.duty() > peak) peak = c.duty(); }
  TEST_ASSERT_EQUAL(State::Run, c.state());
  TEST_ASSERT_FALSE(c.fault());
  TEST_ASSERT_FLOAT_WITHIN(0.5, 50.0, peak);
  TEST_ASSERT_FLOAT_WITHIN(0.5, c.targetDuty(), c.duty());
}

void test_late_tick_does_not_jump() {
  Channel c; c.configure(ChannelParams{}); SimFan f; uint32_t now = 0;
  c.setSpeed(100); c.update(now, 0);
  now += 5000;                       // loop stalled for 5 s
  c.update(now, 0);
  TEST_ASSERT_TRUE(c.duty() < 25.0f);
}

void test_millis_wrap() {
  Channel c; c.configure(ChannelParams{}); SimFan f; uint32_t now = 0xFFFFFF00u;
  c.setSpeed(40);
  run(c, f, now, 15000);             // crosses the 32-bit wrap
  TEST_ASSERT_EQUAL(State::Run, c.state());
  TEST_ASSERT_FALSE(c.fault());
}

void test_rpm_meter() {
  RpmMeter m;
  m.addWindow(0, 0, 0, 1000000);
  TEST_ASSERT_EQUAL(0, m.rpm());
  // 1200 rpm, 2 ppr -> 40 edges/s -> 25 ms apart; 40 edges in 1 s: span 39*25000 µs
  m.addWindow(40, 1000, 1000 + 39 * 25000, 1000000);
  TEST_ASSERT_UINT16_WITHIN(2, 1200, m.rpm());
  // slow fan: 300 rpm = 10 edges/s -> 100 ms apart; 10 edges
  m.addWindow(10, 500, 500 + 9 * 100000, 1000000);
  TEST_ASSERT_UINT16_WITHIN(2, 300, m.rpm());
  // 4 ppr
  m.setPulsesPerRev(4);
  m.addWindow(40, 0, 39 * 25000, 1000000);
  TEST_ASSERT_UINT16_WITHIN(2, 600, m.rpm());
}

void test_rpm_meter_wraps_and_single_edge() {
  RpmMeter m;
  m.addWindow(11, 0xFFFFFF00u, 0xFFFFFF00u + 10 * 100000u, 1000000);  // µs counter wraps
  TEST_ASSERT_UINT16_WITHIN(2, 300, m.rpm());
  m.addWindow(1, 1, 1, 1000000);
  TEST_ASSERT_TRUE(m.rpm() > 0 && m.rpm() <= 30);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_duty_mapping);
  RUN_TEST(test_starts_from_low_duty_and_stays_below_kick);
  RUN_TEST(test_first_duty_is_gentle);
  RUN_TEST(test_start_duty_never_above_target);
  RUN_TEST(test_spinup_detects_turning_and_slews_down_after);
  RUN_TEST(test_slew_limits);
  RUN_TEST(test_off_ramps_down_then_cuts);
  RUN_TEST(test_blocked_fan_faults_and_stops_driving);
  RUN_TEST(test_fault_retries_with_backoff_and_recovers);
  RUN_TEST(test_retry_backoff_doubles_and_caps);
  RUN_TEST(test_switching_off_clears_fault);
  RUN_TEST(test_running_fan_that_stops_is_detected);
  RUN_TEST(test_already_turning_fan_starts_quietly);
  RUN_TEST(test_blind_mode_kicks_then_settles_without_tach);
  RUN_TEST(test_late_tick_does_not_jump);
  RUN_TEST(test_millis_wrap);
  RUN_TEST(test_rpm_meter);
  RUN_TEST(test_rpm_meter_wraps_and_single_edge);
  return UNITY_END();
}
