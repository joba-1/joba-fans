"""Schematic placement + drawing style for the fan controller.

Style rules:
  * signals flow left -> right   (XIAO GPIO -> series R -> fan connector)
  * power flows top -> bottom    (J1 -> D1 -> F1 -> +12V rail -> U2 -> +5V)
  * short point-to-point wires where a direct connection is simple
  * labels for power rails and for any long / multi-point net
"""

# ---------------------------------------------------------------- placement
# Resistors are rotated 90 deg so they sit horizontally, letting each fan
# channel read as one straight left-to-right line.
R_ROT = 90

# Power block: top-left, laid out left-to-right along the 12V path, with the
# regulator's output continuing rightward. Kept on one horizontal band so the
# rail labels have clear space above and below.
POWER = {
    "J1": (35.0,  35.0,   0),   # barrel jack
    "D1": (60.0,  35.0, 180),   # reverse-polarity diode: anode left, so
                                #   current flows left-to-right A -> K
    "F1": (80.0,  35.0,  90),   # polyfuse, horizontal, in line with the rail
    "C1": (105.0, 52.0,   0),   # bulk cap, hangs well below the rail
    "U2": (140.0, 35.0,   0),   # AMS1117 regulator
    "C2": (175.0, 52.0,   0),   # 5V output cap, hangs well below
}

# XIAO: left side, below the power block. Body spans roughly
# x 40.9..77.8, y (cy-17.8)..(cy+21.6) -- keep clear of the fan band.
XIAO = (55.0, 115.0, 0)

# Fan channels: one horizontal band each, well below the power block and to
# the right of the XIAO so the GPIO labels have room.
FAN_ROW_Y     = [80.0, 118.0, 156.0, 194.0]
X_R_PWM       = 125.0   # 1k   series resistor, MCU -> fan   (row + PWM_DY)
X_R_TACH      = 125.0   # 330R series resistor, fan -> MCU   (row + TACH_DY)
X_CONN        = 168.0   # fan connector, close enough to wire directly
PWM_DY        = 0.0
TACH_DY       = 8.0

# The 10k pull-up hangs BELOW the tach run rather than sitting inline with it,
# so the tach wire never has to pass through the pull-up's pins. Vertical
# orientation (rot 0) keeps its +3V3 label clear of the horizontal signal flow.
X_R_PULLUP    = 128.0
PULLUP_DY     = 17.0
PULLUP_ROT    = 90

CHANNELS = [
    ("FAN1", "J2", "R1", "R9",  "R5"),
    ("FAN2", "J3", "R2", "R10", "R6"),
    ("FAN3", "J4", "R3", "R11", "R7"),
    ("FAN4", "J5", "R4", "R12", "R8"),
]


def placements():
    """ref -> (x, y, rotation)"""
    out = dict(POWER)
    out["U1"] = XIAO
    for (name, conn, pullup, tach_r, pwm_r), y in zip(CHANNELS, FAN_ROW_Y):
        out[pwm_r]  = (X_R_PWM,    y + PWM_DY,     R_ROT)
        out[tach_r] = (X_R_TACH,   y + TACH_DY,    R_ROT)
        out[pullup] = (X_R_PULLUP, y + PULLUP_DY,  PULLUP_ROT)
        out[conn]   = (X_CONN,     y + 4.0,        0)
    return out
