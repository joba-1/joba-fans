#!/usr/bin/env python3
"""Regenerate the schematic's placement and drawing from the declarative plan.

Usage: generate.py <schematic.kicad_sch> [--no-verify]

Rewrites symbol positions from layout.py, then draws every net from
netplan.py either as wires (local, simple) or as labels (rails, long hops),
per draw.py.

This is the ONLY command needed to rebuild the schematic. It runs the whole
sequence, because every step used to be separate and each one was forgotten at
least once:

  1. reposition symbols and redraw all nets  (validated before writing)
  2. repair structural defects               (was fix_sch.py)
  3. re-attach PWR_FLAGs and no-connects     (was an ad-hoc snippet)
  4. verify the netlist against the plan     (was a separate audit)

Step 4 is the important one. ERC cannot catch a wire that lands on the wrong
real pin -- that is a perfectly legal connection -- so the netlist is diffed
pin-by-pin against build_connections(). Pass --no-verify to skip it when
kicad-cli is unavailable.
"""
import json, os, re, subprocess, sys, tempfile, uuid, collections

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from netplan import build_connections, pin_abs_rot, STUB
from layout import placements
from draw import classify, route

PATH = sys.argv[1]
VERIFY = "--no-verify" not in sys.argv[1:]

# A placed symbol instance. This script writes it on one line, but KiCad
# rewrites the file with each field on its own line whenever the schematic is
# opened and saved in the GUI, so both layouts must be recognised -- otherwise
# a regenerate after any GUI session silently finds zero symbols.
SYMBOL_RE = (r'\(symbol\s*\n?\s*\(lib_id "([^"]+)"\)\s*\n?\s*'
             r'\(at ([\-\d.]+) ([\-\d.]+) (\d+)\)')


def block_at(t, s):
    d = 0
    for i in range(s, len(t)):
        if t[i] == '(':
            d += 1
        elif t[i] == ')':
            d -= 1
            if d == 0:
                return t[s:i + 1]
    raise ValueError("unbalanced")


def strip_drawing(c):
    for opener in ("\t(wire\n", "\t(label ", "\t(no_connect\n", "\t(junction\n"):
        while True:
            i = c.find(opener)
            if i == -1:
                break
            b = block_at(c, i)
            c = c[:i] + c[i + len(b):]
            if c[i:i + 1] == "\n":
                c = c[:i] + c[i + 1:]
    return c


def reposition(c, place):
    out, k = [], 0
    pat = re.compile(SYMBOL_RE)
    while True:
        m = pat.search(c, k)
        if not m:
            out.append(c[k:])
            return "".join(out)
        blk = block_at(c, m.start())
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        out.append(c[k:m.start()])
        if ref in place:
            nx, ny, nrot = place[ref]
            ox, oy = float(m.group(2)), float(m.group(3))
            # Rewrite the symbol's own (at ...) -- the first one in the block --
            # by span rather than by reconstructing the literal text, since
            # whitespace differs between our output and KiCad's re-saved format.
            am = re.search(r'\(at [\-\d.]+ [\-\d.]+ \d+\)', blk)
            nb = blk[:am.start()] + f'(at {nx} {ny} {nrot})' + blk[am.end():]
            head, sep, tail = nb.partition('(property')
            tail = re.sub(r'\(at ([\-\d.]+) ([\-\d.]+) (\d+)\)',
                          lambda pm: '(at %s %s %s)' % (
                              round(float(pm.group(1)) - ox + nx, 3),
                              round(float(pm.group(2)) - oy + ny, 3), pm.group(3)),
                          sep + tail)
            nb = head + tail
            out.append(nb)
        else:
            out.append(blk)
        k = m.start() + len(blk)


def pin_table(c):
    def parse_pins(sym):
        out, k = {}, 0
        while True:
            m = re.compile(r'\(pin \w+ \w+\n').search(sym, k)
            if not m:
                return out
            pb = block_at(sym, m.start())
            at = re.search(r'\(at ([\-\d.]+) ([\-\d.]+) (\d+)\)', pb)
            out[re.search(r'\(number "([^"]+)"', pb).group(1)] = (
                float(at.group(1)), float(at.group(2)), int(at.group(3)),
                re.search(r'\(name "([^"]*)"', pb).group(1))
            k = m.start() + len(pb)

    lib = block_at(c, c.index("\t(lib_symbols"))
    libpins, i = {}, 0
    while True:
        m = re.compile(r'\(symbol "([^"]+:[^"]+)"').search(lib, i)
        if not m:
            break
        sym = block_at(lib, m.start())
        libpins[m.group(1)] = parse_pins(sym)
        i = m.start() + len(sym)

    table = {}
    for m in re.finditer(SYMBOL_RE, c):
        lib_id, px, py, prot = m.group(1), float(m.group(2)), float(m.group(3)), int(m.group(4))
        blk = block_at(c, m.start())
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        table[ref] = {}
        for num, (lx, ly, pr, nm) in libpins[lib_id].items():
            ax, ay, er = pin_abs_rot(px, py, prot, lx, ly, pr)
            table[ref][num] = {"xy": [ax, ay], "rot": er, "name": nm}
    return table


def stub_end(x, y, rot, length=STUB):
    return {0: (round(x - length, 3), y), 180: (round(x + length, 3), y),
            90: (x, round(y + length, 3)), 270: (x, round(y - length, 3))}[rot]


# Pins in a row (a connector's 1..4) all escape along the same axis, so equal
# stubs would land their labels in one column and short them together. Give
# each pin of such a part a different stub length.
STAGGER = {"1": 20.32, "2": 15.24, "3": 10.16, "4": 2.54}

# PWR_FLAG reference -> the rail it declares as driven.
PWR_FLAGS = {"#FLG01": "+12V_PROT", "#FLG02": "GND"}

# XIAO pins deliberately left unconnected: D0/D8/D9 are ESP32-C3 strapping
# pins, 15/16/19/20 the JTAG alternates, 17 EN, 21 VBAT.
NO_CONNECT_PINS = ["1", "9", "10", "15", "16", "17", "19", "20", "21"]


def stub_len(ref, pin):
    return STAGGER.get(pin, STUB) if ref.startswith("J") and ref != "J1" else STUB


def on_segment(pt, a, b, tol=1e-6):
    (px, py), (ax, ay), (bx, by) = pt, a, b
    if abs(ax - bx) < tol:
        return abs(px - ax) < tol and min(ay, by) - tol <= py <= max(ay, by) + tol
    if abs(ay - by) < tol:
        return abs(py - ay) < tol and min(ax, bx) - tol <= px <= max(ax, bx) + tol
    return False


def wire(a, b):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})\n\t\t)\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(uuid "{uuid.uuid4()}")\n\t)\n')


def label(text, x, y, rot):
    lrot = {0: 180, 180: 0, 90: 90, 270: 270}[rot]
    just = "right" if rot == 0 else "left"
    return (f'\t(label "{text}"\n\t\t(at {x} {y} {lrot})\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify {just} bottom)\n\t\t)\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')


def junction(x, y):
    return (f'\t(junction\n\t\t(at {x} {y})\n\t\t(diameter 0)\n'
            f'\t\t(color 0 0 0 0)\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')


def repair(c, project_name, sheet_uuid):
    """Structural fixes for symbols written by kicad-mcp-server (was fix_sch.py).

    Three defects, any one of which makes the file fail to load in real KiCad
    while ERC-by-regex still reports it as fine:
      * a (uuid ...) inside a placed instance's property block -- invalid
      * a missing (instances (project ...)) block
      * (sheet_instances)/(embedded_fonts) not last in the file

    Idempotent.
    """
    n_uuid = c.count('(uuid "')
    c = re.sub(
        r'(\(effects \(font \(size 1\.27 1\.27\)\)(?: \(hide yes\))?\))\n\s*'
        r'\(uuid "[0-9a-f-]+"\)\n(\s*)\)',
        r'\1\n\2)', c)
    stripped = n_uuid - c.count('(uuid "')

    c = re.sub(r'\n?\t\(sheet_instances\n\t\t\(path "/"\n\t\t\t\(page "1"\)\n\t\t\)\n\t\)\n?', '\n', c)
    c = re.sub(r'\n?\t\(embedded_fonts no\)\n?', '\n', c)

    # Add (instances ...) to any placed symbol lacking one. Matching goes via
    # SYMBOL_RE so this works on both our single-line output and KiCad's
    # re-saved multi-line format -- fix_sch.py only handled the former, so it
    # silently did nothing after any GUI session.
    out, k, added = [], 0, 0
    for m in re.finditer(SYMBOL_RE, c):
        if m.start() < k:
            continue
        blk = block_at(c, m.start())
        out.append(c[k:m.start()])
        if '(instances' not in blk:
            ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
            blk = blk[:-1] + (
                f'\n\t\t(instances\n\t\t\t(project "{project_name}"\n'
                f'\t\t\t\t(path "/{sheet_uuid}"\n'
                f'\t\t\t\t\t(reference "{ref}") (unit 1)\n'
                f'\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
            added += 1
        out.append(blk)
        k = m.start() + len(blk)
    out.append(c[k:])
    c = "".join(out)

    c = c.rstrip()
    assert c.endswith(')')
    c = c[:-1].rstrip()
    c += ('\n\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n'
          '\t(embedded_fonts no)\n)\n')
    return c, stripped, added


def flags_and_no_connects(c, table):
    """Re-attach PWR_FLAGs and no-connect markers stripped by the redraw.

    PWR_FLAGs silence 'input power pin not driven' on rails whose only source
    is a connector or a regulator output. The no-connects mark the XIAO pins
    deliberately left free -- the three ESP32-C3 strapping pins plus the JTAG
    alternates, EN and VBAT.
    """
    parts = []
    for m in re.finditer(SYMBOL_RE, c):
        if m.group(1) != "power:PWR_FLAG":
            continue
        blk = block_at(c, m.start())
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        net = PWR_FLAGS.get(ref)
        if net is None:
            continue
        px, py = float(m.group(2)), float(m.group(3))
        ax, ay, er = pin_abs_rot(px, py, int(m.group(4)), 0.0, 0.0, 90)
        ex, ey = stub_end(ax, ay, er)
        parts.append(wire((ax, ay), (ex, ey)))
        parts.append(label(net, ex, ey, er))

    for pin in NO_CONNECT_PINS:
        if "U1" in table and pin in table["U1"]:
            x, y = table["U1"][pin]["xy"]
            parts.append(f'\t(no_connect\n\t\t(at {x} {y})\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')
    return parts


def verify(path):
    """Diff the exported netlist against the plan, pin by pin.

    The only check that catches a wire landing on the wrong real pin: ERC
    accepts that happily, since it is still a valid connection.
    """
    with tempfile.NamedTemporaryFile(suffix=".net", delete=False) as f:
        netfile = f.name
    try:
        r = subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", "--output", netfile, path],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ! netlist export failed: {r.stderr.strip()[:200]}")
            return False
        c = open(netfile).read()
    finally:
        os.unlink(netfile)

    def blocks(t, o):
        out, k = [], 0
        while True:
            m = t.find(o, k)
            if m == -1:
                return out
            d = 0
            for i in range(m, len(t)):
                if t[i] == '(':
                    d += 1
                elif t[i] == ')':
                    d -= 1
                    if d == 0:
                        break
            out.append(t[m:i + 1])
            k = i + 1

    actual = {}
    for b in blocks(c, "(net\n"):
        n = re.search(r'\(name "([^"]*)"\)', b).group(1).lstrip('/')
        actual[n] = frozenset(
            (re.search(r'\(ref "([^"]+)"\)', nb).group(1),
             re.search(r'\(pin "([^"]+)"\)', nb).group(1))
            for nb in blocks(b, "(node\n"))

    expected = collections.defaultdict(set)
    for r_, p_, n_ in build_connections():
        expected[n_].add((r_, p_))

    bad = [n for n in expected if actual.get(n) != frozenset(expected[n])]
    surprise = [n for n in actual
                if n not in expected and not n.startswith('unconnected-')]
    for n in bad:
        print(f"  ! {n}: want {sorted(expected[n])} got {sorted(actual.get(n) or [])}")
    for n in surprise:
        print(f"  ! unexpected net {n}: {sorted(actual[n])}")
    if bad or surprise:
        return False
    unconn = sum(1 for n in actual if n.startswith('unconnected-'))
    print(f"verified: {len(expected)}/{len(expected)} nets match, {unconn} intended no-connects")
    return True


def main():
    c = open(PATH).read()
    c = strip_drawing(c)
    c = reposition(c, placements())
    table = pin_table(c)

    nets = collections.defaultdict(list)
    for r, p, n in build_connections():
        nets[n].append((r, p, tuple(table[r][p]["xy"]), table[r][p]["rot"]))

    all_pins = {tuple(table[r][p]["xy"]): f"{r}.{p}"
                for r in table for p in table[r]}

    parts, segments, stats = [], [], collections.Counter()

    for net in sorted(nets):
        pts = [(r, p, xy) for r, p, xy, _ in nets[net]]
        kind = classify(net, pts)
        stats[kind] += 1

        if kind == "label":
            for r, p, xy, rot in nets[net]:
                e = stub_end(xy[0], xy[1], rot, stub_len(r, p))
                parts.append(wire(xy, e))
                segments.append((xy, e, net))
                parts.append(label(net, e[0], e[1], rot))
        elif len(nets[net]) == 2:
            (r1, p1, xy1, rot1), (r2, p2, xy2, rot2) = sorted(
                nets[net], key=lambda t: (t[2][0], t[2][1]))
            own = {xy1, xy2}
            foreign = [xy for xy, who in all_pins.items() if xy not in own]

            def blocked(segs):
                return any(on_segment(pt, a, b) for a, b in segs for pt in foreign)

            path = route(xy1, xy2, rot1, rot2)
            if blocked(path):
                # A third part sits in the way. Step the run off onto a clear
                # parallel axis and try progressively larger offsets.
                horiz = rot1 in (0, 180)
                base = xy1[1] if horiz else xy1[0]
                for off in (6.35, -6.35, 12.7, -12.7, 19.05, -19.05):
                    cand = route(xy1, xy2, rot1, rot2, detour=round(base + off, 3))
                    if not blocked(cand):
                        path = cand
                        break
            for a, b in path:
                if a != b:
                    parts.append(wire(a, b))
                    segments.append((a, b, net))
            # Name the wire so the netlist shows the intended name rather than
            # an auto-generated "Net-(D1-A)". One label anywhere on the run is
            # enough; put it on the longest horizontal segment, above the wire.
            horiz = [(a, b) for a, b in path if abs(a[1] - b[1]) < 1e-6]
            if horiz:
                a, b = max(horiz, key=lambda s: abs(s[0][0] - s[1][0]))
                mx = round((a[0] + b[0]) / 2, 3)
                parts.append(label(net, mx, a[1], 180))
        else:
            # Three endpoints: run a trunk between the two extremes, then tap
            # the third onto it, placing a junction dot at the tap point.
            ordered = sorted(nets[net], key=lambda t: (t[2][0], t[2][1]))
            (ra, pa, xya, rota), (rb, pb, xyb, rotb) = ordered[0], ordered[-1]
            trunk = route(xya, xyb, rota, rotb)
            for a, b in trunk:
                if a != b:
                    parts.append(wire(a, b))
                    segments.append((a, b, net))

            rc, pc, xyc, rotc = ordered[1]
            ec = stub_end(xyc[0], xyc[1], rotc, stub_len(rc, pc))
            # Drop onto whichever trunk segment shares an axis with the tap.
            tap = None
            for a, b in trunk:
                if abs(a[1] - b[1]) < 1e-6 and min(a[0], b[0]) <= ec[0] <= max(a[0], b[0]):
                    tap = (ec[0], a[1])
                    break
                if abs(a[0] - b[0]) < 1e-6 and min(a[1], b[1]) <= ec[1] <= max(a[1], b[1]):
                    tap = (a[0], ec[1])
                    break
            if tap is None:
                tap = trunk[0][1]
            parts.append(wire(xyc, ec))
            segments.append((xyc, ec, net))
            if ec != tap:
                parts.append(wire(ec, tap))
                segments.append((ec, tap, net))
            parts.append(junction(tap[0], tap[1]))

    # ---- validation before writing ----
    errors = []
    ends = {}
    pin_at = {tuple(table[r][p]["xy"]): f"{r}.{p}" for r in table for p in table[r]}
    for a, b, net in segments:
        for pt in (a, b):
            if pt in ends and ends[pt] != net:
                errors.append(f"point {pt} shared by nets {ends[pt]} and {net}")
            ends[pt] = net

    for i in range(len(segments)):
        a1, b1, n1 = segments[i]
        for j in range(i + 1, len(segments)):
            a2, b2, n2 = segments[j]
            if n1 == n2:
                continue
            for pt in (a1, b1):
                if on_segment(pt, a2, b2):
                    errors.append(f"{n1} endpoint {pt} touches {n2} segment")
            for pt in (a2, b2):
                if on_segment(pt, a1, b1):
                    errors.append(f"{n2} endpoint {pt} touches {n1} segment")
            # a wire passing through a pin of another net
    for (px, py), who in pin_at.items():
        owner = None
        for r in table:
            for p in table[r]:
                if tuple(table[r][p]["xy"]) == (px, py):
                    owner = f"{r}.{p}"
        for a, b, net in segments:
            if on_segment((px, py), a, b) and (px, py) not in (a, b):
                errors.append(f"{net} passes through pin {owner} at {(px,py)}")

    if errors:
        print("VALIDATION FAILED:")
        for e in sorted(set(errors)):
            print("  !", e)
        return 1

    # ---- step 3: PWR_FLAGs and no-connects, before the file is assembled ----
    parts += flags_and_no_connects(c, table)

    idx = c.index("\t(sheet_instances")
    c = c[:idx] + "".join(parts) + c[idx:]

    # ---- step 2: structural repair -----------------------------------------
    project = os.path.splitext(os.path.basename(PATH))[0]
    sheet_uuid = re.search(r'\(uuid "([0-9a-f-]+)"\)', c).group(1)
    c, stripped, added = repair(c, project, sheet_uuid)

    open(PATH, "w").write(c)

    n_wire = sum(1 for p in parts if p.startswith('\t(wire'))
    n_label = sum(1 for p in parts if p.startswith('\t(label'))
    n_nc = sum(1 for p in parts if p.startswith('\t(no_connect'))
    print(f"wired nets: {stats['wire']}   labelled nets: {stats['label']}")
    print(f"emitted {n_wire} wire segments, {n_label} labels, {n_nc} no-connects")
    if stripped or added:
        print(f"repaired: {stripped} stray property uuids, {added} missing instances blocks")

    # ---- step 4: netlist verification --------------------------------------
    if VERIFY and not verify(PATH):
        print("NETLIST VERIFICATION FAILED - schematic does not match netplan.py")
        return 1
    return 0


sys.exit(main())
