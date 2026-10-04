#!/usr/bin/env python3
"""pre_build.py — fan-remote

PlatformIO pre-build script.

* config.ini: created from config.ini.template on the first build, then read and turned
  into -D defines.
* devices.csv (MAC -> board number) becomes src/DeviceTable.h.
* Version: VERSION file plus git describe and commit date, as -D defines.
* web/index.html -> web/index.html.gz (deterministic), embedded by platformio.ini.
* OTA: hands the admin password to espota, so `pio run -e ota -t upload` just works.
"""
import configparser
import gzip
import os
import shutil
import subprocess

Import("env")  # noqa: F821  (provided by PlatformIO)

proj = env.subst("$PROJECT_DIR")


def read(path):
    with open(path, "rb") as f:
        return f.read()


def git(*args):
    try:
        return subprocess.check_output(
            ["git", "-C", proj, *args], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return ""


# ---- config.ini -------------------------------------------------------------
cfg_path = os.path.join(proj, "config.ini")
if not os.path.exists(cfg_path):
    shutil.copyfile(os.path.join(proj, "config.ini.template"), cfg_path)
    os.chmod(cfg_path, 0o600)
    print("[config] created config.ini from the template")

cp = configparser.ConfigParser(inline_comment_prefixes=(";",))
cp.read(cfg_path, encoding="utf-8")
u = cp["user_config"]


def opt(key, default=""):
    return u.get(key, default).strip()


strings = {
    "CFG_ADMIN_USER": opt("admin_user", "admin"),
    "CFG_ADMIN_PASSWORD": opt("admin_password"),
    "CFG_MQTT_HOST": opt("mqtt_host"),
    "CFG_MQTT_USER": opt("mqtt_user"),
    "CFG_MQTT_PASSWORD": opt("mqtt_password"),
    "CFG_MQTT_PREFIX": opt("mqtt_prefix", "fans"),
    "CFG_HA_PREFIX": opt("ha_prefix", "homeassistant"),
    "CFG_SYSLOG_HOST": opt("syslog_host"),
    "CFG_NTP_HOST": opt("ntp_host", "pool.ntp.org"),
    "CFG_TIMEZONE": opt("timezone", "UTC0"),
}
ints = {
    "CFG_MQTT_PORT": int(opt("mqtt_port", "1883")),
    "CFG_SYSLOG_PORT": int(opt("syslog_port", "514")),
    "CFG_POWER_SAVE": int(opt("power_save", "1")),
    "CFG_IDLE_S": int(opt("idle_seconds", "60")),
    "CFG_CPU_ACTIVE_MHZ": int(opt("cpu_active_mhz", "160")),
    "CFG_CPU_IDLE_MHZ": int(opt("cpu_idle_mhz", "80")),
}
if len(strings["CFG_ADMIN_PASSWORD"]) < 8:
    raise SystemExit("config.ini: admin_password must be at least 8 characters "
                     "(it is also the WiFi setup access point password)")
if ints["CFG_CPU_IDLE_MHZ"] < 80 or ints["CFG_CPU_ACTIVE_MHZ"] < ints["CFG_CPU_IDLE_MHZ"]:
    raise SystemExit("config.ini: cpu_idle_mhz must be >= 80 (WiFi, PWM clock) and <= cpu_active_mhz")

# ---- devices.csv -> src/DeviceTable.h ------------------------------------------------
rows = []
with open(os.path.join(proj, "devices.csv"), encoding="utf-8") as f:
    for ln, line in enumerate(f, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.strip().split(",", 2)
        mac = parts[0].strip().lower().replace(":", "")
        if len(mac) != 12 or int(parts[1]) < 1:
            raise SystemExit("devices.csv line %d: expected 'aa:bb:cc:dd:ee:ff,number,note'" % ln)
        rows.append((mac, int(parts[1])))
nums = [n for _, n in rows]
if len(set(nums)) != len(nums) or len({m for m, _ in rows}) != len(rows):
    raise SystemExit("devices.csv: a MAC or a number is used twice")
body = ",\n".join("    {{%s}, %d}" % (", ".join("0x" + m[i:i + 2] for i in range(0, 12, 2)), n) for m, n in rows)
header = ("// generated from devices.csv by pre_build.py — do not edit\n#pragma once\n#include \"FanCore.h\"\n"
          "static const fancore::DeviceEntry kDeviceTable[] = {\n%s%s{{0, 0, 0, 0, 0, 0}, 0}};\n"
          "static const unsigned kDeviceTableLen = %d;\n" % (body, ",\n    " if rows else "    ", len(rows)))
hp = os.path.join(proj, "src", "DeviceTable.h")
if not os.path.exists(hp) or open(hp, encoding="utf-8").read() != header:
    with open(hp, "w", encoding="utf-8") as f:
        f.write(header)

# ---- version ----------------------------------------------------------------
version = open(os.path.join(proj, "VERSION"), encoding="utf-8").read().strip()
describe = git("describe", "--always", "--dirty", "--tags") or "nogit"
commit_ts = git("show", "-s", "--format=%cI", "HEAD") or "unknown"
strings["FW_VERSION"] = version
strings["FW_GIT"] = describe
strings["FW_DATE"] = commit_ts

defs = [(k, env.StringifyMacro(v)) for k, v in strings.items()]
defs += [(k, v) for k, v in ints.items()]
env.Append(CPPDEFINES=defs)

# ---- web page -> gzip -------------------------------------------------------
src = os.path.join(proj, "web", "index.html")
dst = src + ".gz"
if os.path.exists(src):
    data = gzip.compress(read(src), compresslevel=9, mtime=0)
    if not os.path.exists(dst) or read(dst) != data:
        with open(dst, "wb") as f:
            f.write(data)
        print("[web] index.html -> index.html.gz (%d bytes)" % len(data))

# ---- OTA password -----------------------------------------------------------
# The platform sets UPLOADERFLAGS after this script has run, so the flag has to be added
# right before the upload action. FAN_OTA_PASSWORD overrides config.ini for a board whose
# own admin password differs (set in the setup portal or the settings page).
if env.get("UPLOAD_PROTOCOL") == "espota":
    def _ota_auth(source, target, env):
        pw = os.environ.get("FAN_OTA_PASSWORD") or strings["CFG_ADMIN_PASSWORD"]
        env.Append(UPLOADERFLAGS=["--auth=%s" % pw])
        # The board connects back to the host to fetch the image. FAN_OTA_HOST_PORT pins
        # that port so a host firewall can allow it (default: a random one).
        port = os.environ.get("FAN_OTA_HOST_PORT")
        if port:
            env.Append(UPLOADERFLAGS=["--host_port=%d" % int(port)])

    env.AddPreAction("upload", _ota_auth)
