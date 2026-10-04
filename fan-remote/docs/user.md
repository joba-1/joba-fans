# fan-remote — user guide

## The web page

Open `http://fan-control-N.local/` (N is the number from `devices.csv`; also on the serial output and in the
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

### Standby

After a minute without any interaction the controller saves power (WiFi modem sleep, lower
CPU clock); the fans are not affected. The first touch after a pause wakes it: the page
shows the usual pending marker for a fraction of a second longer. Settings → Status shows
the current mode.

### Soft start

Switching a fan on never jumps to a high speed. The duty rises slowly until the fan
turns, then settles at the target. Do not be surprised that "Starting" lasts a
second or two at low speeds: that is how it stays quiet. If a fan does not turn up
to 50 % duty for three seconds, it is switched off and flagged **Stalled**; the
board retries after 15 s, then 30 s, up to every 5 min. Moving the slider to 0
acknowledges the fault.

### Settings (gear icon)

Asks for the admin login (user `admin`). Everything is stored on the board. Nothing is saved
automatically: a section with unsaved edits shows a dot in the dialog title, "Unsaved changes" next
to its **Save** button, and the button turns solid; changing a value back removes the marker, and
closing with unsaved edits asks first. **Save** covers name, fans, presets and behaviour (applies at
once), **Save network** the broker, syslog and NTP (applies after a reboot).

* **Fans**: name (empty = "Fan N" / "Lüfter N"), enabled, *Min* and *Max* duty, tach wired, pulses per revolution
  (PC fans: 2). Set *Min* to the lowest duty at which your fan still turns reliably
  (default 5 %; many PWM fans keep turning at that, some stall below 15–20 %, so raise it if a card turns "Stalled" at low speeds). *Max* caps the loudest setting.
* **Preset speeds**: the five chips, in speed units (not duty).
* **Behaviour**: how fast the duty may rise/fall, and what happens after power-up
  (restore last speeds, or all off).
* **Network**: broker, syslog, NTP. Applies after a reboot. The login is user `admin`, password `<admin password>`.

## Home Assistant

With MQTT discovery enabled (default) every board appears as a device with one *fan*
per enabled channel (on/off, percentage, preset modes), a **Speed** slider (0–100 %, 1 % steps,
a plain number entity that shows up on the device page and in default dashboards), an *RPM* sensor, a *stalled*
problem sensor, plus WiFi signal and uptime. Entities appear within seconds of the
board connecting to the broker. A fan entity at `0 %` is off; HA's percentage is the
same 1…100 speed as the slider.

Renaming the board or a fan in the settings updates the names in Home Assistant at once. The
**entity ids** stay as they were when the entities were first created: Home Assistant remembers deleted
entities and gives a returning unique id its old entity id back (tested with HA 2026.9: removing
and re-announcing the discovery messages, as Zigbee2MQTT's `homeassistant_rename` does, restored
the old ids). To get new ids from the current names use Settings → Network → **Recreate Home
Assistant entities** (or `curl -u admin:… -d recreate=1 http://fan-control-1.local/api/discovery`):
the board removes its entities in Home Assistant, waits 2.5 s and announces them again under a new
generation number, so HA builds fresh entity ids. History and customisations of the old entities
are lost, so use it right after naming a new board, not later.

## MQTT

Topics are `fan-control/<id>/…`; the full list is in [spec.md](spec.md). Examples:

```sh
mosquitto_pub -h mqtt -t fan-control/fan-control-1/1/speed/set  -m 35        # fan 1 to speed 35
mosquitto_pub -h mqtt -t fan-control/fan-control-1/all/preset/set -m quiet   # everything quiet
mosquitto_pub -h mqtt -t fan-control/fan-control-1/2/power/set  -m OFF
mosquitto_sub -h mqtt -t 'fan-control/fan-control-1/#' -v
```

## HTTP

```sh
curl http://fan-control-1.local/api/state
curl -d ch=1 -d speed=40 http://fan-control-1.local/api/set
curl -d ch=all -d preset=quiet http://fan-control-1.local/api/set
curl http://fan-control-1.local/api/netstatus
```
