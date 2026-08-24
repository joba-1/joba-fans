"""Decide, per net, whether it is drawn as wires or as labels.

Rule of thumb from the user:
  * wires while that is simple enough
  * labels instead of long or multiply-connected wires
    (typically the power rails and anything spanning the sheet)

So: a net is drawn with real wires when it has exactly two endpoints AND
those endpoints are close enough to route with one or two segments.
Everything else -- power rails, and any net crossing the sheet -- is drawn as
matching labels on short stubs.
"""

WIRE_SPAN_LIMIT = 45.0   # mm; beyond this a net is "long" -> use labels

# Rails are always labels: many endpoints, spread all over the sheet.
ALWAYS_LABEL = {"GND", "+3V3", "+5V", "+12V_PROT"}


def classify(net, endpoints):
    """endpoints: list of (ref, pin, (x, y)). Returns 'wire' or 'label'.

    A net is wired when it is local and simple: at most three endpoints, all
    within a small bounding box. Everything else -- the power rails, and the
    MCU-to-resistor hops that span the sheet -- becomes labels.
    """
    if net in ALWAYS_LABEL:
        return "label"
    if len(endpoints) > 2:
        # Three or more endpoints means a T-tap. Drawing those as wires forces
        # the run past whichever part sits between the endpoints, so label them
        # instead -- exactly the "multiply connected" case the style rule calls
        # out. The tach nets (fan pin + pull-up + series R) all land here.
        return "label"
    xs = [p[2][0] for p in endpoints]
    ys = [p[2][1] for p in endpoints]
    if max(xs) - min(xs) > WIRE_SPAN_LIMIT or max(ys) - min(ys) > WIRE_SPAN_LIMIT:
        return "label"                      # long
    return "wire"


ESCAPE = 2.54   # how far a wire leaves a pin before it may turn


def _escape(pt, rot, d=ESCAPE):
    """First point away from a pin, along the direction the pin faces."""
    x, y = pt
    return {0: (round(x - d, 3), y), 180: (round(x + d, 3), y),
            90: (x, round(y + d, 3)), 270: (x, round(y - d, 3))}[rot]


def route(a, b, a_rot, b_rot, detour=None):
    """Orthogonal path between two pins, as a list of 2-point segments.

    Both ends escape along their own facing direction first. That matters
    because pins are usually in a row (a connector's pin 4 sits directly below
    pins 1-3): routing straight at the target would drive the wire through its
    neighbours and short them together.

    `detour`, when given, is a coordinate to route via on the perpendicular
    axis. Use it when a third part sits between the two pins -- a straight run
    would otherwise pass through that part's pins and short them onto this net.
    """
    ea = _escape(a, a_rot)
    eb = _escape(b, b_rot)

    segs = [(a, ea)] if ea != a else []

    if detour is not None:
        # Step onto the detour axis, traverse, then come back.
        if a_rot in (0, 180):          # travelling horizontally -> detour in y
            m1, m2 = (ea[0], detour), (eb[0], detour)
        else:                          # travelling vertically -> detour in x
            m1, m2 = (detour, ea[1]), (detour, eb[1])
        for p, q in ((ea, m1), (m1, m2), (m2, eb)):
            if p != q:
                segs.append((p, q))
    elif abs(ea[0] - eb[0]) < 1e-6 or abs(ea[1] - eb[1]) < 1e-6:
        if ea != eb:
            segs.append((ea, eb))
    else:
        # Turn along the axis the first pin is already travelling.
        corner = (eb[0], ea[1]) if a_rot in (0, 180) else (ea[0], eb[1])
        if corner != ea:
            segs.append((ea, corner))
        if corner != eb:
            segs.append((corner, eb))

    if eb != b:
        segs.append((eb, b))
    return segs
