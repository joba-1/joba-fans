# fan-remote — firmware for the 4-channel fan controller

Firmware for the XIAO ESP32-C3 on the `fan-controller` board (see `../README.md`).
One board drives up to four 4-pin PC fans. Several boards run side by side.

## Goals

1. Drive four fans with 25 kHz PWM and read back their RPM from the tach lines.
2. A one-page web remote: live RPM, on/off, preset speeds, a free slider, per
   fan and for all fans at once. Responsive, phone first.
3. **Safe and quiet switch-on**, also at low speeds (see "Fan control").
4. MQTT control and state, with Home Assistant MQTT discovery.
5. Any number of boards without per-board builds: one image, identity from the MAC.

Non-goals: temperature control loops (that lives in Home Assistant / the heat-pump
tooling and talks to the fans over MQTT), cloud access, BLE.

## Hardware facts the firmware depends on

Verified against `fan-controller.kicad_pcb`, not just the net plan:

| Fan | PWM (via 1 kΩ) | Tach (330 Ω, 10 kΩ pull-up to 3V3) |
|---|---|---|
| FAN1 | D1 = GPIO3 | D2 = GPIO4 |
| FAN2 | D3 = GPIO5 | D4 = GPIO6 |
| FAN3 | D7 = GPIO20 | D10 = GPIO10 |
| FAN4 | D6 = GPIO21 | D5 = GPIO7 |

* The PWM output is a 3.3 V push-pull signal straight into the fan's PWM pin
  (Intel 4-wire spec: 25 kHz, 100 % duty = full speed, **not inverted**).
* There is no pull-down on the PWM lines. While the ESP32 resets (power-up, OTA
  reboot, watchdog) the pins float and the fan's own pull-up asks for full
  speed. The firmware drives the pins low as the very first thing in `setup()`,
  but the first ~0.3 s after a reset can still be a short burst. Not fixable in
  firmware; a 10 kΩ pull-down per line would be a board change.
* D6/D7 are the UART0 pins. The console is USB-CDC, so UART0 is unused, but the
  ROM boot log shows up as a few ms of noise on FAN4's PWM line.
* The ESP32-C3 has no PCNT unit; tach edges are counted in a GPIO interrupt.

## Architecture

```text
 web UI (SSE + REST) ─┐
 MQTT / HA discovery ─┼─> Fans (mutex) ──> FanCore::Channel x4 ──> LEDC PWM 25 kHz
 ArduinoOTA, syslog   ┘        ▲                                       │
                               └── tach ISR (edge count + timestamps) ◄┘ fans
```

* **`lib/FanCore`** — pure C++, no Arduino includes: the per-channel state machine
  (`Channel`), speed→duty mapping and the RPM estimator (`RpmMeter`). Tested on the
  PC (`pio test -e native`).
* **`src/Fans`** — owns the pins, the ISRs and a **dedicated FreeRTOS task** (20 ms
  tick, priority above `loop()`). *Decision:* fan control never shares a thread with
  WiFi, MQTT or the web server, so a blocked connect (WiFiManager, DNS, a slow TLS-less
  TCP timeout) can never freeze a ramp half-way. The network code only calls
  `setSpeed()` and reads snapshots.
* **`src/Settings`** — everything persistent lives in NVS (`Preferences`): identity,
  network targets, per-fan limits, presets, last speeds.
* **`src/Web`** — `ESPAsyncWebServer`; the page is one gzip-compressed HTML file
  embedded in the firmware image (`web/index.html`), so an OTA update is one
  artifact and there is no separate filesystem upload.
* **`src/Mqtt`** — `PubSubClient`, LWT, retained state, HA discovery.
* **`src/NetLog`** — Serial plus UDP syslog (RFC 3164) to the alias `syslog`.

### Decisions and reasons

| Decision | Why |
|---|---|
| Arduino + PlatformIO, not ESPHome | Same toolchain and libraries as `Joba_Modbus`; the custom web UI and the spin-up logic would fight ESPHome's component model. |
| Fan task independent of the network | Safety: fans keep their last speed with no WiFi, no broker, no browser. |
| Speed 1…100 maps onto the *usable* duty range `[min, max]` per fan | "1 %" is the quietest speed that really runs; HA's percentage slider has no dead zone below the stall point. `0` is off. |
| Presets stored as speeds, edited in the UI | Fans differ; "Low" should be what the user finds quiet, not a fixed number. |
| Channel numbers 1…4 in topics and the UI | Matches the silkscreen (FAN1…FAN4). |
| Device id = `fan-` + last 3 MAC bytes, never changes | Stable MQTT topics and HA unique ids; the friendly name is separate and renameable. |
| Control endpoints open on the LAN, settings behind Basic auth | The remote must work from any phone without a login dance. `protectControl` turns the login on for control as well. Deviation from "UI needs auth" is limited to the LAN-only case. |

## Fan control

### Speed model

`speed` (user) 0…100. `0` = off. Otherwise `duty = min + (max − min) · speed / 100`
with per-fan `min` (lowest duty that keeps the fan turning, default 20 %) and `max`
(noise cap, default 100 %).

### Safe, quiet start

A fan standing still needs more torque to start than to keep running. A fixed
"kick to 100 %" is loud; starting at the target duty may never start. The firmware
searches instead:

1. Off → on: start at `startPct` (default 15 %, but never above the target) and
   raise the duty slowly (`spinupPctS`, default 8 %/s).
2. The moment the tach shows rotation (4 edges = 2 revolutions) the fan is **running**;
   the duty then slews to the target. Usually that is the quietest possible start
   and the fan never sees more duty than it needed.
3. The ramp is capped at `kickPct` (default 50 %, or the target if higher). If the
   cap is held for `spinTimeoutMs` without a tach edge, the fan is declared
   **stalled**: PWM goes to 0, the fault is reported (web, MQTT, HA) and a retry
   follows after 15 s, doubling to at most 5 min. A blocked or unplugged fan is
   therefore never driven hard indefinitely.
4. Fans without a usable tach signal (`tach = off`): there is nothing to detect, so
   the duty rises to `kickPct` (or target), holds for `blindKickMs`, then slews down.
5. While running, no tach edge for `stallMs` (5 s) while the target is above 0
   is the same fault → the same recovery.

All speed changes are slew-limited (`rampUpPctS` 10 %/s, `rampDownPctS` 20 %/s):
no sudden pitch changes in a living room. Turning off ramps down, then cuts the PWM.

### RPM

Falling edges are counted in the ISR (glitches closer than 1.5 ms are ignored);
the ISR also stores the timestamp of the first and last edge of each 1 s window.
`rpm = (edges − 1) · 60 s / (span · pulsesPerRev)`. That is accurate at 300 rpm
(10 edges/s), where plain edge counting would be ±10 %.

### Persistence

The target speed per fan is written to NVS 5 s after the last change and restored
at boot (`bootMode`: `last` or `off`, default `last`). The restore goes through the
normal soft start.

## Interfaces

### Web

| Route | Auth | |
|---|---|---|
| `GET /` | – | the page |
| `GET /events` | – | SSE: `state` event (full state JSON) on every change and each second |
| `GET /api/state` | – | same JSON once |
| `POST /api/set` | optional | `ch=1..4|all`, plus `speed=0..100` **or** `preset=<id>` **or** `power=on|off` |
| `GET /api/config`, `POST /api/config` | Basic | per-fan limits and names, presets, ramps, bootMode, protectControl |
| `GET /api/netstatus` | – | firmware, version, build date, hostname, IP, SSID, RSSI, every external resource with host, last status, last access |
| `POST /api/netconfig` | Basic | `name`, `mqttHost`, `mqttPort`, `mqttUser`, `mqttPass`, `syslogHost`, `ntpHost`, `defaults=1`; stored in NVS, applied at next boot |
| `POST /api/reboot`, `POST /api/wifireset` | Basic | |

`netstatus` / `netconfig` follow the reference in `Joba_Modbus` (CodingStandards §2).

### MQTT

Base `fans/<id>` (prefix configurable at build time). `<n>` is 1…4.

| Topic | Dir | Payload |
|---|---|---|
| `fans/<id>/status` | pub, retained, LWT | `online` / `offline` |
| `fans/<id>/<n>/speed/state` | pub, retained | `0…100` |
| `fans/<id>/<n>/speed/set` | sub | `0…100` |
| `fans/<id>/<n>/power/state`, `…/power/set` | pub / sub | `ON` / `OFF` (ON restores the last non-zero speed) |
| `fans/<id>/<n>/preset/state`, `…/preset/set` | pub / sub | preset id, or `None` |
| `fans/<id>/<n>/rpm` | pub | integer rpm, on change ≥ 10 rpm or every 30 s |
| `fans/<id>/<n>/fault` | pub, retained | `ON` / `OFF` (stalled) |
| `fans/<id>/all/speed/set`, `…/all/preset/set` | sub | all fans |
| `fans/<id>/info` | pub, retained | JSON: version, ip, rssi, uptime |

Home Assistant discovery (`homeassistant/…`, retained, re-sent on every connect):
one `fan` per enabled channel (on/off, percentage 1…100, preset modes), a `sensor`
(rpm) and a `binary_sensor` (problem) per channel, diagnostic sensors for RSSI and
uptime. All entities share one HA *device* per board.

Credentials for the broker are stored in NVS, never in the repo.

## Safety / security

* Fans keep running on loss of WiFi / MQTT; the fan task has no network dependency.
* Task watchdog on; a stuck fan task reboots the board (fans then float → full speed
  briefly, see above; acceptable against a hung controller).
* All inputs validated (ranges, enum values, string lengths); no `String` building
  from request data into responses without JSON escaping (ArduinoJson).
* Settings, OTA and reboot need the admin password (Basic auth, constant-time
  compare). OTA is password protected. No credentials in the repository:
  `config.ini` is gitignored, the template carries placeholders.
* MQTT commands can change speeds only — never network targets (CodingStandards §2).

## Open points / future

* A pull-down on the PWM lines (board revision) to make reset quiet.
* Temperature-driven control belongs in HA; a simple "fan follows sensor X" blueprint
  can be added to `docs/` once real fans have been measured.
