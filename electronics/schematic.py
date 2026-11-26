"""Draw the power-stage schematic from code -> ../img/circuit_schematic.png.

Values come from circuit.P, so the drawing and the simulated netlist cannot
drift apart. Two blocks, drawn separately and stacked; nets between blocks and
to the Arduino Nano are tags (BUS, 5V, D9, A0, A1).
"""

import os
import tempfile

import matplotlib

matplotlib.use("Agg")
import schemdraw  # noqa: E402
import schemdraw.elements as elm  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from circuit import P, STALL  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "img", "circuit_schematic.png")
DPI = 100


def ohm(r):
    if r >= 1e6:
        return f"{r / 1e6:g}M"
    if r >= 1e3:
        return f"{r / 1e3:g}k"
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
        d += elm.Line().right(2.5).at(b3.center)
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

        # low-side switch
        d += elm.Line().down(1.2).at(ml.center)
        d += (q := elm.NFet().right().anchor("drain").label("Q1\nIRLZ44N", loc="left", ofst=(-0.2, 0)))
        d += elm.Line().right(1).at(q.gate)
        d += (g := elm.Dot())
        d += elm.Resistor().right().label(f"R1  {ohm(P['r_gate'])}")
        tag(d, "D9", d.here)
        d += elm.Resistor().down().at(g.center).label(f"R2\n{ohm(P['r_gate_pd'])}", loc="bottom")
        gnd(d)

        # shunt, its bypass cap, sense RC -> A1
        d += elm.Line().down(0.8).at(q.source)
        d += (sh := elm.Dot())
        d += elm.Resistor().down().label(f"R3\n{ohm(P['r_shunt'])}\n5 W", loc="bottom")
        gnd(d)
        d += elm.Line().left(2).at(sh.center)
        d += (cs := elm.Dot())
        d += elm.Capacitor().down().label(f"C3\n{far(P['c_shunt'])}\nceramic", loc="bottom")
        gnd(d)
        d += elm.Resistor().left().at(cs.center).label(f"R4  {ohm(P['r_sense'])}")
        d += (a1 := elm.Dot())
        d += elm.Capacitor().down().label(f"C4\n{far(P['c_sense'])}", loc="bottom")
        gnd(d)
        d += elm.Line().left(1.2).at(a1.center)
        tag(d, "A1", d.here, 180)
        d += elm.Label().at((sh.center[0] + 1.3, sh.center[1] - 3.3)).label(
            "star ground: Arduino GND\njoins at R3's low end", fontsize=8, halign="left")
        d.save(path, dpi=DPI)


def inputs(path):
    with schemdraw.Drawing(show=False) as d:
        # speed pot
        d += (pt := elm.Tag().theta(180).label("5V", fontsize=11))
        d += elm.Line().right(0.5).at(pt.start)
        d += (rp := elm.Potentiometer().down().label(f"RV1\n{ohm(P['r_pot'])}\nspeed", loc="top"))
        gnd(d)
        d += elm.Line().right(1.2).at(rp.tap)
        d += (pa := elm.Dot())
        d += elm.Capacitor().down().label(f"C5\n{far(P['c_pot'])}", loc="bottom")
        gnd(d)
        d += elm.Line().right(1).at(pa.center)
        tag(d, "A0", d.here)

        # logic supply
        x = pa.center[0] + 4.5
        d += (bt := elm.Tag().at((x, pa.center[1])).theta(180).label("BUS", fontsize=11))
        d += elm.Line().right(0.6).at(bt.start)
        d += (u1 := elm.Ic(pins=[elm.IcPin(name="", anchorname="IN", side="left"),
                                 elm.IcPin(name="", anchorname="OUT", side="right"),
                                 elm.IcPin(name="", anchorname="GND", side="bot")],
                           size=(3.6, 1.8)).anchor("IN"))
        d += elm.Label().at(u1.center).label("U1 buck module\nMP1584 / LM2596\n19 → 5 V", fontsize=9)
        gnd(d, u1.GND)
        d += elm.Line().right(1).at(u1.OUT)
        d += (o5 := elm.Dot())
        d += elm.Capacitor().down().label("C6\n10 µF", loc="bottom")
        gnd(d)
        d += elm.Line().right(1).at(o5.center)
        tag(d, "5V", d.here)
        d += elm.Label().at((o5.center[0] + 0.2, o5.center[1] + 1.2)).label(
            "→ Nano 5V pin", fontsize=8, halign="left")
        d.save(path, dpi=DPI)


def main():
    tmp = tempfile.mkdtemp()
    blocks = [("1  Power stage – 19 V brick, protection, motor, low-side switch, shunt → A1", power_stage),
              ("2  Speed pot (A0), 5 V logic supply", inputs)]
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
    notes = [f"Arduino Nano: D9 = PWM 20 kHz (Timer1), duty from A0 with a soft-start ramp. "
             f"A1 = {P['r_shunt']} V/A of supply current (motor current = A1 / duty).",
             f"Stall rule (firmware): every {STALL['t_sample'] * 1e3:g} ms, "
             f"{STALL['n_confirm']} samples over {STALL['i_supply']} A supply or "
             f"{STALL['i_motor']} A motor → PWM off."]
    w = max(max(im.width for _, im in imgs), *(int(small.getlength(n)) for n in notes)) + 2 * pad
    h = sum(im.height + head for _, im in imgs) + 2 * pad + 22 * len(notes)
    out = Image.new("RGB", (w, h), "white")
    dr = ImageDraw.Draw(out)
    y = pad
    for title, im in imgs:
        dr.text((pad, y), title, fill="black", font=font)
        out.paste(im, (pad, y + head - 6))
        y += im.height + head
    for n in notes:
        dr.text((pad, y + 5), n, fill="black", font=small)
        y += 22
    out.save(OUT, optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
