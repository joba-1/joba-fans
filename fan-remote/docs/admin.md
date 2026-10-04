# fan-remote — administration

## Build and flash

Needs PlatformIO (`pio`). The first build creates `config.ini` from `config.ini.template`
and prints a **random admin password** once; edit the file (mode 600, gitignored) for the
service aliases (`mqtt`, `syslog`), the HA prefix, standby timing and so on. That one password
is the settings login, the setup access point password and the OTA password of every board
flashed from this tree - on purpose (home network), so keep `config.ini` safe.

```sh
pio run -e xiao_c3 -t upload                  # new board, USB-C
pio run -e ota -t upload --upload-port fan-control-1   # update over WiFi (XIAO C6: -e ota_c6)
```

A XIAO ESP32-C6 works too (same pin positions): `-e xiao_c6` / `-e ota_c6`.

`min_spiffs.csv` gives two 1.9 MB app slots (OTA); the firmware is about 1.2 MB.
Never run two `pio` invocations at once. Updating over WiFi reboots the board: the
PWM pins float for a moment and the fans can burst to full speed (see spec.md).

## Adding a board

Boards are numbered in `devices.csv` (MAC → number, committed). The number is the host name
(`fan-control-N`), the MQTT topics (`fan-control/fan-control-N/…`), the setup AP (`fan-control-N-setup`) and the Home
Assistant ids. Numbers are never reused.

1. Plug the board in and register it: `python3 scripts/register_device.py --port /dev/ttyACM0`
   (prints `fan-control-N`; `devices.csv` gains a line, commit it). Or give the MAC:
   `register_device.py 58:e6:c5:19:38:60 "kitchen"`.
2. Flash over USB-C (`pio run -e xiao_c3 -t upload`, `-e xiao_c6` for a C6). The table is
   compiled in, so build after registering.
3. The board opens the access point `fan-control-N-setup` (password: `admin_password` from `config.ini`). Join it from a
   phone; the page asks for WiFi, a friendly name and the broker alias.
4. The board appears in HA within seconds (broker + MQTT integration + discovery on).
5. Open the page → settings → fans: set names, *Min* duty and which channels exist.

A board that is not in the table still works, as `fan-control-new-xxxxxx` (last three MAC bytes):
register it and reflash to get its number. The number never changes; renaming only changes
the friendly name. Replacing a board therefore creates a new HA device. **Renumbering a
board** (or first moving one from MAC ids): publish an empty retained message to its old
`homeassistant/+/<oldid>_*/config` topics before flashing, so HA drops the old entities
and the new ones keep the entity ids, then clear the old `fan-control/<oldid>/#` retained topics.

## Status LED

Settings → Status LED (or `led` in `/api/config`). Build defaults are `led_mode`, `led_day`, `led_night`,
`night_from`, `night_to` in `config.ini`. To test the problem signal on a board whose fan is off, unplug a
running fan (stalled after about 8 s) or enter a wrong broker under Network and reboot; `curl
http://fan-control-1/api/netstatus` shows `health.issues`. A different board with its own LED pins: set
`LED_FAN_PIN` / `LED_ALERT_PIN` / `LED_ACTIVE_LOW` in the environment's `build_flags`.

## Runtime configuration

Compile-time values are only defaults. Per board, behind the admin login:

```sh
curl -u admin:<pw> -X POST http://fan-control-1/api/netconfig \
     -d mqttHost=mqtt -d syslogHost=syslog -d ntpHost=de.pool.ntp.org
curl -u admin:<pw> -X POST http://fan-control-1/api/netconfig -d defaults=1   # back to config.ini
curl http://fan-control-1/api/netstatus     # firmware, version, WiFi, each resource and its last result
```

Stored in NVS (a firmware update keeps it), applied at the next boot. The broker name
is resolved on every connect, so a moved alias is followed without a reboot; the
syslog name is re-resolved hourly and after a failed send.

## Operations

* **Logs**: serial (USB, 115200) and UDP syslog to the alias `syslog`
  (`app-name fan-remote`, host = device id). Stall/recovery and config changes are logged.
* **Forgetting WiFi**: settings → *Forget WiFi*, or `POST /api/wifireset`. The board
  reboots into the setup portal.
* **Updating over WiFi:** `pio run -e ota -t upload --upload-port fan-control-N`
  (`ota_c6` for a C6) pushes the image to the board's own web server (`POST /api/update`,
  admin login). The host only makes an outbound connection, so **no firewall port is needed**.
  The script retries on a flaky link; a board that was flashed with an older firmware without
  `/api/update` answers 404 and needs one USB or ArduinoOTA flash first. A wrong chip image is
  rejected at the end of the upload and leaves the running firmware alone. By hand:
  `curl -u admin:<pw> -F firmware=@.pio/build/xiao_c6/firmware.bin http://fan-control-1/api/update`.
* **ArduinoOTA fallback** (`-e espota` / `espota_c6`): the board connects back to the host, so a
  host firewall must let that through: pin the port with `FAN_OTA_HOST_PORT=3333` and open it
  (`sudo firewall-cmd --add-port=3333/tcp`, runtime only). `FAN_OTA_PASSWORD=…` overrides the
  password for a board whose own differs. A weak WiFi link can break these uploads ("Broken
  pipe", "No response").
* **Factory reset**: `pio run -e xiao_c3 -t erase`, then flash again.
* **Backup**: nothing on the board needs a backup; `config.ini` (secrets) belongs in the
  password manager, everything else is the repository. Per-board settings are
  re-enterable in a minute.

## Restore procedure

1. Clone the repository; install PlatformIO.
2. Restore `config.ini` from the password manager (or let the build create a new one;
   then boards keep their stored password until you change it in the portal).
3. `pio run -e xiao_c3 -t upload` for each board, then the portal steps above.
4. Verify: `curl http://<board>/api/netstatus` shows MQTT `connected`; HA shows the device.

## Troubleshooting

| Symptom | Check |
|---|---|
| Fan does not start, card says Stalled | Tach wired? `tach` off in settings if the fan has no tach wire. Fan stuck? *Min*/start duty too low for this fan? Try a higher *Min* |
| RPM reads double/half | *Pulses per revolution* (PC fans: 2; some server fans 4) |
| RPM jumps around at low speed | Raise *Min*; a fan at the edge of stalling gives uneven pulses |
| Page loads, no live updates | A proxy buffering `text/event-stream`; the page falls back to polling every 3 s |
| Board not in HA | `/api/netstatus` MQTT line; broker credentials in settings; discovery prefix `homeassistant` |
| Settings prompt keeps coming back | Wrong password. After 5 failures the login is locked for 30 s |
| Fans burst briefly at reset | Hardware: no pull-down on the PWM lines (spec.md). Avoid needless reboots |
