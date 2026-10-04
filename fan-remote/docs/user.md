# fan-remote — user guide

## The web page

Open `http://fan-xxxxxx.local/` (the id is on the board's serial output and in the
router's device list) or the board's IP. Works on phones and desktops, light and
dark, German or English following the browser language.

Every enabled fan has a card:

| Element | Meaning |
|---|---|
| Spinning fan icon | Turns with the measured RPM; grey = off, red = stalled |
| Big number | RPM from the tach line (`–` if the fan has no tach) |
| Round power button | Off, or back to the last non-zero speed |
| Slider | Speed 0…100. `0` is off, `1` is the quietest speed that really runs, `100` the maximum |
| `PWM n %` | The duty actually sent to the fan right now (it follows the slider smoothly) |
| Chips | Preset speeds: Quiet, Low, Medium, High, Max. The matching one is lit |

The **All fans** card at the top sets every enabled fan at once.

### Soft start

Switching a fan on never jumps to a high speed. The duty rises slowly until the fan
turns, then settles at the target. Do not be surprised that "Starting" lasts a
second or two at low speeds: that is how it stays quiet. If a fan does not turn up
to 50 % duty for three seconds, it is switched off and flagged **Stalled**; the
board retries after 15 s, then 30 s, up to every 5 min. Moving the slider to 0
acknowledges the fault.

### Settings (gear icon)

Asks for the admin login (user `admin`). Everything is stored on the board.

* **Fans**: name, enabled, *Min* and *Max* duty, tach wired, pulses per revolution
  (PC fans: 2). Set *Min* to the lowest duty at which your fan still turns reliably
  (20 % is typical for PWM fans; try 10–30). *Max* caps the loudest setting.
* **Preset speeds**: the five chips, in speed units (not duty).
* **Behaviour**: how fast the duty may rise/fall, and what happens after power-up
  (restore last speeds, or all off).
* **Network**: broker, syslog, NTP, admin password. Applies after a reboot.

## Home Assistant

With MQTT discovery enabled (default) every board appears as a device with one *fan*
per enabled channel (on/off, percentage, preset modes), an *RPM* sensor, a *stalled*
problem sensor, plus WiFi signal and uptime. Entities appear within seconds of the
board connecting to the broker. A fan entity at `0 %` is off; HA's percentage is the
same 1…100 speed as the slider.

## MQTT

Topics are `fans/<id>/…`; the full list is in [spec.md](spec.md). Examples:

```sh
mosquitto_pub -h mqtt -t fans/fan-a1b2c3/1/speed/set  -m 35        # fan 1 to speed 35
mosquitto_pub -h mqtt -t fans/fan-a1b2c3/all/preset/set -m quiet   # everything quiet
mosquitto_pub -h mqtt -t fans/fan-a1b2c3/2/power/set  -m OFF
mosquitto_sub -h mqtt -t 'fans/fan-a1b2c3/#' -v
```

## HTTP

```sh
curl http://fan-a1b2c3.local/api/state
curl -d ch=1 -d speed=40 http://fan-a1b2c3.local/api/set
curl -d ch=all -d preset=quiet http://fan-a1b2c3.local/api/set
curl http://fan-a1b2c3.local/api/netstatus
```
