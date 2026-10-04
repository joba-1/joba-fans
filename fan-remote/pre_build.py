#!/usr/bin/env python3
"""pre_build.py — fan-remote

PlatformIO pre-build script.

* config.ini: created from config.ini.template on the first build (with a random
  admin password), then read and turned into -D defines.
* Version: VERSION file plus git describe and commit date, as -D defines.
* web/index.html -> web/index.html.gz (deterministic), embedded by platformio.ini.
* OTA: hands the admin password to espota, so `pio run -e ota -t upload` just works.
"""
import configparser
import gzip
import os
import secrets
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
    tpl = open(os.path.join(proj, "config.ini.template"), encoding="utf-8").read()
    pw = secrets.token_urlsafe(9)
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(tpl.replace("@RANDOM@", pw))
    os.chmod(cfg_path, 0o600)
    print("[config] created config.ini — admin password: %s (change it there)" % pw)

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
}
if len(strings["CFG_ADMIN_PASSWORD"]) < 8:
    raise SystemExit("config.ini: admin_password must be at least 8 characters "
                     "(it is also the WiFi setup access point password)")

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
if env.get("UPLOAD_PROTOCOL") == "espota":
    env.Append(UPLOADERFLAGS=["--auth=%s" % strings["CFG_ADMIN_PASSWORD"]])
