# fan-remote — administration

## Build and flash

Needs PlatformIO (`~/.platformio/penv/bin/pio`). The first build creates `config.ini`
from `config.ini.template` with a random `admin_password` and prints it; edit the file
(mode 600, gitignored) for the service aliases (`mqtt`, `syslog`), the HA prefix, and so on.

```sh
pio run -e xiao_c3 -t upload                  # new board, USB-C
pio run -e ota -t upload --upload-port fan-a1b2c3.local   # update over WiFi
```

`min_spiffs.csv` gives two 1.9 MB app slots (OTA); the firmware is about 1.2 MB.
Never run two `pio` invocations at once. Flashing over OTA reboots the board: the
PWM pins float for a moment and the fans can burst to full speed (see spec.md).

## Adding a board

1. Flash over USB-C. The XIAO is socketed on the board; flash it before inserting if you like.
2. The board opens the access point `fan-<mac>-setup`. The password is `admin_password` from `config.ini`.
3. Join it from a phone; the captive page asks for WiFi, a friendly name, the broker
   alias and optionally a new admin password for this board (min. 8 characters).
4. The board appears in HA within seconds (broker + MQTT integration + discovery on).
5. Open the page → settings → fans: set names, *Min* duty and which channels exist.

The device id (`fan-` + last three MAC bytes) never changes; renaming only changes
the friendly name. Replacing a board therefore creates a new HA device.

## Runtime configuration

Compile-time values are only defaults. Per board, behind the admin login:

```sh
curl -u admin:<pw> -X POST http://fan-a1b2c3.local/api/netconfig \
     -d mqttHost=mqtt -d syslogHost=syslog -d ntpHost=de.pool.ntp.org
curl -u admin:<pw> -X POST http://fan-a1b2c3.local/api/netconfig -d defaults=1   # back to config.ini
curl http://fan-a1b2c3.local/api/netstatus     # firmware, version, WiFi, each resource and its last result
```

Stored in NVS (a firmware update keeps it), applied at the next boot. The broker name
is resolved on every connect, so a moved alias is followed without a reboot; the
syslog name is re-resolved hourly and after a failed send.

## Operations

* **Logs**: serial (USB, 115200) and UDP syslog to the alias `syslog`
  (`app-name fan-remote`, host = device id). Stall/recovery and config changes are logged.
* **Forgetting WiFi**: settings → *Forget WiFi*, or `POST /api/wifireset`. The board
  reboots into the setup portal.
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
