#!/usr/bin/env python3
"""Mock of the device's HTTP API for working on web/index.html without hardware.

    python3 scripts/mock_server.py [port] [delay_s]   # default 8099, no delay

Serves the page, /events (SSE), /api/state, /api/set, /api/config, /api/netstatus
with four simulated fans (one of them stalled), using the same JSON as the firmware.
`delay_s` holds every POST /api/set back that long, to look at the pending markers of the
page (the real board answers in 10 ms to 250 ms depending on WiFi power save).
No authentication: this is a design aid, not a reimplementation.
"""
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parent.parent / "web"
PRESETS = [("quiet", 10), ("low", 30), ("medium", 50), ("high", 75), ("max", 100)]
lock = threading.Lock()
DELAY = 0.0
cfg = {"name": "Fans Living room", "rampUp": 10, "rampDown": 20, "bootMode": 0, "protectControl": False,
       "presets": [p[1] for p in PRESETS],
       "ch": [{"name": n, "enabled": e, "min": 20, "max": 100, "tach": True, "ppr": 2}
              for n, e in (("Radiator left", True), ("Radiator right", True), ("Window", True), ("Fan 4", True))],
       "net": {"mqttHost": "mqtt", "mqttPort": 1883, "mqttUser": "fans", "mqttPassSet": True,
               "syslogHost": "syslog", "ntpHost": "de.pool.ntp.org"}}
fans = [{"speed": 50, "duty": 60.0, "rpm": 1480, "state": "run", "fault": False},
        {"speed": 0, "duty": 0.0, "rpm": 0, "state": "off", "fault": False},
        {"speed": 20, "duty": 24.0, "rpm": 310, "state": "spinup", "fault": False},
        {"speed": 60, "duty": 0.0, "rpm": 0, "state": "fault", "fault": True}]


def sim():
    while True:
        time.sleep(0.2)
        with lock:
            for f, c in zip(fans, cfg["ch"]):
                if f["fault"]:
                    continue
                tgt = 0 if f["speed"] == 0 else c["min"] + (c["max"] - c["min"]) * f["speed"] / 100
                f["duty"] += max(-4, min(2, tgt - f["duty"]))
                f["duty"] = max(0.0, f["duty"])
                f["state"] = "off" if f["duty"] < 0.5 and f["speed"] == 0 else "run"
                f["rpm"] = int(f["duty"] * 24.5) if f["duty"] > 5 else 0


def state():
    with lock:
        ch = []
        for i, (f, c) in enumerate(zip(fans, cfg["ch"])):
            ch.append({"n": i + 1, "name": c["name"], "enabled": c["enabled"], "speed": f["speed"],
                       "duty": round(f["duty"], 1), "rpm": f["rpm"], "state": f["state"], "fault": f["fault"],
                       "tach": c["tach"], "min": c["min"], "max": c["max"]})
        return {"id": "fan-a1b2c3", "name": cfg["name"], "v": "0.1.0", "up": 4242, "rssi": -58, "mqtt": True,
                "presets": [{"id": p[0], "speed": cfg["presets"][i]} for i, p in enumerate(PRESETS)], "ch": ch}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json", extra=()):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/":
            self.send(200, (ROOT / "index.html").read_bytes(), "text/html")
        elif self.path == "/logo.svg":
            self.send(200, (ROOT / "logo.svg").read_bytes(), "image/svg+xml")
        elif self.path == "/api/wake":
            self.send(204, "", "text/plain")
        elif self.path == "/api/state":
            self.send(200, json.dumps(state()))
        elif self.path == "/api/config":
            self.send(200, json.dumps(cfg))
        elif self.path == "/api/netstatus":
            self.send(200, json.dumps({"firmware": "fan-remote", "version": "0.1.0", "git": "mock", "hostname": "fan-a1b2c3",
                "ip": "192.168.1.50", "ssid": "home", "rssi": -58, "uptimeS": 4242, "freeHeap": 180000,
                "power": {"mode": "standby", "cpuMhz": 80, "standbyInS": 0, "pwmHz": 25000},
                "resources": [{"name": "mqtt", "host": "mqtt", "status": "connected", "lastOkAgoS": 2},
                              {"name": "syslog", "host": "syslog", "status": "sent", "lastOkAgoS": 40},
                              {"name": "ntp", "host": "de.pool.ntp.org", "status": "synced", "lastOkAgoS": 900}]}))
        elif self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                while True:
                    self.wfile.write(("event: state\ndata: %s\n\n" % json.dumps(state())).encode())
                    self.wfile.flush()
                    time.sleep(0.5)
            except OSError:
                pass
        else:
            self.send(404, "not found", "text/plain")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode()
        if self.path == "/api/set":
            time.sleep(DELAY)
            q = {k: v[0] for k, v in parse_qs(body).items()}
            idx = range(4) if q.get("ch") == "all" else [int(q["ch"]) - 1]
            with lock:
                for i in idx:
                    f = fans[i]
                    if "speed" in q:
                        f["speed"] = int(q["speed"])
                    elif "preset" in q:
                        f["speed"] = cfg["presets"][[p[0] for p in PRESETS].index(q["preset"])]
                    elif q.get("power") == "off":
                        f["speed"] = 0
                    elif q.get("power") == "on":
                        f["speed"] = 40
                    f["fault"] = False if f["speed"] == 0 else f["fault"]
            self.send(200, json.dumps(state()))
        elif self.path == "/api/config":
            new = json.loads(body)
            with lock:
                for k in ("name", "rampUp", "rampDown", "bootMode", "protectControl", "presets", "ch"):
                    if k in new:
                        cfg[k] = new[k]
            self.send(200, json.dumps(cfg))
        else:
            self.send(200, "{}")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8099
    DELAY = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    threading.Thread(target=sim, daemon=True).start()
    print("mock device on http://localhost:%d/" % port)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
