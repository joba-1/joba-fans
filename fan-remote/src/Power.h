// Power.h — standby power saving. Full power (CPU clock up, WiFi awake) for a minute after
// any user interaction, then WiFi modem sleep and a lower CPU clock.
// The fans do not care: their PWM timer runs from the 80 MHz APB clock, which CPU clocks
// of 80 MHz and above leave alone (checked at runtime: /api/netstatus reports pwmHz).
#pragma once
#include <Arduino.h>

void powerBegin();
void powerActivity();      // call on every user interaction; safe from any task
void powerLoop();          // call from loop()
bool powerIdle();
uint32_t powerCpuMhz();
uint32_t powerIdleInS();   // seconds until standby, 0 when already there
