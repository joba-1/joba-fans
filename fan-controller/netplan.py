#!/usr/bin/env python3
"""Declarative net plan for the fan controller.

Every connection is (ref, pin) -> net name. No wire routing: each pin gets a
short stub wire pointing away from the symbol body, with a label at the stub's
far end. Same-named labels merge into one net (skill note #3), and the stub
satisfies the "label needs a wire under it" rule (skill note #4).

Because nothing routes across the sheet, there are no shared lanes and thus no
collinear T-tap shorts (skill note #3b).
"""

STUB = 2.54  # stub length, mm

# Fan connector (Conn_01x04) standard PC 4-pin fan pinout
#   1=GND  2=+12V  3=Tach  4=PWM
FAN_PINS = {"1": "GND", "2": "+12V_PROT", "3": "TACH", "4": "PWM"}

# Fan channel -> (connector, pullup R, tach series R, pwm series R,
#                 XIAO pwm pin, XIAO tach pin)
# XIAO pin numbers verified against extracted table:
#   pin2=D1 pin3=D2 pin4=D3 pin5=D4 pin6=D5 pin7=D6 pin8=D7 pin11=D10
# D0(pin1)/D8(pin9)/D9(pin10) avoided: ESP32-C3 strapping pins.
CHANNELS = [
    # name,  conn, pullup, tach_R, pwm_R, xiao_pwm, xiao_tach
    ("FAN1", "J2", "R1", "R9",  "R5", "2", "3"),   # PWM=D1  TACH=D2
    ("FAN2", "J3", "R2", "R10", "R6", "4", "5"),   # PWM=D3  TACH=D4
    ("FAN3", "J4", "R3", "R11", "R7", "6", "7"),   # PWM=D5  TACH=D6
    ("FAN4", "J5", "R4", "R12", "R8", "8", "11"),  # PWM=D7  TACH=D10
]


def build_connections():
    """Return list of (ref, pin, netname)."""
    conns = []

    # ---- Power input chain -------------------------------------------------
    # J1 barrel jack: pin1 = tip (+12V), pin2 = sleeve (GND)
    conns.append(("J1", "1", "+12V_IN"))
    conns.append(("J1", "2", "GND"))

    # D1 Schottky reverse-polarity protection.
    # pin2 = A (anode) takes the raw input; pin1 = K (cathode) is protected side.
    conns.append(("D1", "2", "+12V_IN"))
    conns.append(("D1", "1", "+12V_FUSED"))

    # F1 polyfuse in series after the diode.
    conns.append(("F1", "1", "+12V_FUSED"))
    conns.append(("F1", "2", "+12V_PROT"))

    # C1 bulk cap across the protected 12V rail.
    conns.append(("C1", "1", "+12V_PROT"))
    conns.append(("C1", "2", "GND"))

    # U2 AMS1117-5.0 regulator: 12V -> 5V.
    conns.append(("U2", "3", "+12V_PROT"))  # VI
    conns.append(("U2", "1", "GND"))        # GND
    conns.append(("U2", "2", "+5V"))        # VO

    # C2 output cap on the 5V rail.
    conns.append(("C2", "1", "+5V"))
    conns.append(("C2", "2", "GND"))

    # ---- XIAO ESP32-C3 power ----------------------------------------------
    conns.append(("U1", "14", "+5V"))     # VBUS  <- 5V in
    conns.append(("U1", "12", "+3V3"))    # 3V3_OUT -> tach pull-up rail
    for gnd_pin in ("13", "18", "22"):    # all three GND pins
        conns.append(("U1", gnd_pin, "GND"))

    # ---- Per-fan channels --------------------------------------------------
    for name, conn, pullup, tach_r, pwm_r, xiao_pwm, xiao_tach in CHANNELS:
        tach_raw = f"{name}_TACH_RAW"   # fan tach output + pull-up node
        tach_mcu = f"{name}_TACH"       # after series resistor, into MCU
        pwm_mcu  = f"{name}_PWM"        # MCU output, before series resistor
        pwm_fan  = f"{name}_PWM_OUT"    # after series resistor, to fan

        # Fan connector pins
        for pin, role in FAN_PINS.items():
            if role == "TACH":
                conns.append((conn, pin, tach_raw))
            elif role == "PWM":
                conns.append((conn, pin, pwm_fan))
            else:
                conns.append((conn, pin, role))  # GND / +12V_PROT

        # Tach pull-up: 10k from tach node to 3V3
        conns.append((pullup, "2", tach_raw))
        conns.append((pullup, "1", "+3V3"))

        # Tach series resistor: tach node -> MCU input
        conns.append((tach_r, "2", tach_raw))
        conns.append((tach_r, "1", tach_mcu))
        conns.append(("U1", xiao_tach, tach_mcu))

        # PWM series resistor: MCU output -> fan
        conns.append((pwm_r, "1", pwm_mcu))
        conns.append((pwm_r, "2", pwm_fan))
        conns.append(("U1", xiao_pwm, pwm_mcu))

    return conns


def pin_abs(place_x, place_y, local_x, local_y):
    """Absolute schematic position of a pin on a symbol placed at 0 rotation.

    CRITICAL: symbol libraries use math convention (+y is UP), while the
    schematic canvas uses screen convention (+y is DOWN). The Y component must
    therefore be NEGATED, not added:

        abs_x = place_x + local_x
        abs_y = place_y - local_y

    Getting this wrong mirrors every pin about its symbol's origin, so wires
    silently attach to the pin on the opposite side of the part (e.g. the
    XIAO's VBUS pin 14 resolves to D9/BOOT pin 10). ERC still passes, because
    landing on the wrong real pin is a perfectly valid connection -- only a
    netlist audit catches it.
    """
    return (round(place_x + local_x, 3), round(place_y - local_y, 3))


def stub_endpoint(x, y, rot):
    """Point STUB mm away from the pin, pointing away from the symbol body.

    Rotation is expressed in the library's math convention, so the vertical
    cases invert when mapped onto the screen's downward +y:
        rot   0 -> -x   (pin on the symbol's left edge)
        rot 180 -> +x   (pin on the right edge)
        rot  90 -> +y   (library "up" = screen down)
        rot 270 -> -y   (library "down" = screen up)
    """
    if rot == 0:
        return (x - STUB, y)
    if rot == 180:
        return (x + STUB, y)
    if rot == 90:
        return (x, y + STUB)
    if rot == 270:
        return (x, y - STUB)
    raise ValueError(f"unexpected rotation {rot}")
