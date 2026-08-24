#!/usr/bin/env python3
"""Regenerate the schematic's placement and drawing from the declarative plan.

Usage: generate.py <schematic.kicad_sch>

Rewrites symbol positions from layout.py, then draws every net from
netplan.py either as wires (local, simple) or as labels (rails, long hops),
per draw.py. Validates geometry before writing anything.
"""
import json, re, sys, uuid, collections

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from netplan import build_connections, pin_abs_rot, STUB
from layout import placements
from draw import classify, route

PATH = sys.argv[1]


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
    pat = re.compile(r'\(symbol \(lib_id "([^"]+)"\) \(at ([\-\d.]+) ([\-\d.]+) (\d+)\)')
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
            nb = blk.replace(f'(at {m.group(2)} {m.group(3)} {m.group(4)})',
                             f'(at {nx} {ny} {nrot})', 1)
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
    for m in re.finditer(r'\(symbol \(lib_id "([^"]+)"\) \(at ([\-\d.]+) ([\-\d.]+) (\d+)\)', c):
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

    idx = c.index("\t(sheet_instances")
    open(PATH, "w").write(c[:idx] + "".join(parts) + c[idx:])
    print(f"wired nets: {stats['wire']}   labelled nets: {stats['label']}")
    print(f"emitted {sum(1 for p in parts if p.startswith(chr(9)+'(wire'))} wire segments, "
          f"{sum(1 for p in parts if p.startswith(chr(9)+'(label'))} labels")
    return 0


sys.exit(main())
