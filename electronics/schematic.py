"""Draw the power-stage schematic from code -> ../img/circuit_schematic.png.

Values come from circuit.P, so the drawing and the simulated netlist cannot
drift apart. Three blocks, drawn separately and stacked; nets between blocks
and to the Arduino Nano are tags (BUS, SH, 5V, D9, A0, A1, A2, D2).
"""

import os
import tempfile

import matplotlib

matplotlib.use("Agg")
import schemdraw  # noqa: E402
import schemdraw.elements as elm  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from circuit import P, trip_current  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "img", "circuit_schematic.png")
DPI = 100


def ohm(r):
    if r >= 1e6:
        return f"{r / 1e6:g}M"
    if r >= 1e3:
        return f"{r / 1e3:g}k"
    if r < 1:
        return f"{r * 1e3:g} mΩ"
    return f"{r:g} Ω"


def far(c):
    return f"{c * 1e6:g} µF" if c >= 1e-6 else f"{c * 1e9:g} nF"


def tag(d, name, at, theta=0):
    d += elm.Tag().at(at).theta(theta).label(name, fontsize=11)


def gnd(d, at=None):
    d += elm.Ground().at(at) if at is not None else elm.Ground()


def power_stage(path):
    with schemdraw.Drawing(show=False) as d:
        gnd(d)
        d += elm.SourceV().up().label("J1\n19 V / 90 W\nlaptop brick", loc="bottom")
        d += elm.Fuse().right().label("F1  5 A slow")
        d += (b1 := elm.Dot())
        d += elm.Diode().down().reverse().label("D1\nSMBJ22A\nTVS", loc="bottom")
        gnd(d)
        d += elm.Line().right().at(b1.center)
        d += (b2 := elm.Dot())
        d += elm.Capacitor(polar=True).down().label(f"C1\n{far(P['c_bulk'])}\n35 V low-ESR", loc="bottom")
        gnd(d)
        d += elm.Line().right().at(b2.center)
        d += (b3 := elm.Dot())
        d += elm.Line().up(1).at(b3.center)
        tag(d, "BUS", d.here, 90)
        d += elm.Line().right(1.5).at(b3.center)
        d += (b4 := elm.Dot())
        d += elm.Motor().down().label("M1\nRS-550", loc="bottom")
        d += (ml := elm.Dot())
        d += elm.Line().right(3).at(b4.center)
        d += (b5 := elm.Dot())
        d += elm.Diode(schottky=True).down().reverse().label("D2\nSB540", loc="bottom")
        d += elm.Line().left(3)
        d += elm.Line().right(2.5).at(b5.center)
        d += elm.Capacitor().down().label(f"C2\n{far(P['c_motor'])}", loc="bottom")
        d += elm.Line().left(2.5)
        d += elm.Line().down(1.2).at(ml.center)
        d += (q := elm.NFet().right().anchor("drain").label("Q1\nIRLZ44N", loc="left", ofst=(-0.2, 0)))
        d += elm.Line().right(1).at(q.gate)
        d += (g := elm.Dot())
        d += elm.Resistor().right().label(f"R1  {ohm(P['r_gate'])}")
        tag(d, "D9", d.here)
        d += elm.Resistor().down().at(g.center).label(f"R2\n{ohm(P['r_gate_pd'])}", loc="bottom")
        gnd(d)
        d += elm.Line().down(0.8).at(q.source)
        d += (sh := elm.Dot())
        d += elm.Resistor().down().label(f"R3\n{ohm(P['r_shunt'])}\n2 W", loc="bottom")
        gnd(d)
        d += elm.Label().at((sh.center[0] - 4.2, sh.center[1] - 2.0)).label(
            "star ground:\nArduino GND + U1 GND\njoin at R3's low end", fontsize=8, halign="left")
        d += elm.Line().left(1.5).at(sh.center)
        tag(d, "SH", d.here, 180)
        d.save(path, dpi=DPI)


def sense(path):
    gain = 1 + P["r_g2"] / P["r_g1"]
    with schemdraw.Drawing(show=False) as d:
        d += (t := elm.Tag().theta(180).label("SH", fontsize=11))
        d += elm.Resistor().right().at(t.start).label(f"R4  {ohm(P['r_pf'])}")
        d += (sf := elm.Dot())
        d += elm.Capacitor().down().label(f"C3\n{far(P['c_pf'])}", loc="bottom")
        gnd(d)
        d += elm.Line().right(1).at(sf.center)
        d += (u1 := elm.Opamp(leads=True).anchor("in2").label(f"U1A\nLM358\n×{gain:.1f}", loc="center", ofst=(-0.4, 0), fontsize=9))
        d += elm.Line().up(1.2).at(u1.in1)
        d += (fb := elm.Dot())
        d += elm.Resistor().left().label(f"R6  {ohm(P['r_g1'])}")
        gnd(d)
        d += elm.Line().right(0.6).at(u1.out)
        d += (ao := elm.Dot())
        d += elm.Resistor().right().at(fb.center).tox(ao.center).label(f"R5  {ohm(P['r_g2'])}")
        d += elm.Line().toy(ao.center)
        d += elm.Resistor().right().at(ao.center).label(f"R7  {ohm(P['r_adc'])}")
        d += (a1 := elm.Dot())
        d += elm.Capacitor().down().label(f"C4\n{far(P['c_adc'])}", loc="bottom")
        gnd(d)
        d += elm.Line().right(1.2).at(a1.center)
        tag(d, "A1", d.here)

        # comparator below: + from amp output, - from reference
        d += elm.Line().down(6.5).at(ao.center)
        d += elm.Resistor().right(6.5).label(f"R8  {ohm(P['r_cmp_in'])}")
        d += (cp := elm.Dot())
        d += elm.Line().right(0.8)
        d += (u2 := elm.Opamp(leads=True).anchor("in2").label("U1B\nLM358", loc="center", ofst=(-0.4, 0), fontsize=9))
        d += elm.Line().down(1.4).at(cp.center)
        d += elm.Resistor().right().tox(u2.out).label(f"R9  {ohm(P['r_cmp_hys'])}  hysteresis", loc="bottom")
        d += elm.Line().toy(u2.out)
        d += elm.Line().right(0.6).at(u2.out)
        d += elm.Resistor().right().label(f"R10  {ohm(P['r_int'])}")
        tag(d, "D2", d.here)
        d += elm.Line().up(1.2).at(u2.in1)
        d += (rf := elm.Dot())
        d += elm.Resistor().up().label(f"R11\n{ohm(P['r_ref_top'])}", loc="bottom")
        tag(d, "5V", d.here, 90)
        d += elm.Resistor().right().at(rf.center).label(f"R12  {ohm(P['r_ref_bot'])}")
        gnd(d)
        d += elm.Label().at((rf.center[0] + 3.6, rf.center[1] + 0.9)).label(
            f"ref {P['v_logic'] * P['r_ref_bot'] / (P['r_ref_top'] + P['r_ref_bot']):.2f} V "
            f"= trip at {trip_current():.1f} A", fontsize=8)
        d.save(path, dpi=DPI)


def inputs(path):
    with schemdraw.Drawing(show=False) as d:
        # bus voltage divider
        d += (t := elm.Tag().theta(180).label("BUS", fontsize=11))
        d += elm.Resistor().right().at(t.start).label(f"R13  {ohm(P['r_v1'])}")
        d += (a2 := elm.Dot())
        d += elm.Resistor().down().label(f"R14\n{ohm(P['r_v2'])}", loc="bottom")
        gnd(d)
        d += elm.Line().right(1.6).at(a2.center)
        d += (c5 := elm.Dot())
        d += elm.Capacitor().down().label(f"C5\n{far(P['c_v'])}", loc="bottom")
        gnd(d)
        d += elm.Line().right(1).at(c5.center)
        tag(d, "A2", d.here)

        # speed pot
        x = c5.center[0] + 4.5
        y = a2.center[1] + 1.25
        d += (pt := elm.Tag().at((x, y)).theta(180).label("5V", fontsize=11))
        d += elm.Line().right(0.5).at(pt.start)
        d += (rp := elm.Potentiometer().down().label(f"RV1\n{ohm(P['r_pot'])}\nspeed", loc="top"))
        gnd(d)
        d += elm.Line().right(1.2).at(rp.tap)
        d += (pa := elm.Dot())
        d += elm.Capacitor().down().label(f"C6\n{far(P['c_pot'])}", loc="bottom")
        gnd(d)
        d += elm.Line().right(1).at(pa.center)
        tag(d, "A0", d.here)

        # logic supply
        x = pa.center[0] + 4.5
        d += (bt := elm.Tag().at((x, a2.center[1])).theta(180).label("BUS", fontsize=11))
        d += elm.Line().right(0.6).at(bt.start)
        d += (u3 := elm.Ic(pins=[elm.IcPin(name="", anchorname="IN", side="left"),
                                 elm.IcPin(name="", anchorname="OUT", side="right"),
                                 elm.IcPin(name="", anchorname="GND", side="bot")],
                           size=(3.6, 1.8)).anchor("IN"))
        d += elm.Label().at(u3.center).label("U3 buck module\nMP1584 / LM2596\n19 → 5 V", fontsize=9)
        gnd(d, u3.GND)
        d += elm.Line().right(1).at(u3.OUT)
        d += (o5 := elm.Dot())
        d += elm.Capacitor().down().label("C7\n10 µF", loc="bottom")
        gnd(d)
        d += elm.Line().right(1).at(o5.center)
        tag(d, "5V", d.here)
        d += elm.Label().at((o5.center[0] + 0.2, o5.center[1] + 1.2)).label(
            "→ Nano 5V pin, U1 VCC", fontsize=8, halign="left")
        d.save(path, dpi=DPI)


def main():
    tmp = tempfile.mkdtemp()
    blocks = [("1  Power stage – 19 V brick, protection, motor, low-side switch, shunt", power_stage),
              ("2  Current sense (A1) and over-current comparator (D2) – U1 = LM358 on 5 V", sense),
              ("3  Bus voltage (A2), speed pot (A0), 5 V logic supply", inputs)]
    imgs = []
    for title, fn in blocks:
        p = os.path.join(tmp, fn.__name__ + ".png")
        fn(p)
        imgs.append((title, Image.open(p).convert("RGB")))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
        small = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = small = ImageFont.load_default()
    pad, head = 20, 40
    notes = ("Arduino Nano: D9 PWM 20 kHz (Timer1) = duty from A0 with soft-start ramp; "
             "A1 = 0.448 V/A supply current; A2 = bus/5.55; D2 = INT0 over-current (LM358 high ≈ 3.5 V).")
    w = max(im.width for _, im in imgs) + 2 * pad
    h = sum(im.height + head for _, im in imgs) + 2 * pad + 30
    out = Image.new("RGB", (w, h), "white")
    dr = ImageDraw.Draw(out)
    y = pad
    for title, im in imgs:
        dr.text((pad, y), title, fill="black", font=font)
        out.paste(im, (pad, y + head - 6))
        y += im.height + head
    dr.text((pad, y + 5), notes, fill="black", font=small)
    out.save(OUT, optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
