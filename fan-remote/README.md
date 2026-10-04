# fan-remote

Firmware for the four-channel fan controller in `../fan-controller/` (XIAO ESP32-C3).
One board drives four 4-pin PC fans with 25 kHz PWM and reads their RPM.

* **Web remote** on every board (`http://fan-xxxxxx.local/`): live RPM, on/off, preset
  speeds, a free slider, per fan and for all fans. Phone first, German and English.
* **Safe, quiet start.** The duty is raised slowly until the tach shows the fan
  turning, then slewed to the target; a blocked fan is detected and retried with
  backoff instead of being driven hard.
* **MQTT** with **Home Assistant discovery**; any number of boards, one image.
* Fans keep running without WiFi, broker or browser: control runs in its own task.

```text
docs/spec.md    architecture, decisions and their reasons, topic reference
docs/user.md    using the web page and Home Assistant
docs/admin.md   building, flashing, provisioning, operations, troubleshooting
docs/test.md    test plan and the hardware bring-up checklist
```

## Quick start

```sh
~/.platformio/penv/bin/pio test -e native      # unit tests, no hardware
~/.platformio/penv/bin/pio run -e xiao_c3 -t upload   # first flash over USB-C
```

The first build creates `config.ini` (gitignored) with a random admin password.
A fresh board opens the access point `fan-xxxxxx-setup` (password: that admin
password); join it and enter WiFi, name and broker. Later updates go over WiFi:

```sh
pio run -e ota -t upload --upload-port fan-a1b2c3.local
```

Details in [docs/admin.md](docs/admin.md).

## Layout

| Path | |
|---|---|
| `lib/FanCore/` | hardware-free logic (state machine, speed mapping, RPM): unit tested |
| `src/` | firmware: `Fans` (PWM, tach, task), `Web`, `Mqtt`, `Net`, `NetLog`, `Settings` |
| `web/` | the page (`index.html`, gzipped and embedded at build time) and `logo.svg` |
| `scripts/mock_server.py` | fake device API to work on the page without hardware |
| `test/` | Unity tests |
