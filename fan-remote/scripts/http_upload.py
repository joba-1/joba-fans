#!/usr/bin/env python3
"""Upload firmware to a board over HTTP: POST /api/update on the board's own web server.

    python3 scripts/http_upload.py fan-control-1.local .pio/build/xiao_c6/firmware.bin
    pio run -e ota_c6 -t upload --upload-port fan-control-1.local      # the same, via PlatformIO

The host only makes an outbound connection to the board's port 80, so no firewall port has
to be opened on the host (ArduinoOTA needs one: the board connects back). Password: env
FAN_OTA_PASSWORD, else admin_password from config.ini. A weak WiFi link can drop an upload;
it is retried.
"""
import base64
import configparser
import http.client
import json
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def password() -> str:
    pw = os.environ.get("FAN_OTA_PASSWORD")
    if pw:
        return pw
    cp = configparser.ConfigParser(inline_comment_prefixes=(";",))
    cp.read(ROOT / "config.ini", encoding="utf-8")
    return cp.get("user_config", "admin_password", fallback="").strip()


def user() -> str:
    cp = configparser.ConfigParser(inline_comment_prefixes=(";",))
    cp.read(ROOT / "config.ini", encoding="utf-8")
    return cp.get("user_config", "admin_user", fallback="admin").strip()


def upload(host: str, image: bytes) -> tuple:
    boundary = uuid.uuid4().hex
    head = ('--%s\r\nContent-Disposition: form-data; name="firmware"; filename="firmware.bin"\r\n'
            'Content-Type: application/octet-stream\r\n\r\n' % boundary).encode()
    tail = ("\r\n--%s--\r\n" % boundary).encode()
    auth = base64.b64encode(("%s:%s" % (user(), password())).encode()).decode()
    c = http.client.HTTPConnection(host, 80, timeout=60)
    try:
        c.request("POST", "/api/update", body=head + image + tail, headers={
            "Authorization": "Basic " + auth,
            "Content-Type": "multipart/form-data; boundary=" + boundary,
            "Content-Length": str(len(head) + len(image) + len(tail)),
        })
        r = c.getresponse()
        return r.status, r.read().decode(errors="replace")
    finally:
        c.close()


def wait_back(host: str, seconds: int = 60):
    end = time.time() + seconds
    time.sleep(3)
    while time.time() < end:
        try:
            c = http.client.HTTPConnection(host, 80, timeout=4)
            c.request("GET", "/api/netstatus")
            d = json.loads(c.getresponse().read())
            c.close()
            return d
        except (OSError, ValueError):
            time.sleep(2)
    return None


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    host, path = sys.argv[1], sys.argv[2]
    image = Path(path).read_bytes()
    print("uploading %s (%d bytes) to http://%s/api/update" % (path, len(image), host))
    last = ""
    for attempt in range(1, 5):
        try:
            status, body = upload(host, image)
        except (OSError, http.client.HTTPException) as e:
            last = str(e)
            print("attempt %d: %s, retrying" % (attempt, e))
            time.sleep(3)
            continue
        if status == 200:
            print("accepted, waiting for the board to come back ...")
            d = wait_back(host)
            if d:
                print("up again: %s %s (%s)" % (d.get("hostname"), d.get("version"), d.get("git")))
                return
            sys.exit("the board did not answer again within 60 s")
        if status == 404:
            sys.exit("404: this board runs a firmware without /api/update. Flash it once over USB or "
                     "ArduinoOTA (-e espota / espota_c6); after that this script works.")
        if status in (401, 403, 429):
            sys.exit("refused (%d): %s" % (status, body))
        last = "HTTP %d: %s" % (status, body)
        print("attempt %d: %s" % (attempt, last))
        time.sleep(3)
    sys.exit("upload failed: " + last)


if __name__ == "__main__":
    main()
