# fan-remote — test plan

## Automated (no hardware)

```sh
pio test -e native
```

`lib/FanCore` is hardware-free and covered by 22 Unity tests: speed→duty mapping,
gentle first duty, start duty never above target, spin detection then slew, slew
limits, ramp-down then cut, blocked fan → fault without exceeding the ceiling,
retry with doubling/capped backoff and recovery, off clears the fault, a running
fan that stops, an already-turning fan, blind (no tach) mode, late ticks, `millis()`
wrap, RPM estimation (including 4 ppr, µs wrap, single-edge window), the MAC → number table
lookup and id format, and the standby policy (timeout, forced active, wake, `millis()` wrap).

The page is exercised against `scripts/mock_server.py` (see below). Run before every commit:
unit tests green, `pio run -e xiao_c3` without warnings.

## Web page against the mock

```sh
python3 scripts/mock_server.py 18099     # then open http://localhost:18099/
```

Check: phone width (≈390 px) and desktop; light and dark; German and English
(browser language); chip, slider drag, power button, all-fans card, stalled card;
settings dialog and save; no console errors.

## Hardware bring-up (once per board design, then spot checks)

Not covered by the automated tests; run with a scope or logic analyser and a real fan.

| # | Step | Expect |
|---|---|---|
| 1 | Flash over USB-C, open serial | `fan-remote <version>`; portal AP appears |
| 2 | Scope on FAN1 PWM, speed 50 | 25 kHz, 3.3 V, duty = `min + (max−min)·0.5` |
| 3 | Fan connected, speed 1 from standstill | slow duty rise; `Starting` → `Running`; no 100 % burst |
| 4 | Compare RPM with the fan's datasheet / a second tach reading | within a few % at 30, 60, 100 % |
| 5 | Tach unplugged, speed 50 | Stalled after ≈ 8 s (ramp + 3 s hold), PWM 0, retry in 15 s |
| 6 | Hold the rotor | Stalled within 5 s; release → recovers on retry |
| 7 | Unplug WiFi/router while running | fan unchanged; reconnects later |
| 8 | Reset the board while a fan runs | note the burst length (documents the PWM floating issue) |
| 9 | MQTT: set speed/preset/power, watch retained state | topics as in spec.md; HA entities appear |
| 10 | OTA update | succeeds; settings and last speeds survive |
| 11 | Two boards | separate ids, two HA devices, no topic clashes |
| 12 | Find each fan's real *Min* | lowest duty that keeps it turning from a *running* state; set it in settings |

Done on the bench C6 with a fan on FAN1 (2026-10-04): steps 1, 3 (soft start observed, rpm ≈ 800
at speed 10), 9 (topics, HA entities), 10 (OTA, several times), plus standby: after 60 s
`power.mode` switches to `standby` at 80 MHz, PWM stays 25 000 Hz and the fan RPM is unchanged;
a wake request brings it back to 160 MHz and the next command takes ≈ 13 ms.

Status of this list: steps 2, 4–8, 11 and 12 are still open (the board has not been
tried on the fan PCB, and no scope was used).
