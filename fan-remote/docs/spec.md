# fan-remote — firmware for the 4-channel fan controller

Firmware for the XIAO ESP32-C3 on the `fan-controller` board (see [`../fan-controller/README.md`](../../fan-controller/README.md)).
One board drives up to four 4-pin PC fans. Several boards run side by side.

## Goals

1. Drive four fans with 25 kHz PWM and read back their RPM from the tach lines.
2. A one-page web remote: live RPM, on/off, preset speeds, a free slider, per
   fan and for all fans at once. Responsive, phone first.
3. **Safe and quiet switch-on**, also at low speeds (see "Fan control").
4. MQTT control and state, with Home Assistant MQTT discovery.
5. Any number of boards without per-board builds: one image, identity from `devices.csv` (MAC → number).
6. Low power in standby: full power for a minute after any interaction, then WiFi modem sleep and a lower CPU clock.

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
| Arduino + PlatformIO, not ESPHome | Plain Arduino-ESP32 code and libraries; the custom web UI and the spin-up logic would fight ESPHome's component model. |
| Fan task independent of the network | Safety: fans keep their last speed with no WiFi, no broker, no browser. |
| Speed 1…100 maps onto the *usable* duty range `[min, max]` per fan | "1 %" is the quietest speed that really runs; HA's percentage slider has no dead zone below the stall point. `0` is off. |
| Presets stored as speeds, edited in the UI | Fans differ; "Low" should be what the user finds quiet, not a fixed number. |
| Channel numbers 1…4 in topics and the UI | Matches the silkscreen (FAN1…FAN4). |
| Device id = `fan-control-N`, N from `devices.csv` (MAC → number), never reused | Readable, stable MQTT topics and HA unique ids instead of MAC digits; the friendly name is separate and renameable. An unregistered board runs as `fan-control-new-xxxxxx` so it is still unique and recognisable. |
| Friendly name starts as the id (`fan-control-N`); a fan without a name of its own has an empty name | The page labels it "Fan N" or "Lüfter N" by browser language, Home Assistant "Fan N". No language is baked into the stored data. |
| One admin password per build tree (random, in the gitignored `config.ini`) for settings, AP and OTA | Home network: a per-board secret to look up is more trouble than protection. Still HTTP Basic with a constant-time compare and a lockout; changeable per board via `/api/netconfig`. |
| Control endpoints open on the LAN, settings behind Basic auth | The remote must work from any phone without a login dance. `protectControl` turns the login on for control as well. Deviation from "UI needs auth" is limited to the LAN-only case. |

## Fan control

### Speed model

`speed` (user) 0…100. `0` = off. Otherwise `duty = min + (max − min) · speed / 100`
with per-fan `min` (lowest duty that keeps the fan turning, default 5 %) and `max`
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

### Web feedback

Input is acknowledged at once but never guessed: the control that was used gets a
"pending" marker (pulsing chip, spinner on the power button, dimmed number with a dot on
the slider). Speed, badge, RPM and the lit preset chip change only when the controller
reports them; the marker clears when the reported speed matches the request, or after 3 s
with a hint. The slider sends its first value immediately, then at most every 120 ms.

### Standby power saving

`power_save = 1` (default). Any user interaction (page load, command, settings, HA/MQTT
command, OTA, the page's `/api/wake` on touch) means **active**: CPU 160 MHz, WiFi awake.
`idle_seconds` (60) after the last one the board goes to **standby**: WiFi modem sleep,
CPU 80 MHz. It stays active while the setup portal is open or WiFi is down. Measured on
the bench board: active answers in 1…5 ms; in standby pings average ≈ 115 ms, and the
page's wake request (sent when a finger touches it) absorbs that, so the command that
follows takes ≈ 13 ms.

The floor is 80 MHz: WiFi needs it, and the LEDC PWM timer runs from the 80 MHz APB clock,
which CPU clocks ≥ 80 MHz leave alone. Checked on the C6 with a fan running: the PWM stays
at 25 000 Hz and the RPM does not change across the switch (`/api/netstatus` → `power.pwmHz`).
Not checked on a C3 yet. Fan control is not interaction: a running fan alone does not keep
the board awake. `power_save = 0` keeps full power always.

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
| `GET /api/netstatus` | – | firmware, version, build date, hostname, IP, SSID, RSSI, heap (`freeHeap`, `minFreeHeap`, `maxAllocHeap`), stack left per task (`stackLeft`: lowest free bytes ever of `async_tcp`, `loopTask`, `fans`), every external resource with host, last status, last access |
| `POST /api/netconfig` | Basic | `name`, `mqttHost`, `mqttPort`, `mqttUser`, `mqttPass`, `syslogHost`, `ntpHost`, `defaults=1`; stored in NVS, applied at next boot |
| `POST /api/update` | Basic | firmware image (multipart field `firmware`); written to the next OTA slot, validated, then reboot. The host connects out to port 80: no host firewall port needed (ArduinoOTA remains as a fallback) |
| `POST /api/discovery` | Basic | resend the Home Assistant discovery; `recreate=1` first removes the old entities and announces new ones under generation + 1 (unique ids and discovery topics carry `_gN`), so entity ids are rebuilt from the current names |
| `GET /api/wake` | – | the page sends it on touch; counts as an interaction and wakes the board from standby |
| `POST /api/reboot`, `POST /api/wifireset` | Basic | |

`netstatus` / `netconfig` give every external resource (broker, syslog, NTP) a host, a last status and a last access time, and keep the settings editable at run time.

### MQTT

Base `fan-control/<id>` (prefix configurable at build time). `<n>` is 1…4.

| Topic | Dir | Payload |
|---|---|---|
| `fan-control/<id>/status` | pub, retained, LWT | `online` / `offline` |
| `fan-control/<id>/<n>/speed/state` | pub, retained | `0…100` |
| `fan-control/<id>/<n>/speed/set` | sub | `0…100` |
| `fan-control/<id>/<n>/power/state`, `…/power/set` | pub / sub | `ON` / `OFF` (ON restores the last non-zero speed) |
| `fan-control/<id>/<n>/preset/state`, `…/preset/set` | pub / sub | preset id, or `None` |
| `fan-control/<id>/<n>/rpm` | pub | integer rpm, on change ≥ 10 rpm or every 30 s |
| `fan-control/<id>/<n>/fault` | pub, retained | `ON` / `OFF` (stalled) |
| `fan-control/<id>/all/speed/set`, `…/all/preset/set` | sub | all fans |
| `fan-control/<id>/info` | pub, retained | JSON: version, ip, rssi, uptime |

Home Assistant discovery (`homeassistant/…`, retained, re-sent on every connect):
one `fan` per enabled channel (on/off, percentage 1…100, preset modes), a `number` "speed"
slider (0…100 %, step 1, same topics as the fan's percentage), a `sensor`
(rpm) and a `binary_sensor` (problem) per channel, diagnostic sensors for RSSI and
uptime. All entities share one HA *device* per board.

Entity ids: Home Assistant restores the old entity id for a returning unique id (tested on 2026.9:
clearing and re-announcing, as Zigbee2MQTT's `homeassistant_rename` does, changes nothing). So the
unique ids carry a generation (`haGen` in NVS, 0 = plain ids); `/api/discovery?recreate=1` bumps it,
clears the old topics, waits 2.5 s (otherwise HA creates `_2` entities) and announces the new ones.

Credentials for the broker are stored in NVS, never in the repo.

## Safety / security

* Fans keep running on loss of WiFi / MQTT; the fan task has no network dependency.
* Task watchdog on; a stuck fan task reboots the board (fans then float → full speed
  briefly, see above; acceptable against a hung controller).
* All inputs validated (ranges, enum values, string lengths); no `String` building
  from request data into responses without JSON escaping (ArduinoJson).
* Settings, OTA and reboot need the admin password (Basic auth, constant-time compare; by default
  the random one from `config.ini`). OTA is password protected. No credentials in the repository:
  `config.ini` is gitignored, the template carries a placeholder that the first build replaces.
* MQTT commands can change speeds only — never network targets.

## Open points / future

* A pull-down on the PWM lines (board revision) to make reset quiet.
* Temperature-driven control belongs in HA; a simple "fan follows sensor X" blueprint
  can be added to `docs/` once real fans have been measured.

## Status LED and health

Optional; a build without `LED_FAN_PIN` has no LED code path. Pins and polarity are build flags in
`platformio.ini`: `LED_FAN_PIN` (+ `LED_ALERT_PIN` for a second LED) and `LED_ACTIVE_LOW`. The XIAO
ESP32-C6 build drives its yellow user LED (GPIO15, active low); the red LED beside it is the battery charge
indicator and is not under software control. The C3 build points at D8, the pin the housing README suggests
for a retrofitted LED (harmless without one).

**Health** is a bit mask (`netstatus.health`): a stalled fan, no WiFi, no MQTT (only if a broker is
configured), clock not synchronised. 0 = healthy.

| LEDs | Pattern |
|---|---|
| one | fans off, healthy: dark · fans on, healthy: steady · fans off, problem: 100 ms flash once a second · fans on, problem: blinking 2 Hz |
| two | first LED: fans on · second LED: problem |

**Brightness** is PWM (1 kHz, 10 bit), in percent: `ledDay` by day, `ledNight` at night (defaults 30 % and 5 %),
night = local hours `nightFrom`..`nightTo` (default 22..7, wraps over midnight). `ledMode` 0 switches the LED off
completely (dark operation). Without a synchronised clock it is always day. All of it is in `/api/config`
(`led`) and the settings dialog; defaults come from `config.ini`. The pure logic (night window, brightness,
patterns, health mask) is in `FanCore` and unit tested.

## Web page colour

The base hue of the page comes from the device number (`fan-control-N`, read from the host name first and
from the state's id after that): eight hues between blue and violet (190, 245, 285, 215, 265, 205, 295, 230°),
wrapping for N > 8. Red and green are the signal colours of the page (problem / ok) and stay fixed; the hue set
keeps clear of both. Board 1 keeps the original blue.

## Stack and heap budget

Measured on the real board with `/api/netstatus` (`stackLeft` is the lowest free stack since boot), after
state/config reads, a settings save, a Home Assistant discovery resend and a rejected firmware upload:

| Task | Stack | Lowest free | Used at most |
|---|---|---|---|
| `async_tcp` (all web handlers) | 16 384 B | 13 076 B | ~3.3 KB |
| `loopTask` (WiFi, MQTT, power) | 8 192 B | 5 216 B | ~3.0 KB |
| `fans` | 6 144 B | 5 740 B | ~0.4 KB |

Heap: about 278 KB free, lowest 253 KB since boot, largest allocatable block 245 KB. Re-check after
changes to the handlers or the discovery code (`curl http://fan-control-1/api/netstatus`).
