#!/usr/bin/env python3
"""Give a board its number in devices.csv (host name fan-control-N, topics fan-control/fan-control-N/..., HA ids).

    python3 scripts/register_device.py --port /dev/ttyACM0     # read the MAC from the board
    python3 scripts/register_device.py 58:e6:c5:19:38:60 "kitchen"

A MAC that is already registered keeps its number; a new one gets the next free number
(numbers are never reused). Rebuild and flash afterwards: the table is compiled in.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

CSV = Path(__file__).resolve().parent.parent / "devices.csv"
ESPTOOL = Path.home() / ".platformio/packages/tool-esptoolpy/esptool.py"
PYTHON = Path.home() / ".platformio/penv/bin/python"


def norm(mac: str) -> str:
    m = mac.strip().lower().replace("-", ":")
    if not re.fullmatch(r"([0-9a-f]{2}:){5}[0-9a-f]{2}", m):
        sys.exit("not a MAC address: %r" % mac)
    return m


def mac_from_board(port: str) -> str:
    out = subprocess.run([str(PYTHON), str(ESPTOOL), "--port", port, "chip_id"],
                         capture_output=True, text=True).stdout
    m = re.search(r"BASE MAC:\s*([0-9a-f:]{17})", out, re.I) or re.search(r"^MAC:\s*([0-9a-f:]{17})", out, re.I | re.M)
    if not m:
        sys.exit("could not read the MAC from %s:\n%s" % (port, out[-400:]))
    return norm(m.group(1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mac", nargs="?")
    ap.add_argument("note", nargs="?", default="")
    ap.add_argument("--port")
    a = ap.parse_args()
    if bool(a.mac) == bool(a.port):
        ap.error("give a MAC or --port")
    mac = norm(a.mac) if a.mac else mac_from_board(a.port)

    rows = []
    for line in CSV.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            f = line.split(",", 2)
            rows.append((norm(f[0]), int(f[1])))
    known = dict(rows)
    if mac in known:
        print("fan-control-%d  (already registered: %s)" % (known[mac], mac))
        return
    n = max([r[1] for r in rows] + [0]) + 1
    with CSV.open("a", encoding="utf-8") as f:
        f.write("%s,%d,%s\n" % (mac, n, a.note))
    print("fan-control-%d  (registered %s). Rebuild and flash this board." % (n, mac))


if __name__ == "__main__":
    main()
